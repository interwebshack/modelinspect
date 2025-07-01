![AI Forensics Banner](https://raw.githubusercontent.com/interwebshack/ai-forensics/main/images/AI_Forensics.png)

# AI Forensics  
Command-line tool for inspecting AI/ML models.

| Category          | Badge                                                                                       |
|-------------------|---------------------------------------------------------------------------------------------|
| License           | [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)][license]             |
| Black Formatter   | [![black]][black]                                                                           |
| Tests (main)      | [![Tests]][tests]                                                                           |
| Matrix Tests      | [![Matrix]][matrix]                                                                         |
| SonarCloud        | [![Quality Gate]][quality_gate]                                                             |
| CodeQL            | [![CodeQL Security Scan]][codeql]                                                           |

| Coverage          | [![Coverage]][coverage]                                                                     |
| Maintainability   | [![Maintainability Rating]][maintainability]                                                |
| Container Build   | [![Container]][container]                                                                   |
| Release & Signing | [![Release]][release]                                                                       |
| Release Verified  | [![Release Verified]][release_verified]                                                     |

[license]: https://opensource.org/license/MIT
[black]: https://github.com/interwebshack/ai-forensics/actions/workflows/black.yml/badge.svg
[tests]: https://github.com/interwebshack/ai-forensics/actions/workflows/test.yml/badge.svg
[matrix]: https://github.com/interwebshack/ai-forensics/actions/workflows/test-matrix.yml/badge.svg
[quality_gate]: https://sonarcloud.io/summary/new_code?id=interwebshack_ai-forensics
[codeql]: https://github.com/interwebshack/ai-forensics/actions/workflows/codeql.yml/badge.svg
[coverage]: https://sonarcloud.io/summary/new_code?id=interwebshack_ai-forensics
[maintainability]: https://sonarcloud.io/summary/new_code?id=interwebshack_ai-forensics
[container]: https://github.com/interwebshack/ai-forensics/actions/workflows/build-container.yml/badge.svg
[release]: https://github.com/interwebshack/ai-forensics/actions/workflows/release.yml/badge.svg
[release_verified]: https://github.com/yourgithubuser/ai-forensics/actions/workflows/verify-release.yml

## Supported Model Formats

| Format          | Status       | Supported Versions  | Description |
|-----------------|--------------|---------------------|-------------|
| **SafeTensors** | ✅ Supported | `≤ v0.5.3`          | Provides safe, zero-copy loading of AI model weights. `ai-forensics` can inspect and report metadata, tensor structure, and potential risks within `.safetensors` files. Version `≥ v0.5.3` is recommended due to a precision metadata fix. |
| **ONNX**        | 🚧 Planned   | _Not yet supported_ | Open Neural Network Exchange format. Planned for future releases to enable inspection of cross-framework models. |
| **GGUF**        | 🚧 Planned   | _Not yet supported_ | Format used by `llama.cpp` for quantized models. Support is planned to help with auditing local LLM deployments. |

  
## Project Structure

```shell
ai-forensics/
├── .github/                       # 📁 GitHub-specific configurations
│   └── workflows/                 # 📁 CI/CD workflow definitions for GitHub Actions
│       └── black.yaml             # 📄 GitHub Actions workflow for checking code formatting with Black
├── ai_forensics/                  # 📁 Main source code package
│   ├── __init__.py                # Initializes the package
│   ├── __main__.py                # Enables `python -m ai_forensics` to run the CLI
│   ├── ascii.py                   # Contains ASCII art display class using Rich
│   └── cli.py                     # CLI entry point
├── documentation/                 # 📁 Technical analysis and format-specific documentation
│   ├── gguf_analysis.md           # 📄 In-depth analysis of the GGUF model format
│   ├── onnx_analysis.md           # 📄 In-depth analysis of the ONNX (Open Neural Network Exchange) format
│   ├── safetensor_analysis.md     # 📄 In-depth analysis of the SafeTensors format
├── images/                        # 📁 Project-related images
│   └── AI_Forensics.png           # Project image/logo
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

`ai-forensics` is currently under development.  More to come in future versions.  


## License

MIT (See [LICENSE](./LICENSE))

## Acknowledgements

This project is heavily inspired by the following projects: 
* [PickleScan](https://github.com/mmaitre314/picklescan)  
* [ModelScan](https://github.com/protectai/modelscan)  
* [Fickling](https://github.com/trailofbits/fickling)  
