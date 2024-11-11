from pathlib import Path

from loguru import logger

from modelinspect.config import ConfigError, load_config


def configure_logging(log_file: Path, config_file: Path) -> str:
    """
    Configures Loguru logging for the project. Logs to both console and a file.

    Args:
        log_file (Path): The file path where logs should be written.
        config_file (Path): The path to the YAML configuration file.

    Returns:
        str: The configured log level.
    """
    try:
        # Load and verify YAML configuration
        config = load_config(config_file)
    except ConfigError as e:
        # Handle configuration errors (fall back to defaults)
        logger.warning(f"Configuration error: {e}. Using default log level 'INFO'.")
        config = {"logging": {"level": "INFO"}}

    log_level = config.get("logging", {}).get("level", "INFO")

    logger.remove()  # Remove the default logger configuration

    # Log to the console with dynamic log level
    logger.add(lambda msg: print(msg, end=""), format="{time} {level} {message}", level=log_level)

    # Log to a file with rotation after 1 MB
    logger.add(log_file, format="{time} {level} {message}", level=log_level, rotation="1 MB")

    return log_level
