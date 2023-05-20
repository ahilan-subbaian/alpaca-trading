from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import os
from dotenv import load_dotenv

load_dotenv()

apiKey = os.getenv('API_KEY')
secretKey = os.getenv('SECRET_KEY')

client = TradingClient(apiKey, secretKey, paper=True)
tickers = ["RSP", "SCHD", "VONG"]
assets = client.get_all_positions()
ticker_assets = [{'ticker': i.symbol, 'value': i.market_value}
                 for i in assets if i.symbol in tickers]
investmentTotal = 1
ticker_assets = [{'ticker': 'RSP', 'value': 50}, {
    'ticker': 'SCHD', 'value': 65}, {'ticker': 'VONG', 'value': 60}, {'value': 55}, {'value': 90}]
values = [i['value'] for i in ticker_assets]
values.sort(reverse=True)

total = sum(values) + investmentTotal
for index, value in enumerate(values):
    print(value, total / (len(values) - index))
    if value > total / (len(values) - index):
        total -= value
    else:
        print(total / (len(values) - index))
        break


# print(tickers)
# print(assets)
# print(ticker_assets)
