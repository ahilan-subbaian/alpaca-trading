import logging
from lambda_function import *
import time
start = time.time()

print(f"Start time: {start}\n\n")
logger = logging.getLogger(__name__)

testEvent = {
    'tickers': ["VONG", "SCHD", "SCHG", "SPGP", "RSP"],
    'limit': 50,
    'displace': 5,
    'timeout': 10,
    'logging': 'INFO',
    'paper': True,
}

testContext = {}

print()
print(lambda_handler(testEvent, testContext))
print(f"\n\nTotal time: {time.time() - start}")
