from modelinspect.logger import configure_logging, logger
from pathlib import Path

# Initialize the logger
log_file = Path.cwd() / "modelinspect.log"
configure_logging(log_file)

__all__ = ["logger"]
