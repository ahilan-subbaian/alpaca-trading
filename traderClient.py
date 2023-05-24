from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import datetime
import time
import logging

logger = logging.getLogger(__name__)


class localClient:
    def __init__(self, apiKey, secretKey, limit, tickers, displace, timeout, paper=True):
        self.client = TradingClient(apiKey, secretKey, paper=paper)
        self.displace = displace
        self.tickers = tickers
        self.limit = limit
        self.timeout = timeout

    # Retrieves all investments from Alpaca
    def get_investments(self):
        return self.client.get_all_positions()

    # Gets the ratio of Fridays that exist between now and the next transfer date
    def fridayRatio(self):
        # Get today's date
        today = datetime.datetime.now()

        # get displaced start date
        end_date = datetime.datetime(
            today.year, (today.month + (today.day >= self.displace)) % 12, self.displace)

        # Finds the number of fridays from today to end date
        fridays = 0
        while today < end_date:
            if today.weekday() == 4:
                fridays += 1
            today += datetime.timedelta(days=1)

        # Division by 0 error and no month has more than 5 fridays
        if fridays <= 0 or fridays > 5:
            logger.error("Friday: {friday}, will be set to 0")
            return 0

        invest_ratio = 1 / fridays
        return invest_ratio

    # Calcualtes the total investment amount of this run
    # by comparing the amount by what is left in the account
    # and the passed in limit
    def equalInvestmentAmount(self):
        dollarValue = self.fridayRatio() * self.get_cash()

        logger.info(
            f"Investable cash by ratio: ${dollarValue:.2f} and investable cash by limit: ${self.limit}")

        return min(dollarValue, self.limit)

    # Calcaultes the amount that should be invested in each ticker
    # grabing the cash in the account comapred to the limit
    def investmentAmount(self):
        dollarValue = self.fridayRatio() * self.get_cash()
        limit = self.limit / len(self.tickers)

        logger.info(
            f"Investable cash by ratio: ${dollarValue:.2f} and investable cash by limit: ${limit}")

        return min(dollarValue, limit)

    # Get the cash amount in the account
    def get_cash(self):
        return float(self.client.get_account().cash)

    # Creates a market order and returns the order details
    def marketBuyOrder(self, symbol, dollarValue):
        order = MarketOrderRequest(symbol=symbol, notional=dollarValue, side=OrderSide.BUY,
                                   time_in_force=TimeInForce.DAY)
        order_details = self.client.submit_order(order)
        return order_details

    #  Place order for all tickers with the same dollarValue.
    #  Terminates if dollar value passes the limit
    def placeAllOrders(self, dollarValue):
        orderInfos = []
        total = 0
        for ticker in self.tickers:
            total += dollarValue
            if total > self.limit * 1.01:
                logger.error(f"Transactions exceeding limit: {self.limit}")
            orderInfos.append(self.marketBuyOrder(ticker, dollarValue))
        return orderInfos

    # Uses ceiling to calcualte the ammount that should
    # be invested by all tickers
    def placeEqualOrders(self, ceiling):
        # Calculate the amount to be invested in each stock
        assets = self.client.get_all_positions()
        values = []
        for i in assets:
            if i.symbol in self.tickers and float(i.market_value) < ceiling:
                values.append(
                    {'ticker': i.symbol, 'invest': ceiling - float(i.market_value)})

        logger.info(f"Investing positions: {values}")

        # Place order for each asset that is believe the ceiling
        orderInfos = []
        total = 0
        for position in values:
            total += position['invest']
            if total > self.limit * 1.01:
                logger.error(f"Transactions exceeding limit: {self.limit}")
            orderInfos.append(self.marketBuyOrder(
                position['ticker'], position['invest']))
        return orderInfos

    #  Calculates the ceiling to be invested on with
    def calculateInvestment(self, totalValue):
        assets = self.client.get_all_positions()
        values = [float(i.market_value)
                  for i in assets if i.symbol in self.tickers]
        values.sort(reverse=True)

        total = sum(values) + totalValue
        for index, value in enumerate(values):
            ceiling = total / (len(values) - index)
            if value > ceiling:
                total -= value
            else:
                logger.info(f"Holding values: {values} and ceiling: {ceiling}")
                return ceiling

        logger.error(
            f"Ended beyond for loop in calculateInvestment, holdings: {values} and ceiling {ceiling}")
        return 0

    # Checks to make sure that all orders were filled,
    # returns a message holding all tickers that did not execute
    def getStatus(self, orders):
        statuses = [self.client.get_order_by_id(
            order.id).status.lower() for order in orders]

        messages = []

        # Make sure all orders have been filled
        for ticker, status in zip(self.tickers, statuses):
            if status != 'filled':
                messages.append(
                    f"Order failed on {ticker} with status: {status}.")

        return messages

    #  master command for even split execute
    def execute(self):
        result = {"result": False, "message": "All orders failed"}
        logger.info("In localClient.execute()")

        dollarValue = self.investmentAmount()
        orders = self.placeAllOrders(dollarValue)
        time.sleep(self.timeout)
        messages = self.getStatus(orders)

        if len(messages) == 0:
            result["result"] = True
            result["message"] = "Successfully completed all orders"
        else:
            result["result"] = False
            result['message'] = ' '.join(messages)

        return result

    # master command for equal weighting investments
    def execute_equal(self):
        result = {"result": False, "message": "All orders failed"}
        logger.info("In localClient.execute_equal()")

        dollarValue = self.equalInvestmentAmount()
        ceiling = self.calculateInvestment(dollarValue)
        orders = self.placeEqualOrders(ceiling)
        time.sleep(self.timeout)
        messages = self.getStatus(orders)

        if len(messages) == 0:
            result["result"] = True
            result["message"] = "Successfully completed all orders"
        else:
            result["result"] = False
            result['message'] = ' '.join(messages)

        return result
