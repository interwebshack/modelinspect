![AI Forensics Banner](https://raw.githubusercontent.com/interwebshack/aiforensics/main/images/AI_Forensics.png)

# AI Forensics  
Command-line tool for inspecting AI/ML models.

|          |                                                                                                    |
|----------|----------------------------------------------------------------------------------------------------|
| Testing  | [![black](https://github.com/interwebshack/aiforensics/actions/workflows/black.yml/badge.svg)](https://github.com/interwebshack/aiforensics/actions/workflows/black.yml) |
| Meta     | [![License: Apache 2.0](https://img.shields.io/crates/l/apa)](https://opensource.org/license/mit/) |
|          |                                                                                                    |
  

## Project Structure

```shell
aiforensics/
├── images/                        # 📁 Project-related images
│   └── AI_Forensics.png           # Project image/logo
├── ai_forensics/                 # 📁 Main source code package
│   ├── __init__.py                # Initializes the package
│   ├── __main__.py                # Enables `python -m ai_forensics` to run the CLI
│   ├── ascii.py                   # Contains ASCII art display class using Rich
│   └── cli.py                     # CLI entry point
├── tests/                         # 📁 Test suite
│   └── __init__.py                # Marks this directory as a Python package
├── .gitignore                     # 📄 Specifies intentionally untracked files to ignore in Git
├── .pylintrc                      # 📄 Pylint configuration file for static code analysis
├── LICENSE                        # 📄 License file (e.g., MIT) defining terms of use
├── mypy.ini                       # 📄 Configuration for mypy static type checker
├── poetry.lock                    # 📄 Locked dependency versions (auto-generated by Poetry)
├── pyproject.toml                 # 📄 Main project configuration for Poetry and build system
├── README.md                      # 📄 Project description, usage, setup instructions

```
## Limitations & Alternatives

`aiforensics` is currently under development.  More to come in future versions.  


## License

MIT (See [LICENSE](./LICENSE))

## Acknowledgements

This project is heavily inspired by the following projects: 
* [PickleScan](https://github.com/mmaitre314/picklescan)  
* [ModelScan](https://github.com/protectai/modelscan)  
* [Fickling](https://github.com/trailofbits/fickling)  
