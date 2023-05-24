from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import os
from dotenv import load_dotenv
import datetime
import traderClient

load_dotenv()


def fridayRatio(displace):
    # Get today's date
    today = datetime.datetime.now()

    # get displaced start date
    end_date = datetime.datetime(
        today.year, (today.month + (today.day >= displace)) % 12, displace)

    # Finds the number of fridays from today to end date
    fridays = 0
    while today < end_date:
        if today.weekday() == 4:
            fridays += 1
        today += datetime.timedelta(days=1)

    # Division by 0 error and no month has more than 5 fridays
    if fridays <= 0 or fridays > 5:
        # logger.error("Friday: {friday}, will be set to 0")
        return 0

    invest_ratio = 1 / fridays
    return invest_ratio


for i in range(1, 31):
    print(f"Shift: {i}, number of fridays {fridayRatio(i)}")
