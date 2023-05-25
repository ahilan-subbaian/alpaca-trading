import logging
from lambda_function import *
import time
import json

file_path = "test.json"
with open(file_path, "r") as json_file:
    testEvent = json.load(json_file)
testContext = {}

start = time.time()

print(f"Start time: {start}\n\n")
logger = logging.getLogger(__name__)

lambda_handler(testEvent, testContext)

print(f"\n\nTotal time: {time.time() - start}")
