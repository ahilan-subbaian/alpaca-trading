from lambda_function import *
import time
start = time.time()

testEvent = {
    'tickers': ["VONG", "SCHD", "SCHG", "SPGP", "RSP"],
    'limit': 50,
    'displace': 5,
    'timeout': 60
}

testContext = {}

print(lambda_handler(testEvent, testContext))

print(f"Total time: {time.time() - start}")
