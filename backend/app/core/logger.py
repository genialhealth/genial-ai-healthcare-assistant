import logging
import sys

# Define the log format
# %(asctime)s - Timestamp
# %(name)s - Which file/module the log came from
# %(levelname)s - INFO, ERROR, etc.
# %(message)s - The actual log text
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging():
    """
    Configures the root logger to output to stdout.
    Docker will automatically capture these logs.
    """
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # You can silence noisy third-party loggers here if needed
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger("app")
