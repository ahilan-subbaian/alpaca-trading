import logging
from lambda_function import *
import time
import json

file_path = "configs/alpaca_orders_schedule_DEV.json"
with open(file_path, "r") as json_file:
    testEvent = json.load(json_file)["Input"]
testContext = {}
logger = logging.getLogger(__name__)

start = time.time()
print(f"Start time: {start}\n\n")

lambda_handler(testEvent, testContext)

print(f"\n\nTotal time: {time.time() - start}")
