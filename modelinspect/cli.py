import click
from modelinspect.logger import configure_logging, logger
from pathlib import Path
from functools import wraps

def logging_decorator(func):
    """
    A decorator that initializes the logger before running any command.
    This ensures logging is initialized only after a command has started.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Initialize logging before running the actual command
        log_file = Path.cwd() / "logs/cli.log"
        configure_logging(log_file)
        logger.debug(f"Logging initialized. Logs will be written to: {log_file}")
        return func(*args, **kwargs)
    
    return wrapper

@click.group(context_settings=dict(help_option_names=['-h', '--help']), invoke_without_command=False)
def cli() -> None:
    """ModelInspect command-line tool for inspecting AI/ML models."""
    pass

@cli.command()
@click.argument("data")
@click.option("--uppercase", is_flag=True, help="Convert data to uppercase.")
@click.option("--repeat", type=int, default=1, show_default=True, help="Number of times to repeat the data.")
@click.option("--suffix", type=str, default="", show_default=True, help="String to append to the data.")
@logging_decorator
def process(data: str, uppercase: bool, repeat: int, suffix: str) -> None:
    """
    Processes the given DATA and logs the output with optional parameters.

    Args:
        data (str): The data to process.
        uppercase (bool): Convert data to uppercase if set.
        repeat (int): Number of times to repeat the data.
        suffix (str): Suffix to append to the data.
    """
    if uppercase:
        data = data.upper()

    processed_data = (data + suffix) * repeat

    click.echo(f"Processing data: {data}")
    click.echo(f"Final result: {processed_data}")

@cli.command()
@click.argument("name")
@logging_decorator
def greet(name: str) -> None:
    """
    Greets the given NAME with a simple message.

    Args:
        name (str): The name to greet.
    """
    click.echo(f"Hello, {name}!")
