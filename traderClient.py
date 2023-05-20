from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import datetime
import time


def calculate_fridays(day_displace):

    # gets number of fridays [start, end)
    def fridays_between(start, end):
        fridays = 0
        while start < end:
            if start.weekday() == 4:
                fridays += 1
            start += datetime.timedelta(days=1)
        return fridays

    # Get today's date
    today = datetime.datetime.now()

    # get displaced start date
    end_date = datetime.datetime(
        today.year, (today.month + (today.day >= day_displace)) % 12, day_displace)

    return 0 if (days := fridays_between(today, end_date)) == 0 else 1 / days


class localClient:
    def __init__(self, apiKey, secretKey, limit, tickers, displace, timeout, paper=True):
        self.client = TradingClient(apiKey, secretKey, paper=paper)
        self.displace = displace
        self.tickers = tickers
        self.limit = limit
        self.timeout = timeout

    def get_investments(self):
        holdings = self.client.get_all_positions()
        return holdings

    def get_cash(self):
        return float(self.client.get_account().cash)

    def marketBuyOrder(self, symbol, dollarValue):
        order = MarketOrderRequest(symbol=symbol, notional=dollarValue, side=OrderSide.BUY,
                                   time_in_force=TimeInForce.DAY)
        order_details = self.client.submit_order(order)
        return order_details

    def placeAllOrders(self, dollarValue):
        orderInfos = []
        for ticker in self.tickers:
            orderInfos.append(self.marketBuyOrder(ticker, dollarValue))
        return orderInfos

    def execute(self):
        result = {"result": False, "message": "All orders failed"}
        dollarValue = min(calculate_fridays(self.displace) *
                          self.get_cash(), self.limit)
        orders = self.placeAllOrders(dollarValue)

        time.sleep(self.timeout)

        statuses = [self.client.get_order_by_id(
            order.id).status.lower() for order in orders]

        messages = []

        for ticker, status in zip(self.tickers, statuses):
            if status != 'filled':
                messages.append(
                    f"Order failed on {ticker} with status: {status}.")

        if len(messages) > 0:
            result["result"] = True
            result["message"] = "Successfully completed all orders"
        else:
            result["result"] = False
            result['message'] = ' '.join(messages)

        return result
