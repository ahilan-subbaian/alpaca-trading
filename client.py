from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, GetCalendarRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus, OrderStatus
import datetime
import time
import logging
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

NOTIONAL_INVALID = {
    "PTY",
}
TOTAL_SYMBOL_VALUE = 100
TIMEOUT = 5
GREATER_MULTIPLIER = 1.05
LESSER_MULTIPLIER = 0.95


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
        if not symbols or not isinstance(symbols, dict) or int(sum(symbols.values())) != TOTAL_SYMBOL_VALUE:
            raise ValueError(
                f"symbols <{symbols}> is invalid. Expected dictionary with values summing to 100.")

        # connection to alpaca api
        self.client = TradingClient(apiKey, secretKey, paper=paper)
        self.broker = StockHistoricalDataClient(
            api_key=apiKey, secret_key=secretKey)

        # maximum amount to trade this week
        self.limit = limit

        # dictionary of symbols to trade and their weights
        self.symbols = symbols

        # amount traded this week, will be set in prior_trades()
        self.traded = 0

    # main execution method
    def execute(self):
        response = {"result": False, "message": "execution failed"}

        logger.info("Executing trading client actions")

        # set self.traded to amount traded this week
        execution_response = self.pre_order_checks()
        if not execution_response["result"]:
            return execution_response

        # validate market is open
        is_market_open = self.is_market_open()
        logger.info(f"Market open: {is_market_open}")
        if not is_market_open:
            response["result"] = True
            response["message"] = "market is closed"
            return response

        # place orders
        execution_response = self.order()
        # populate orders
        orders = execution_response.pop("orders")
        if not execution_response["result"]:
            return execution_response

        time.sleep(TIMEOUT)

        # post order checks
        execution_response = self.post_order_checks(orders)
        if not execution_response["result"]:
            return execution_response

        # success
        response["result"] = True
        response["message"] = "execution successful"
        return response

    # checks to be done before placing orders
    def pre_order_checks(self):
        response = {"result": False, "message": "pre-order checks failed"}

        # validate prior trades as less than limit
        # set self.traded to amount traded this week
        self.traded = self.prior_trades()
        logger.info(f"Prior trades: {self.traded}")
        if self.traded < 0 or self.traded > self.limit * GREATER_MULTIPLIER:
            response["message"] = "prior trades outside of expected limit"
            return response

        # success
        response["result"] = True
        response["message"] = "pre-order checks successful"
        return response

    # does calculations to determine amount to trade and places trades
    def order(self):
        response = {"result": False, "message": "order failed", "orders": []}

        # make sure we have not traded more than limit
        if self.traded >= self.limit * LESSER_MULTIPLIER:
            response["message"] = "order not placed, limit reached"
            return response

        # validate purchase power is within range
        purchase_power = self.purchase_power()
        logger.info(f"Purchase power: {purchase_power}")
        if purchase_power <= 0 or purchase_power > (self.limit - self.traded) * GREATER_MULTIPLIER:
            response["message"] = "purchase power is out of range"
            return response

        # place orders
        orders = self.place_order(purchase_power)
        logger.info(f"Orders placed: {orders}")
        if len(orders) != len(self.symbols):
            logger.error(f"Order count does not match symbol count")
            response["result"] = True
            response["message"] = "order count does not match symbol count"
            return response

        # success
        response["result"] = True
        response["message"] = "order successful"
        response["orders"] = orders
        return response

    # checks to be done after placing orders
    def post_order_checks(self, orders):
        response = {"result": False, "message": "post-order checks failed"}

        # validate orders are filled
        failed_orders = self.check_order_status(orders)
        logger.info(f"Failed orders: {failed_orders}")
        if failed_orders > 0:
            logger.error(f"Failed orders: {failed_orders}")

        # validate total traded is within range
        total_traded = self.prior_trades()
        logger.info(f"Total traded: {total_traded}")
        if total_traded < self.limit * LESSER_MULTIPLIER or total_traded > self.limit * GREATER_MULTIPLIER:
            response["message"] = "total traded outside of expected limit"
            return response

        # success
        response["result"] = True
        response["message"] = "post-order checks successful"
        return response

    # checks if orders were filled
    # Parameters:
    #   orders: list of orders to check
    def check_order_status(self, orders):
        failed_orders = 0

        for order in orders:
            order = self.client.get_order_by_id(order.id)
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
            if symbol not in NOTIONAL_INVALID:
                investment = purchase_power * (amount / TOTAL_SYMBOL_VALUE)
                order = MarketOrderRequest(
                    symbol=symbol,
                    notional=investment,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                )
            else:
                investment = purchase_power * (amount / TOTAL_SYMBOL_VALUE)
                last_price = self.broker.get_stock_latest_quote(
                    StockLatestQuoteRequest(symbol_or_symbols=symbol))[symbol].bid_price
                # round up to nearest whole number
                qty = int(0.5 + investment / last_price)
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
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
            account_cash = float(self.client.get_account().cash)
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
        start = datetime.datetime.now()

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
            trade = self.process_order(order)
            if trade == -1:
                return -1
            else:
                traded += trade

        # return an integer
        return traded

    def process_order(self, order):
        traded = 0
        # cancel orders are not counted but logged
        if order.status == OrderStatus.CANCELED:
            logger.info(f"Canceled order: {order}")
        # filled orders are counted
        elif order.status == OrderStatus.FILLED:
            if order.notional != None:
                logger.info(f"Filled order: {order}")
                traded = float(order.notional)
            elif order.qty != None:
                logger.info(f"Filled order: {order}")
                traded = float(order.qty) * float(order.filled_avg_price)
            else:
                logger.error(f"Filled order has no values: {order}")
                return -1
        else:
            logger.error(f"Unknown order status: {order}")
            return -1
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
