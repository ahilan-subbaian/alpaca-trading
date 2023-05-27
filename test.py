import pandas as pd
import pandas_market_calendars as mcal
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, OrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.enums import OrderSide, QueryOrderStatus, OrderStatus
import os
from dotenv import load_dotenv
import datetime
import traderClient
import logging
logging.basicConfig(level='INFO',
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

load_dotenv()


def is_market_open():
    # Get the NYSE calendar
    nyse = mcal.get_calendar('NYSE')

    # Get today's date
    start = end = datetime.datetime.now().date()

    while end.weekday() != 4:
        end += datetime.timedelta(days=1)

    # Get market schedule for today
    market_schedule = nyse.valid_days(
        start_date=start, end_date=end)

    # check if the last available date is today
    return not market_schedule.empty and market_schedule[-1].to_pydatetime().date() == start


print(is_market_open())
