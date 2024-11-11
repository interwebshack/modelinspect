from pathlib import Path

import yaml


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


def load_config(config_file: Path) -> dict:
    """
    Loads and verifies the YAML configuration file.

    Args:
        config_file (Path): Path to the YAML config file.

    Returns:
        dict: Dictionary containing the configuration.

    Raises:
        ConfigError: If the file is missing or the content is invalid.
    """
    if not config_file.exists():
        raise ConfigError(f"Configuration file '{config_file}' not found.")

    try:
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)

            # Validate the presence of required sections
            if "logging" not in config:
                raise ConfigError("Missing 'logging' section in the configuration file.")

            # Additional validation for logging section
            valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            log_level = config["logging"].get("level")

            if not log_level or log_level not in valid_levels:
                raise ConfigError(
                    f"Invalid log level '{log_level}' in the 'logging' section. "
                    f"Must be one of {', '.join(valid_levels)}."
                )

            return config

    except yaml.YAMLError as e:
        # Re-raise the YAML parsing error with context
        raise ConfigError(f"Error parsing YAML file: {e}") from e
