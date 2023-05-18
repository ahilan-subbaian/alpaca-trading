import os
from dotenv import load_dotenv

import OrderClient

load_dotenv()

apiKey = os.getenv('API_KEY')
secretKey = os.getenv('SECRET_KEY')

client = OrderClient.OrderClient(apiKey, secretKey, paper=True)
print(client.execute(['VONG', 'SCHD', 'SCHG', 'SPGP', 'RSP']))
