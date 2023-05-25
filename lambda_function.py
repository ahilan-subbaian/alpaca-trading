from dotenv import load_dotenv
import os
import json
import traderClient
import logging

load_dotenv()


def lambda_handler(event, context):

    # Removes all configururations from the logger
    # Sets logging configuration to "Time - Level - message"
    for handler in logging.getLogger().handlers:
        logging.getLogger().removeHandler(handler)
    logging.basicConfig(level=event['logging'],
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    logger = logging.getLogger(__name__)

    logger.info(f"Event passed in {event}")

    tickers = event['tickers']
    limit = event['limit']
    displace = event['displace']
    timeout = event['timeout']
    paper = event['paper']
    prior_trades = event.get('prior_trades', False)

    apiKey = os.getenv(f'API_KEY_{"PAPER" if paper else "LIVE"}')
    secretKey = os.getenv(f'SECRET_KEY_{"PAPER" if paper else "LIVE"}')

    # Inititalize trading client
    client = traderClient.localClient(
        apiKey, secretKey, limit, tickers, displace, timeout, paper=paper)

    # response = client.equal_execute()
    response = client.handler(prior_trades=prior_trades)

    if not response['result']:
        logger.error(
            f"Response message: {response['message']}")
    else:
        logger.info(
            f"Response message: {response['message']}")

    # response = client.split_execute()

    # if not response['result']:
    #     logger.error(
    #         f"Response message: {response['message']}")
    # else:
    #     logger.info(
    #         f"Response message: {response['message']}")

    return response
