from alpaca.trading.client import TradingClient

from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import time
import datetime
import calendar

import os
from dotenv import load_dotenv
import OrderClient

load_dotenv()

apiKey = os.getenv('API_KEY')
secretKey = os.getenv('SECRET_KEY')


event = OrderClient.OrderClient(apiKey, secretKey, paper=True)

print(event.get_investments())
