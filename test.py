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


apiKey = os.getenv('API_KEY')
secretKey = os.getenv('SECRET_KEY')

client = traderClient.localClient(apiKey, secretKey, 100, [
                                  "VONG", "SCHD", "SCHG", "SPGP", "RSP"], 5, 10, paper=True)
print(client.prior_orders())
print(client.traded)

# request_params = GetOrdersRequest(
#     status=QueryOrderStatus.CLOSED,
#     after=datetime.datetime.now() - datetime.timedelta(days=7),
#     side=OrderSide.BUY,
# )

# client = TradingClient(apiKey, secretKey, paper=True)
# orders = client.get_orders(request_params)

# for order in orders:
#     if order.status == OrderStatus.CANCELED:
#         print(
#             f"Canceled Order: created <{order.created_at}>, canceled <{order.canceled_at}>, symbol <{order.symbol}>, "
#             f"notional <{order.notional}>, quantity <{order.qty}>")
#     else:
#         print("The order was not canceled")
