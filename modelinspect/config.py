import yaml
from pathlib import Path

def load_config(config_file: Path) -> dict:
    """
    Loads the YAML configuration file.

    Args:
        config_file (Path): Path to the YAML config file.

    Returns:
        dict: Dictionary containing the configuration or None if the file cannot be loaded.
    """
    if not config_file.exists():
        return None

    try:
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        print(f"Error reading config file: {e}")
        return None
