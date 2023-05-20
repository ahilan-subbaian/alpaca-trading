from dotenv import load_dotenv
import os
import json
import traderClient
import logging

load_dotenv()


def lambda_handler(event, context):

    for handler in logging.getLogger().handlers:
        logging.getLogger().removeHandler(handler)
    logging.basicConfig(level=event['logging'],
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    logger = logging.getLogger(__name__)

    logger.info(f"Event passed in {event}")

    apiKey = os.getenv('API_KEY')
    secretKey = os.getenv('SECRET_KEY')

    tickers = event['tickers']
    limit = event['limit']
    displace = event['displace']
    timeout = event['timeout']
    paper = event['paper']

    client = traderClient.localClient(
        apiKey, secretKey, limit, tickers, displace, timeout, paper=paper)

    response = client.execute()

    if not response['result']:
        logger.error(
            f"Response message: {response['message']}")
    else:
        logger.info(
            f"Response message: {response['message']}")

    return response
