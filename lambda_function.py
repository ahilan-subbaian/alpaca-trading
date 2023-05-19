from dotenv import load_dotenv
import os
import json
import traderClient

load_dotenv()


def lambda_handler(event, context):

    apiKey = os.getenv('API_KEY')
    secretKey = os.getenv('SECRET_KEY')

    tickers = event['tickers']
    limit = event['limit']
    displace = event['displace']
    timeout = event['timeout']
    paper = event['paper']

    client = traderClient.localClient(
        apiKey, secretKey, limit, tickers, displace, timeout, paper=paper)
    return client.execute()
