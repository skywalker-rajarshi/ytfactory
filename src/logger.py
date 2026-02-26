import logging
import os

def get_factory_logger(name="yt_factory"):
    """Sets up a logger that prints INFO to terminal and saves ERRORs to a file."""
    os.makedirs("data/logs", exist_ok=True)
    
    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers if the logger is called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 1. The File Handler (Captures only Warnings and Errors, saves to disk)
        file_handler = logging.FileHandler("data/logs/error_log.txt")
        file_handler.setLevel(logging.WARNING)
        file_formatter = logging.Formatter('%(asctime)s - %(module)s - [%(levelname)s] - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # 2. The Stream Handler (Captures everything, prints to your terminal)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s') # Keep terminal output clean
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger