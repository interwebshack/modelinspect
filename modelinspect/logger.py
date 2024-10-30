from loguru import logger
from pathlib import Path


def configure_logging(log_file: Path) -> None:
    """
    Configures Loguru logging. Logs to both console and a file in the CWD.

    Args:
        log_file (Path): The file path where logs should be written.
    """
    logger.remove()  # Remove the default logger configuration
    
    # Log to the console
    logger.add(lambda msg: print(msg, end=""), format="{time} {level} {message}", level="INFO")

    # Log to a file in CWD with rotation after 1 MB
    logger.add(log_file, format="{time} {level} {message}", level="DEBUG", rotation="1 MB")

