import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, GetCalendarRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus, OrderStatus
import datetime
import time
import logging
from enum import Enum
from dateutil.relativedelta import relativedelta
import pandas_market_calendars as mcal

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

        is_open = self.is_market_open()
        logger.info(f"The market is {'open' if is_open else 'closed'}.")
        if not is_open:
            result["message"] = f"The market is {'open' if is_open else 'closed'}."
            return result

        self.traded = self.prior_orders()
        logger.info(f"Traded: {self.traded}")
        if self.traded < 0 or self.traded > self.limit * .95:
            result["message"] = f"Traded <{self.traded}> which is out of expected range."
            return result

        today = datetime.datetime.now()

        # Rebalancing occurs once every quarter
        if today.month % 3 == 0 and today.day < 8:
            result = self.equal_execute()
        else:
            result = self.split_execute()

        if result["result"] == False:
            return result

        trading_check = self.prior_orders()
        if trading_check < self.limit * 0.95 or trading_check > self.limit * 1.05:
            result["result"] = False
            result["message"] = f"Traded <{trading_check:.2f}> which is not similar to the limit <{self.limit:.2f}>"
            return result

        return result

    # uses alpaca calendar to see if market is open today
    def is_market_open(self):
        start = end = datetime.datetime.now().date()

        while end.weekday() != 4:
            end += datetime.timedelta(days=1)

        calendar = GetCalendarRequest(start=start, end=end)
        calendar = self.client.get_calendar(calendar)
        return calendar[-1].date == start

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
                if order.notional != None:
                    logger.info(
                        f"Canceled Order: created <{order.created_at}>, canceled <{order.canceled_at}>, symbol <{order.symbol}>, notional <{float(order.notional):.2f}>")
                elif order.qty != None:
                    logger.info(
                        f"Canceled Order: created <{order.created_at}>, canceled <{order.canceled_at}>, symbol <{order.symbol}>, notional <{float(order.qty):.2f}>")
                else:
                    logger.error(
                        f"Odd ordered processed: order id <{order.id}>")
                    return -1
            elif order.status == OrderStatus.FILLED or order.status == OrderStatus.ACCEPTED:
                if order.notional != None:
                    logger.info(
                        f"Order placed for {order.symbol} for ${float(order.notional):.2f}.")
                    traded += float(order.notional)
                elif order.qty != None:
                    logger.info(
                        f"Order placed for {order.symbol} for {float(order.qty):.2f} shares.")
                    traded += float(order.qty) * \
                        float(order.filled_avg_price)
                else:
                    logger.error(
                        f"Odd ordered processed: order id <{order.id}>")
                    return -1
            else:
                logger.error(
                    f"Status <{order.status}> is different than expected.")
                return self.limit

        return traded

    # Split Execute
    # Invests the same ammount in each ticker

    def split_execute(self):
        result = {"result": False, "message": "All orders failed"}
        logger.info("In localClient.split_execute()")

        ratio = self.fridayRatio()
        logger.info(f"Ratio: {ratio}")
        if ratio == 0:
            result['message'] = "Failed in retrieving ratio"
            return result

        purchase_power = self.purchase_power(ratio)
        logger.info(f"Purchase Power: {purchase_power}")
        if purchase_power <= 0:
            result["message"] = "Failed in retrieving purchase_power"
            return result

        investments = self.investments(purchase_power, Execute.SPLIT)
        logger.info(f"Investments: {investments}")
        if len(investments) == 0 or any([i not in self.tickers for i in investments]):
            result["message"] = "Failed in retrieving investments"
            return result

        orders = self.place_orders(investments)
        logger.info(f"Number of orders: {len(orders)}")
        if len(orders) == 0:
            result["message"] = "Failed in retrieving orders"
            return result

        time.sleep(self.timeout)

        messages = self.get_status(orders)
        logger.info(f"Messages: {messages}")
        if len(messages) > 0:
            result["message"] = ' '.join(messages)
            return result

        result["message"] = "Successfully completed all orders"
        result["result"] = True
        return result

    # Equal Execute
    # Rebalances the portfolio, all stocks tend towards equal value
    def equal_execute(self):
        result = {"result": False, "message": "All orders failed"}
        logger.info("In localClient.equal_execute()")

        ratio = self.fridayRatio()
        logger.info(f"Ratio: {ratio}")
        if ratio == 0:
            result['message'] = "Failed in retrieving ratio"
            return result

        purchase_power = self.purchase_power(ratio)
        logger.info(f"Purchase Power: {purchase_power}")
        if purchase_power <= 0:
            result["message"] = "Failed in retrieving purchase_power"
            return result

        ceiling = self.ceiling(purchase_power)
        logger.info(f"Ceiling: {ceiling:.2f}")
        if ceiling == 0:
            result["message"] = "Failed in retrieving ceiling"
            return result

        investments = self.investments(ceiling, Execute.EQUAL)
        logger.info(
            f"Investments: {({key: f'{value:.2f}' for key, value in investments.items()})}")
        if len(investments) == 0 or any([i not in self.tickers for i in investments]):
            result["message"] = "Failed in retrieving investments"
            return result

        orders = self.place_orders(investments)
        logger.info(f"Number of orders: {len(orders)}")
        if len(orders) == 0:
            result["message"] = "Failed in retrieving orders"
            return result

        time.sleep(self.timeout)

        messages = self.get_status(orders)
        logger.info(f"Messages: {messages}")
        if len(messages) > 0:
            result["message"] = ' '.join(messages)
            return result

        result["message"] = "Successfully completed all orders"
        result["result"] = True
        return result

    # Checks to make sure that all orders were filled,
    # returns a message holding all tickers that did not execute
    def get_status(self, orders):
        messages = []

        # Make sure all orders have been filled
        for order in orders:
            order_info = self.client.get_order_by_id(order.id)
            if order_info.status.lower() != 'filled':
                messages.append(
                    f"Order failed on {order_info.symbol} with status: {order_info.status.lower()} and amount: {float(order_info.notional):.2f}.")

        return messages

    # Places order for each {ticker: amount} in parameters
    def place_orders(self, investments):
        orders = []

        total_invested = 0
        for symbol, amount in investments.items():
            total_invested += amount
            if total_invested > (self.limit - self.traded) * 1.05:
                logger.error(
                    f"Investing {total_invested} which is over the limit <{self.limit}> - traded <{self.traded}>.")
            if amount > 0:
                orders.append(self.marketBuyOrder(symbol, amount))

        return orders

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

    # Calculates the intended investments for each ticker

    def investments(self, limit, execute):
        if execute not in Execute:
            logger.error(f"Execute type does not exist: {execute}")
            return 0

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
            limit = limit / len(self.tickers)
            for ticker in self.tickers:
                investments[ticker] = limit
            return investments

        logger.error(f"Did not find execute: {execute}")
        return {}

    # Finds the ceiling using averaging math
    # the ceiling is the value all investments should be at minimum
    def ceiling(self, purchase_power):
        asset_values = [self.get_position_value(
            ticker) for ticker in self.tickers]
        asset_values.sort(reverse=True)

        total = sum(asset_values) + purchase_power
        for index, value in enumerate(asset_values):
            ceiling = total / (len(asset_values) - index)
            if value > ceiling:
                total -= value
            else:
                logger.info(
                    f"Holding values: {[f'{value:.2f}' for value in asset_values]} and ceiling: {ceiling}")
                return ceiling

        logger.error(
            f"Ended beyond for loop in calculateInvestment, holdings: {[f'{value:.2f}' for value in asset_values]} and ceiling {ceiling}")
        return 0

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
