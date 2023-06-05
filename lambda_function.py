from dotenv import load_dotenv
import os
import client
import logging

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    logger.info(f"Event passed in {event}")

    necessary_keys = ['symbols', 'limit', 'paper']
    missing_keys = [key for key in necessary_keys if key not in event]
    if missing_keys:
        missing_keys_str = ', '.join(missing_keys)
        logger.error(f"Event missing keys: {missing_keys_str}")
        return {"result": False, "message": f"Event missing keys: {missing_keys_str}"}

    symbols = event['symbols']
    limit = event['limit']
    paper = event['paper']

    logger.info(f"symbols: {symbols}, limit: {limit}, paper: {str(paper)}")

    # validate inputs
    if not isinstance(symbols, list) or len(symbols) == 0:
        logger.error("No symbols provided")
        return {"result": False, "message": "no symbols provided"}
    if not isinstance(limit, int) or limit <= 0:
        logger.error("Invalid limit provided")
        return {"result": False, "message": "invalid limit provided"}
    if not isinstance(paper, bool):
        logger.error("Invalid paper provided")
        return {"result": False, "message": "invalid paper provided"}

    apiKey = os.getenv(f'API_KEY_{"PAPER" if paper else "LIVE"}')
    secretKey = os.getenv(f'SECRET_KEY_{"PAPER" if paper else "LIVE"}')

    logger.info("API and Secret keys retrieved successfully")

    # make sure keys are not empty
    if not apiKey:
        logger.error("API Key is missing.")
        return {"result": False, "message": "API Key is missing."}

    if not secretKey:
        logger.error("Secret Key is missing.")
        return {"result": False, "message": "Secret Key is missing."}

    try:
        # Inititalize trading client
        connection = client.AlpacaClient(
            apiKey, secretKey, limit, symbols, paper)
    except Exception as e:
        error_message = f"Error initializing trading client: {str(e)}"
        logger.error(error_message)
        return {"result": False, "message": error_message}

    logger.info("AlpacaClient initialized successfully")

    try:
        response = connection.execute()
    except Exception as e:
        error_message = f"Error executing trading client actions: {type(e).__name__}, {str(e)}"
        logger.error(error_message)
        return {"result": False, "message": error_message}

    logger.info(f"Response received: {response}")

    if 'result' not in response or 'message' not in response:
        logger.error(
            f"Response message: {response}")
    elif not response['result']:
        logger.error(
            f"Response message: {response['message']}")
    else:
        logger.info(
            f"Response message: {response['message']}")

    return response
