from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, GetCalendarRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus, OrderStatus
import datetime
import time
import logging
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class AlpacaClient:
    # Initialize the trading client
    # Parameters:
    #   apiKey: Alpaca API key
    #   secretKey: Alpaca secret key
    #   limit: maximum amount to trade this week
    #   symbols: dictionary of symbols to trade and their weights
    #   paper: True if paper trading, False if live trading
    def __init__(self, apiKey, secretKey, limit, symbols, paper=True) -> None:
        # validate inputs
        if not apiKey or not isinstance(apiKey, str):
            raise ValueError(f"apiKey <{apiKey}> is invalid. Expected string.")
        if not secretKey or not isinstance(secretKey, str):
            raise ValueError(
                f"secretKey <{secretKey}> is invalid. Expected string.")
        if not limit or not isinstance(limit, int):
            raise ValueError(f"limit <{limit}> is invalid. Expected integer.")
        if not symbols or not isinstance(symbols, dict) or int(sum(symbols.values())) != 100:
            raise ValueError(
                f"symbols <{symbols}> is invalid. Expected dictionary with values summing to 100.")

        self.client = TradingClient(apiKey, secretKey, paper=paper)
        self.limit = limit
        self.symbols = symbols
        self.traded = 0

    # main execution method
    def execute(self):
        response = {"result": False, "message": "execution failed"}

        # validate prior trades as less than limit
        # set self.traded to amount traded this week
        self.traded = self.prior_trades()
        logger.info(f"Prior trades: {self.traded}")
        if self.traded < 0 or self.traded > self.limit * .95:
            response["message"] = "prior trades outside of expected limit"
            return response

        # validate market is open
        is_market_open = self.is_market_open()
        logger.info(f"Market open: {is_market_open}")
        if not is_market_open:
            response["result"] = True
            response["message"] = "market is closed"
            return response

        # validate purchase power is within range
        purchase_power = self.purchase_power()
        logger.info(f"Purchase power: {purchase_power}")
        if purchase_power <= 0 or purchase_power > (self.limit - self.traded) * 1.05:
            response["message"] = "purchase power is out of range"
            return response

        # place orders
        orders = self.place_order(purchase_power)
        logger.info(f"Orders placed: {orders}")
        if len(orders) != len(self.symbols):
            logger.error(f"Order count does not match symbol count")

        time.sleep(5)

        # validate orders are filled
        failed_orders = self.check_order_status(orders)
        logger.info(f"Failed orders: {failed_orders}")
        if failed_orders > 0:
            logger.error(f"Failed orders: {failed_orders}")

        # validate total traded is within range
        total_traded = self.prior_trades()
        logger.info(f"Total traded: {total_traded}")
        if total_traded < self.limit * .95 or total_traded > self.limit * 1.05:
            response["message"] = "total traded outside of expected limit"
            return response

        # success
        response["result"] = True
        response["message"] = "execution successful"
        return response

    # checks if orders were filled
    # Parameters:
    #   orders: list of orders to check
    def check_order_status(self, orders):
        failed_orders = 0

        for order in orders:
            order = self.client.get_order(order.id)
            if order.status != OrderStatus.FILLED:
                logger.error(f"Order failed on: {order}")
                failed_orders += 1

        return failed_orders

    # places the orders based on symbols and purchase power
    # Parameters:
    #   purchase_power: amount to invest
    def place_order(self, purchase_power):

        orders = []
        for symbol, amount in self.symbols.items():
            invesmtment = purchase_power * (amount / 100)
            order = MarketOrderRequest(
                symbol=symbol,
                notional=invesmtment,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )
            logger.info(f"Placing order: {order}")

            try:
                orders.append(self.client.submit_order(order))
            except Exception as e:
                logger.error(f"Error placing order: {e}")
                continue

        return orders

    # calculates the amount that will be traded this week
    def purchase_power(self):
        try:
            account_cash = self.client.get_account().cash
        except Exception as e:
            logger.error(f"Error fetching account cash: {e}")
            return 0
        logger.info(f"Account cash: {account_cash}")
        cash_invest_ratio = self.cash_invest_ratio()
        logger.info(f"Cash invest ratio: {cash_invest_ratio}")
        cash_invest = account_cash * cash_invest_ratio
        purchase_power = min(cash_invest, self.limit - self.traded)
        return purchase_power

    # calculates the ratio of current cash that should be invested
    def cash_invest_ratio(self):
        # Get today's date
        current = datetime.datetime.now()

        # get displaced start date
        month_end = current + relativedelta(months=1)
        month_end = datetime.datetime(month_end.year, month_end.month, 1)

        # Finds the number of fridays from today to end date
        fridays = 0
        while current < month_end:
            if current.weekday() == 4:
                fridays += 1
            current += datetime.timedelta(days=1)

        # Division by 0 error and no month has more than 5 fridays
        if fridays <= 0 or fridays > 5:
            logger.error(f"friday value is out of range: {fridays}")
            return 0

        invest_ratio = 1 / fridays
        return invest_ratio

    # gets the value of all orders that have been closed since the start of the week
    def prior_trades(self):
        start = datetime.datetime.now().date()

        # finds the first monday of the week
        while start.weekday() != 0:
            start -= datetime.timedelta(days=1)

        # Get all orders that havebeen closed since the start of the week
        order_params = GetOrdersRequest(
            status=QueryOrderStatus.CLOSED,
            after=start,
            side=OrderSide.BUY,
        )

        # send request to get orders
        # returns a list of orders
        try:
            orders = self.client.get_orders(order_params)
        except Exception as e:
            logger.error(f"Error fetching prior trades: {e}")
            return -1

        logger.info(f"Orders fetched: {orders}")

        traded = 0

        for order in orders:
            # cancel orders are not counted but logged
            if order.status == OrderStatus.CANCELED:
                logger.info(f"Canceled order: {order}")
            # filled orders are counted
            elif order.status == OrderStatus.FILLED:
                # orders should only be notional orders
                if order.notional != None:
                    logger.info(f"Filled order: {order}")
                    traded += order.notional
                else:
                    logger.error(f"Filled order has no notional: {order}")
                    return -1
            else:
                logger.error(f"Unknown order status: {order}")
                return -1

        # return an integer
        return traded

    # checks if today is the last day the market is open this week
    def is_market_open(self):
        start = end = datetime.datetime.now().date()

        # finds the first friday following today
        while end.weekday() != 4:
            end += datetime.timedelta(days=1)

        calendar = GetCalendarRequest(start=start, end=end)

        # sends request to alpaca api
        # returns list of days open
        try:
            calendar = self.client.get_calendar(calendar)
        except Exception as e:
            logger.error(f"Error fetching calendar: {e}")
            return False

        logger.info(f"Calendar: {calendar}")

        # checks if today is the last day the market is open this week
        return len(calendar) > 0 and calendar[-1].date == start
