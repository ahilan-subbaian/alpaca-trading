from lambda_function import *
import time
start = time.time()

testEvent = {}
testContext = {}

print(lambda_handler(testEvent, testContext))

print(f"Total time: {time.time() - start}")
