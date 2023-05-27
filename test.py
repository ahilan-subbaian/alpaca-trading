from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, OrderRequest, GetOrdersRequest, GetCalendarRequest
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


apiKey = os.getenv('API_KEY_PAPER')
secretKey = os.getenv('SECRET_KEY_PAPER')

client = traderClient.localClient(apiKey, secretKey, 100, [
                                  "VONG", "SCHD", "SCHG", "SPGP", "RSP"], 5, 10, paper=True)

start = end = datetime.datetime.now().date()

while end.weekday() != 4:
    end += datetime.timedelta(days=1)

calendar = GetCalendarRequest(start=start, end=end)
calendar = client.client.get_calendar(calendar)

print(calendar[-1].date == start)
