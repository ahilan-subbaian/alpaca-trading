from dotenv import load_dotenv
import os
import json
import traderClient
import time
start = time.time()


load_dotenv()

apiKey = os.getenv('API_KEY')
secretKey = os.getenv('SECRET_KEY')
weeklyLimit = float(os.getenv('WEEKLY_LIMIT'))
tickers = json.loads(os.getenv('TICKERS'))
displace = 5
timeout = 60


client = traderClient.localClient(
    apiKey, secretKey, weeklyLimit, tickers, displace, timeout)
print(client.execute())

print(f"Total time: {time.time() - start}")
