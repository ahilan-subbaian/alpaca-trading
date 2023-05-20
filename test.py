import os
import logging

# Set the environment variable before calling logging.basicConfig()
os.environ['LOG_LEVEL'] = 'ERROR'  # Replace with your desired log level

# Retrieve the environment variable
log_level = os.getenv('LOG_LEVEL', 'INFO')

# Configure logging
logging.basicConfig(level=log_level)

# Log some messages
logging.debug('This is a debug log message')
logging.info('This is an info log message')
