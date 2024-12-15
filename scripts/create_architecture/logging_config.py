import logging
import os

# Define the log file path
log_file_path = '/tmp/log_file.log'
  # Replace with your desired log file path
log_dir = os.path.dirname(log_file_path)
os.makedirs(log_dir, exist_ok=True)

# Create a logger with the name 'main_logger'
logger = logging.getLogger('main_logger')

# Set the log level for the logger to capture error and warning messages
logger.setLevel(logging.WARNING)  # This will capture WARNING and ERROR messages

# Define a formatter for log messages
formatter = logging.Formatter('%(levelname)s - %(message)s')

# Create a FileHandler to write log messages to the specified file
file_handler = logging.FileHandler(log_file_path)

# Set the log level for the file handler
file_handler.setLevel(logging.WARNING)  # This will capture WARNING and ERROR messages

# Set the formatter for the file handler
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

# Log an error message
logger.error("This is an error message")

# Log a warning message
logger.warning("This is a warning message")

# Log an info message (this won't be captured in the log file)
logger.info("This is an informational message")

# Now, only the error and warning messages will be written to the specified log file.
