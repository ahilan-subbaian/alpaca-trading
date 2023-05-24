from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import os
from dotenv import load_dotenv
import datetime
import traderClient

load_dotenv()


apiKey = os.getenv('API_KEY')
secretKey = os.getenv('SECRET_KEY')

client = TradingClient(apiKey, secretKey, paper=True)
print([i.symbol for i in client.get_all_positions()])
