"""
cli.py

Main entry point for running the ASCII art display from the terminal.
"""

from ai_forensics.ascii import AsciiArtDisplayer


def main() -> None:
    """
    Entry point for displaying ASCII art using the AsciiArtDisplayer.
    """
    displayer = AsciiArtDisplayer()
    displayer.display()


if __name__ == "__main__":
    main()
