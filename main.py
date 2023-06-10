import logging
import time
import json
import client
import os
import dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

dotenv.load_dotenv()


def main():
    file_path = "event.json"
    with open(file_path, "r") as json_file:
        event = json.load(json_file)

    logger.info(f"Event: {event}")

    only_keys = ["symbols", "limit", "paper"]
    if sorted(only_keys) != sorted(event.keys()):
        logger.error(f"Event contains keys other than {only_keys}")
        return {
            "result": False,
            "message": f"Event contains keys other than {only_keys}",
        }

    symbols = event["symbols"]
    limit = event["limit"]
    paper = event["paper"]

    apiKey = os.getenv(f'API_KEY_{"PAPER" if paper else "LIVE"}')
    secretKey = os.getenv(f'SECRET_KEY_{"PAPER" if paper else "LIVE"}')

    logger.info(apiKey, secretKey)

    logger.info(
        "API keys, Secret keys, symbols, limit and paper retrieved successfully"
    )

    try:
        connection = client.AlpacaClient(
            apiKey=apiKey,
            secretKey=secretKey,
            symbols=symbols,
            limit=limit,
            paper=paper,
        )
    except Exception as e:
        error_message = f"Error initializing trading client: {str(e)}"
        return {"result": False, "message": error_message}

    logger.info("AlpacaClient initialized successfully")

    try:
        response = connection.execute()
    except Exception as e:
        error_message = (
            f"Error executing trading client actions: {type(e).__name__}, {str(e)}"
        )
        return {"result": False, "message": error_message}

    logger.info(f"Response received: {response}")

    return response


if __name__ == "__main__":
    start = time.time()
    logger.info(f"Start time: {start}\n\n")

    response = main()

    if response["result"]:
        logger.info(response["message"])
    else:
        logger.error(response["message"])

    logger.info(f"\n\nTotal time: {time.time() - start}")
