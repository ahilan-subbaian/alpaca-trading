import json
import os
from dotenv import load_dotenv

load_dotenv()

apiKey = os.getenv('API_KEY')
secretKey = os.getenv('SECRET_KEY')
weeklyLimit = os.getenv('WEEKLY_LIMIT')
tickers = json.loads(os.getenv('TICKERS'))

print(apiKey)
print(secretKey)
print(weeklyLimit)
print(tickers)
