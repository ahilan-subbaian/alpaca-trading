from dotenv import load_dotenv
import os
import json
import client
import logging

load_dotenv()


def lambda_handler(event, context):

    # Removes all configururations from the logger
    # Sets logging configuration to "Time - Level - message"
    for handler in logging.getLogger().handlers:
        logging.getLogger().removeHandler(handler)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    logger = logging.getLogger(__name__)

    logger.info(f"Event passed in {event}")

    symbols = event['symbols']
    limit = event['limit']
    paper = event['paper']

    apiKey = os.getenv(f'API_KEY_{"PAPER" if paper else "LIVE"}')
    secretKey = os.getenv(f'SECRET_KEY_{"PAPER" if paper else "LIVE"}')

    # Inititalize trading client
    connection = client.AlpacaClient(
        apiKey, secretKey, limit, symbols, paper)

    traded = connection.prior_orders()

    if traded > limit * 1.05:
        logger.error(f"Traded <{traded}> over the limit <{limit}>.")
        return {"result": False}
    else:
        logger.info(
            f"Traded <{traded}> over the last 7 days (under the ${limit} limit).")

    return {"result": True}
