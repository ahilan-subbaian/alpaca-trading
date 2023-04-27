import os
from dotenv import load_dotenv

import tradingClient

load_dotenv()

apiKey = os.getenv('API_KEY')
secretKey = os.getenv('SECRET_KEY')

client = tradingClient.ClientTrading(apiKey, secretKey, paper=True)
print(client.execute(['VONG','SCHD','SCHG','SPGP','RSP']))