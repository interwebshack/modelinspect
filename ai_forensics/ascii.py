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
              _____   ______                       _
        /\   |_   _| |  ____|                     (_)
       /  \    | |   | |__ ___  _ __ ___ _ __  ___ _  ___ ___
      / /\ \   | |   |  __/ _ \| '__/ _ \ '_ \/ __| |/ __/ __|
     / ____ \ _| |_  | | | (_) | | |  __/ | | \__ \ | (__\__ \
    /_/    \_\_____| |_|  \___/|_|  \___|_| |_|___/_|\___|___/


        """
        panel: Panel = Panel.fit(
            art, title=None, subtitle="Inspect Ai Models", border_style="bold green"
        )
        self.console.print(panel)
