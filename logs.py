import logging

# Create a logger instance
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define a formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Define a console handler and set the formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)
