![ModelInpect Banner](/images/ModelInspect.png)
[![black](https://github.com/interwebshack/modelinspect/actions/workflows/black.yml/badge.svg)](https://github.com/interwebshack/modelinspect/actions/workflows/black.yml)
[![License: Apache 2.0](https://img.shields.io/crates/l/apa)](https://opensource.org/license/mit/)

# Model Inspect  
Model Inspect is a tool for inspecting the contents of Ai Models.  

## Project Structure

```shell
model_inspect/
├── analyzers/
│   └── zipfile/                  # Zip File Analyzer
│       ├── __init__.py           # Package initializer
│       ├── decompression.py      # Decompression-related classes and functions
│       ├── decryption.py         # Decryption logic
│       ├── zip_info.py           # Classes for ZIP file metadata (like ZipInfo)
│       ├── zip_reader.py         # Logic for reading files within the ZIP archive
│       ├── exceptions.py         # Custom exception classes
│       ├── utils.py              # Utility functions used across the package
│       └── constants.py          # Constants used across the package
└── tests/                        # Directory for unit tests
    ├── __init__.py
    └── analyzers/
        ├── __init__.py
        └── zipfile/
            ├── __init__.py
            ├── test_decompression.py
            ├── test_decryption.py
            ├── test_zip_reader.py
            └── test_utils.py

```
## Limitations & Alternatives

`modelinspect` currently only examines [pytorch](https://pytorch.org/) models.  More to come in future versions.  
You might want to check alternatives such as [ModelScan](https://github.com/protectai/modelscan).  

## License

MIT (See [LICENSE](./LICENSE))

## Acknowledgements

This project is heavily inspired by the following projects: 
* [PickleScan](https://github.com/mmaitre314/picklescan)  
* [ModelScan](https://github.com/protectai/modelscan)  
* [Fickling](https://github.com/trailofbits/fickling)  
* [cpython-zipfile](https://github.com/akheron/cpython/blob/master/Lib/zipfile.py)  
