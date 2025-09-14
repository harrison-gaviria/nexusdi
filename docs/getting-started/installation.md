# Installation

## Requirements

NexusDI requires Python 3.8 or higher.

## Install from PyPI

```bash
pip install nexusdi
```

## Install from Source

If you want to install the latest development version:

```bash
git clone https://github.com/yourname/nexusdi.git
cd nexusdi
pip install -e .
```

## Verify Installation

You can verify that NexusDI is installed correctly by importing it:

```python
import nexusdi
print(nexusdi.__version__)  # Should print the version number
```

## Development Installation

If you want to contribute to NexusDI, install it in development mode with additional dependencies:

```bash
git clone https://github.com/yourname/nexusdi.git
cd nexusdi
pip install -e ".[dev]"
```

This will install additional packages for testing, linting, and documentation generation.

## Virtual Environment

It's recommended to use a virtual environment when working with NexusDI:

```bash
# Create virtual environment
python -m venv nexusdi-env

# Activate it (Windows)
nexusdi-env\Scripts\activate

# Activate it (Linux/Mac)
source nexusdi-env/bin/activate

# Install NexusDI
pip install nexusdi
```

## Next Steps

Once you have NexusDI installed, head over to the [Quick Start](quick-start.md) guide to begin using dependency injection in your Python applications.
