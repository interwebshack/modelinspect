from modelinspect.cli import cli

if __name__ == "__main__":
    # standalone_mode=False:
    # This tells Click not to handle exceptions or exit on its own,
    # giving you control over the output.
    cli(prog_name="modelinspect", standalone_mode=False)
