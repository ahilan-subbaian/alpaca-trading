from dotenv import load_dotenv
import os
import client
import logging

load_dotenv()

# Removes all configururations from the logger
# Sets logging configuration to "Time - Level - message"
for handler in logging.getLogger().handlers:
    logging.getLogger().removeHandler(handler)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)


def lambda_handler(event: dict, context):

    logger.info(f"Event: {event}")

    # validate event having only the required keys
    only_keys = ['symbols', 'limit', 'paper']
    if sorted(only_keys) != sorted(event.keys()):
        logger.error(f"Event contains keys other than {only_keys}")
        return {"result": False, "message": f"Event contains keys other than {only_keys}"}

    symbols = event['symbols']
    limit = event['limit']
    paper = event['paper']

    apiKey = os.getenv(f'API_KEY_{"PAPER" if paper else "LIVE"}')
    secretKey = os.getenv(f'SECRET_KEY_{"PAPER" if paper else "LIVE"}')

    logger.info(
        "API keys, Secret keys, symbols, limit and paper retrieved successfully")

    # Inititalize trading client
    try:
        connection = client.AlpacaClient(
            apiKey=apiKey, secretKey=secretKey, symbols=symbols, limit=limit, paper=paper)
    except Exception as e:
        error_message = f"Error initializing trading client: {str(e)}"
        logger.error(error_message)
        return {"result": False, "message": error_message}

    logger.info("AlpacaClient initialized successfully")

    # Execute trading client actions
    try:
        response = connection.execute()
    except Exception as e:
        error_message = f"Error executing trading client actions: {type(e).__name__}, {str(e)}"
        logger.error(error_message)
        return {"result": False, "message": error_message}

    logger.info(f"Response received: {response}")

    # Validate response
    if 'result' not in response or 'message' not in response:
        logger.error(
            f"Response: {response} does not contain result or message")
    elif not response['result']:
        logger.error(
            f"Response message: {response['message']}")
    else:
        logger.info(
            f"Response message: {response['message']}")

    return response
