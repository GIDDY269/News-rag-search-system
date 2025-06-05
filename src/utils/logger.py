import logging
import os
import sys
import inspect
from datetime import datetime



def setup_logger(level=logging.INFO):
    """Function to setup a logger with a specific name and log file."""

    file_name  = f'{datetime.now().strftime("%Y-%m-%d_%H_%M_%S")}.log'
    os.makedirs('logs',exist_ok=True)
    log_file = os.path.join('logs',file_name)

    # Create a custom logger
    running_filename = os.path.basename(inspect.stack()[1].filename) # get name of calling file
    logger = logging.getLogger(running_filename)
    logger.setLevel(level)

    # Create handlers
    c_handler = logging.StreamHandler(sys.stdout)
    f_handler = logging.FileHandler(log_file)

    # Set level for handlers
    c_handler.setLevel(level)
    f_handler.setLevel(level)

    # Create formatters and add them to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s - Line: %(lineno)d')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - Line: %(lineno)d')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger
