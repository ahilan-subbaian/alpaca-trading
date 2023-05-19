from dotenv import load_dotenv
import os
import json
import traderClient

load_dotenv()


def lambda_handler(event, context):

    apiKey = os.getenv('API_KEY')
    secretKey = os.getenv('SECRET_KEY')
    tickers = ["VONG", "SCHD", "SCHG", "SPGP", "RSP"]
    weeklyLimit = 50 / len(tickers)
    displace = 5
    timeout = 60

    client = traderClient.localClient(
        apiKey, secretKey, weeklyLimit, tickers, displace, timeout)
    return client.execute()
