from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, GetCalendarRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus, OrderStatus
import datetime
import time
import logging
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class AlpacaClient:
    def __init__(self, apiKey, secretKey, limit, symbols, paper=True) -> None:
        self.client = TradingClient(apiKey, secretKey, paper=paper)
        self.limit = limit
        self.symbols = symbols
        self.traded = 0

    def execute(self):
        response = {"result": False, "message": "execution failed"}

        is_market_open = self.is_market_open()
        logger.info(f"Market open: {is_market_open}")
        if not is_market_open:
            response["result"] = True
            response["message"] = "market is closed"
            return response

        self.traded = self.prior_trades()
        logger.info(f"Prior trades: {self.traded}")
        if self.traded < 0 or self.traded > self.limit * .95:
            response["message"] = "prior trades outside of expected limit"
            return response

        cash_invest_ratio = self.cash_invest_ratio()
        logger.info(f"Cash invest ratio: {cash_invest_ratio}")
        if cash_invest_ratio <= 0 or cash_invest_ratio > 1:
            response["message"] = "cash invest ratio is out of range"
            return response

        purchase_power = self.purchase_power(cash_invest_ratio)
        logger.info(f"Purchase power: {purchase_power}")
        if purchase_power <= 0 or purchase_power > self.limit - self.traded:
            response["message"] = "purchase power is out of range"
            return response

        orders = self.place_order(purchase_power)
        logger.info(f"Orders placed: {orders}")
        if len(orders) != len(self.symbols):
            response["message"] = "order count does not match symbol count"
            return response

        time.sleep(5)

        failed_orders = self.check_order_status(orders)
        logger.info(f"Failed orders: {failed_orders}")
        if failed_orders > 0:
            response["message"] = "failed orders"
            return response

        total_traded = self.prior_trades()
        logger.info(f"Total traded: {total_traded}")
        if total_traded < self.limit * .95 or total_traded > self.limit * 1.05:
            response["message"] = "total traded outside of expected limit"
            return response

        response["result"] = True
        response["message"] = "execution successful"
        return response

    def check_order_status(self, orders):
        failed_orders = 0

        for order in orders:
            order = self.client.get_order(order.id)
            if order.status != OrderStatus.FILLED:
                logger.error(f"Order failed on: {order}")
                failed_orders += 1

        return failed_orders

    def place_order(self, purchase_power):
        invesmtment_per_symbol = purchase_power / len(self.symbols)

        orders = []
        for symbol in self.symbols:
            order = MarketOrderRequest(
                symbol=symbol,
                notional=invesmtment_per_symbol,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY,
            )

            logger.info(f"Order placed: {order}")
            orders.append(self.client.submit_order(order))

        return orders

    def purchase_power(self, cash_invest_ratio):
        account_cash = self.client.get_account().cash
        logger.info(f"Account cash: {account_cash}")
        cash_invest = account_cash * cash_invest_ratio
        purchase_power = min(cash_invest, self.limit - self.traded)
        return purchase_power

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

    def prior_trades(self):
        start = datetime.datetime.now().date()

        while start.weekday() != 0:
            start -= datetime.timedelta(days=1)

        order_params = GetOrdersRequest(
            status=QueryOrderStatus.CLOSED,
            after=start,
            side=OrderSide.BUY,
        )

        orders = self.client.get_orders(order_params)
        traded = 0

        for order in orders:
            if order.status == OrderStatus.CANCELED:
                logger.info(f"Canceled order: {order}")
            elif order.status == OrderStatus.FILLED:
                if order.notional != None:
                    logger.info(f"Filled order: {order}")
                    traded += order.notional
                else:
                    logger.error(f"Filled order has no notional: {order}")
                    return -1
            else:
                logger.error(f"Unknown order status: {order}")
                return -1

        return traded

    def is_market_open(self):
        start = end = datetime.datetime.now().date()

        while end.weekday() != 4:
            end += datetime.timedelta(days=1)

        calendar = GetCalendarRequest(start=start, end=end)
        calendar = self.client.get_calendar(calendar)

        return len(calendar) > 0 and calendar[-1].date == start
