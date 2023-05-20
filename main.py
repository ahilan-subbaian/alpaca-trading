from lambda_function import *
import time
start = time.time()

testEvent = {
    'tickers': ["VONG", "SCHD", "SCHG", "SPGP", "RSP"],
    'limit': 50,
    'displace': 5,
    'timeout': 10,
    'paper': True
}

testContext = {}

print(lambda_handler(testEvent, testContext))

print()
print()
print(f"Total time: {time.time() - start}")
