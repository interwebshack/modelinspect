from pathlib import Path

import click

from modelinspect.logger import configure_logging, logger


def display_ascii_art() -> None:
    """
    Displays ASCII art before logging initialization.
    """
    art = r"""
     __  __           _      _   _____                           _   
    |  \/  |         | |    | | |_   _|                         | |  
    | \  / | ___   __| | ___| |   | |  _ __  ___ _ __   ___  ___| |_ 
    | |\/| |/ _ \ / _` |/ _ \ |   | | | '_ \/ __| '_ \ / _ \/ __| __|
    | |  | | (_) | (_| |  __/ |  _| |_| | | \__ \ |_) |  __/ (__| |_ 
    |_|  |_|\___/ \__,_|\___|_| |_____|_| |_|___/ .__/ \___|\___|\__|
                                                | |                  
                                                |_|                  
    """
    print(art)


class CustomGroup(click.Group):
    def invoke(self, ctx):
        # Display ASCII art before logging initialization
        display_ascii_art()

        # Initialize logging before running any command
        log_file = Path.cwd() / "modelinspect.log"
        config_file = Path.cwd() / "config.yaml"

        # Initialize logging and get the log level
        log_level = configure_logging(log_file, config_file)

        # Log the level and where logs will be written
        logger.info(f"Logging initialized at {log_level} level.")
        logger.info(f"Logs will be written to: {log_file}")

        # Now invoke the original command
        super().invoke(ctx)

    def format_help(self, ctx, formatter):
        display_ascii_art()
        super().format_help(ctx, formatter)


@click.group(cls=CustomGroup, context_settings=dict(help_option_names=["-h", "--help"]))
def cli():
    """ModelInspect command-line tool for inspecting AI/ML models."""
    pass


@cli.command()
@click.argument("data")
@click.option("--uppercase", is_flag=True, help="Convert data to uppercase.")
@click.option(
    "--repeat", type=int, default=1, show_default=True, help="Number of times to repeat the data."
)
@click.option(
    "--suffix", type=str, default="", show_default=True, help="String to append to the data."
)
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
def greet(name: str) -> None:
    """
    Greets the given NAME with a simple message.

    Args:
        name (str): The name to greet.
    """
    click.echo(f"Hello, {name}!")
