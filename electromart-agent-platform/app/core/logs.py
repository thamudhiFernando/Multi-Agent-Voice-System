import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings

LOG_DIR = Path(settings.LOG_FILE).parent
LOG_DIR.mkdir(parents=True, exist_ok=True)

def configure_logging():
    #remove default logger
    logger.remove()

    #Add console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level= settings.LOG_LEVEL,
        colorize=True,
    )

    #Add file handler with rotation
    logger.add(
        settings.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level= settings.LOG_LEVEL,
        #Rotate when the file reaches 100MB
        rotation="100 MB",
        #Keeps logs for 30 days
        retention="30 days",
        #Compress the rotated logs
        compression="zip",
        #Thread safe loggin
        enqueue=True,
    )

    logger.info("Logging configured")
    return logger

#Initialize Logger
app_logger = configure_logging()

def get_logger():
    return app_logger