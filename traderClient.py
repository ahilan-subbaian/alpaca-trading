from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, GetCalendarRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus, OrderStatus
import datetime
import time
import logging
from enum import Enum
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

# Defines execute types as a value


class Execute(Enum):
    EQUAL = 0
    SPLIT = 1


class localClient:
    def __init__(self, apiKey, secretKey, limit, tickers, displace, timeout, paper=True):
        self.client = TradingClient(apiKey, secretKey, paper=paper)
        self.displace = displace
        self.tickers = tickers
        self.limit = limit
        self.timeout = timeout
        self.traded = 0

    # Routes the caller to the specified execute type
    def handler(self):
        result = {"result": False, "message": "Handler failed"}

        today = datetime.datetime.now()

        # Rebalancing occurs once every quarter
        if today.month % 3 == 0 and today.day < 8:
            execute = Execute.EQUAL
        else:
            execute = Execute.SPLIT
        logger.info(f"Will be executing script as {execute}.")

        # Check to see if the market is open
        is_market_open = self.is_market_open()
        logger.info(f"is_market_open: {is_market_open}")
        # fail if the market is closed, will return true since this is not an error
        if not is_market_open:
            result["result"] = True
            result["message"] = f"The market is {'open' if is_market_open else 'closed'}."
            return result

        # gets the amount of money to invest in stocks for this week
        self.traded = self.prior_orders(days=5)
        logger.info(f"Traded {self.traded} this week.")
        # fail if the amount of money traded is out of the expected range
        if self.traded < 0 or self.traded > self.limit * .95:
            result["message"] = f"Traded <{self.traded}> which is out of expected range."
            return result

        # checks how many fridays are left in the month to determine the ratio
        cash_invest_ratio = self.fridayRatio()
        logger.info(f"fridayRatio: {cash_invest_ratio}")
        # fail if the ratio is not a positive number (undefined or error in calculation)
        if cash_invest_ratio == 0:
            result['message'] = "Failed in retrieving ratio"
            return result

        # this is the total amount that will beinvested in stocks this week
        purchase_power = self.purchase_power(cash_invest_ratio)
        logger.info(f"Purchase Power: {purchase_power}")
        # issue if the purchase power is not a positive number (undefined or error in calculation)
        if purchase_power <= 0:
            result["message"] = "Failed in retrieving purchase_power"
            return result

        # this is the maximum amount that can be invested in a single stock
        investing_maximum = self.ceiling(purchase_power, execute)
        logger.info(f"Ceiling: {investing_maximum:.2f}")
        # fail if the ceiling is not a positive number (undefined or error in calculation)
        if investing_maximum <= 0:
            result["message"] = "Failed in retrieving ceiling"
            return result

        # this is the amount to be invested in each stock
        individal_investments = self.investments(investing_maximum, execute)
        logger.info(f"Investments: {individal_investments}")
        # investments need to exist, investments need to all be in self.tickers, and investments need to be less than the purchase power
        if len(individal_investments) == 0 or any([i not in self.tickers for i in individal_investments]) or sum(individal_investments.values()) > self.limit - self.traded:
            result["message"] = "Failed in retrieving investments"
            return result

        # places the orders
        order_information = self.place_orders(individal_investments)
        logger.info(f"Place_orders: {order_information}")
        # fail if there are no orders or if there are more orders than there are stocks
        if len(order_information) == 0 or len(order_information) > len(self.tickers):
            result["message"] = "Failed in retrieving orders"
            return result

        # waits for the orders to be filled
        time.sleep(self.timeout)

        # checks the status of the orders
        unfilled_orders = self.get_status(order_information)
        logger.info(f"Get Status: {unfilled_orders}")
        # fail if there are any errors in placing the orders
        if unfilled_orders > 0:
            result["message"] = f"Number of errors in placing orders: {unfilled_orders}"
            return result

        # checks to see if the orders are within the expected range
        total_traded = self.prior_orders(days=5)
        logger.info(f"Trading check: {total_traded}")
        # fail if the orders are not within the expected range
        if total_traded < self.limit * 0.95 or total_traded > self.limit * 1.05:
            result["message"] = f"Traded <{total_traded:.2f}> which is not similar to the limit <{self.limit:.2f}>"
            return result

        # success
        result["message"] = "Successfully completed all orders"
        result["result"] = True

        return result

    # uses alpaca calendar to see if market is open today
    def is_market_open(self):
        start = end = datetime.datetime.now().date()

        while end.weekday() != 4:
            end += datetime.timedelta(days=1)

        calendar = GetCalendarRequest(start=start, end=end)
        calendar = self.client.get_calendar(calendar)
        return len(calendar) > 0 and calendar[-1].date == start

    # Checks the orders placed in the last week to minimize over trading in one week

    def prior_orders(self, days=6):

        order_params = GetOrdersRequest(
            status=QueryOrderStatus.CLOSED,
            after=datetime.datetime.now() - datetime.timedelta(days=days),
            side=OrderSide.BUY,
        )

        orders = self.client.get_orders(order_params)
        traded = 0

        for order in orders:
            if order.status == OrderStatus.CANCELED:
                logger.info(
                    f"Canceled Order: created <{order.created_at}>, canceled <{order.canceled_at}>, symbol <{order.symbol}>, notional <{float(order.notional):.2f}>, qty <{float(order.qty):.2f}>")
            elif order.status == OrderStatus.FILLED:
                if order.notional != None:
                    logger.info(
                        f"Order placed for {order.symbol} for ${float(order.notional):.2f}.")
                    traded += float(order.notional)
                else:
                    logger.error(
                        f"Odd ordered processed: order id <{order.id}>")
                    return -1
            else:
                logger.error(
                    f"Status <{order.status}> is different than expected.")
                return -1

        return traded

    # Checks to make sure that all orders were filled,
    # returns a message holding all tickers that did not execute
    def get_status(self, orders):
        unfilled_orders = 0

        # Make sure all orders have been filled
        for order in orders:
            order_info = self.client.get_order_by_id(order.id)
            if order_info.status.lower() != 'filled':
                logger.error(
                    f"Order failed on {order_info.symbol} with status: {order_info.status.lower()} and amount: {float(order_info.notional):.2f}.")
                unfilled_orders += 1

        return unfilled_orders

    # Places order for each {ticker: amount} in parameters
    def place_orders(self, investments):
        order_info = []

        total_invested = 0
        for ticker, amount in investments.items():
            total_invested += amount
            if total_invested > (self.limit - self.traded) * 1.05:
                logger.error(
                    f"Investing {total_invested} which is over the limit <{self.limit}> - traded <{self.traded}>.")
                return []
            if amount > 0:
                order_info.append(self.marketBuyOrder(ticker, amount))

        return order_info

    # Creates a market order and returns the order details
    def marketBuyOrder(self, symbol, amount):
        order = MarketOrderRequest(symbol=symbol, notional=amount, side=OrderSide.BUY,
                                   time_in_force=TimeInForce.DAY)
        order_details = self.client.submit_order(order)
        logger.info(f"Placed an order for {symbol} with ${amount}.")
        return order_details

    def get_position_value(self, ticker):
        try:
            return float(self.client.get_open_position(ticker).market_value)
        except Exception as e:
            logger.info(f"Unable to get market value for {ticker}")
            return 0

    def validate_execute_type(self, execute):
        if execute not in Execute:
            logger.error(f"Execute type does not exist: {execute}")
            return False
        return True

    # Calculates the intended investments for each ticker

    def investments(self, limit, execute):
        if not self.validate_execute_type(execute):
            return {}

        investments = {}

        # if market value is below limit, add ticker to investments
        if execute == Execute.EQUAL:
            for ticker in self.tickers:
                investments[ticker] = max(
                    0, limit - self.get_position_value(ticker))
            return investments

        # Adds all tickers to investments with
        # the total investment amount divided by number of tickers
        if execute == Execute.SPLIT:
            for ticker in self.tickers:
                investments[ticker] = limit
            return investments

        logger.error(
            f"Did not find execute: {execute}, in function investments()")
        return {}

    # Finds the ceiling using averaging math
    # the ceiling is the value all investments should be at minimum
    def ceiling(self, purchase_power, execute):
        if not self.validate_execute_type(execute):
            return -1

        if execute == Execute.EQUAL:
            asset_values = [self.get_position_value(
                ticker) for ticker in self.tickers]
            asset_values.sort(reverse=True)

            total = sum(asset_values) + purchase_power
            for index, value in enumerate(asset_values):
                ceiling = total / (len(asset_values) - index)
                if value > ceiling:
                    total -= value
                else:
                    if len(asset_values) * ceiling > sum(asset_values) + purchase_power:
                        logger.error(
                            f"Ceiling is too high: {ceiling}, aasets: {[f'{value:.2f}' for value in asset_values]}")
                        return -1
                    logger.info(
                        f"Holding values: {[f'{value:.2f}' for value in asset_values]} and ceiling: {ceiling}")
                    return ceiling

            logger.error(
                f"Ended beyond for loop in calculateInvestment, holdings: {[f'{value:.2f}' for value in asset_values]} and ceiling {ceiling}")
            return -1

        if execute == Execute.SPLIT:
            return purchase_power / len(self.tickers)

        logger.error(f"Did not find execute: {execute}, in function ceiling()")
        return -1

    # Finds the amount that will be in

    def purchase_power(self, ratio):
        account_cash = self.get_cash()
        limit = account_cash * ratio
        return min(limit, self.limit - self.traded)

    # Get the cash amount in the account
    def get_cash(self):
        return float(self.client.get_account().cash)

    # Gets the ratio of Fridays that exist between now and the next transfer date
    def fridayRatio(self):
        # Get today's date
        today = datetime.datetime.now()

        # get displaced start date
        end_date = datetime.datetime(
            today.year, today.month, self.displace) + (relativedelta(months=1) if today.day >= self.displace else relativedelta())

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

    # Retrieves all investments from Alpaca
    def get_investments(self):
        return self.client.get_all_positions()
