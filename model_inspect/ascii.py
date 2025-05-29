"""
ascii.py

Provides a class for rendering ASCII art using the Rich library.
"""

from rich.console import Console
from rich.panel import Panel


class AsciiArtDisplayer:
    """
    A class to handle displaying ASCII art using the Rich library.
    """

    def __init__(self) -> None:
        """
        Initializes the console for Rich output.
        """
        self.console = Console()

    def display(self) -> None:
        """
        Displays ASCII art within a styled Rich panel.
        """
        art: str = r"""
     __  __           _      _   _____                           _
    |  \/  |         | |    | | |_   _|                         | |
    | \  / | ___   __| | ___| |   | |  _ __  ___ _ __   ___  ___| |_
    | |\/| |/ _ \ / _` |/ _ \ |   | | | '_ \/ __| '_ \ / _ \/ __| __|
    | |  | | (_) | (_| |  __/ |  _| |_| | | \__ \ |_) |  __/ (__| |_
    |_|  |_|\___/ \__,_|\___|_| |_____|_| |_|___/ .__/ \___|\___|\__|
                                                | |
                                                |_|
        """
        panel: Panel = Panel.fit(
            art, title="Welcome", subtitle="Inspect Ai Models", border_style="bold green"
        )
        self.console.print(panel)
