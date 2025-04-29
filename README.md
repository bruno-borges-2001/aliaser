# Aliaser

A command-line tool that lets users create terminal command aliases in a structured, persistent, and portable way.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📚 Overview

Aliaser helps you manage your shell aliases by providing a simple command-line interface to create, list, update, and delete aliases. It ensures that your aliases are:

- **Structured**: All aliases are stored in a dedicated section in your shell config file
- **Persistent**: Aliases survive shell restarts and system reboots
- **Portable**: Easily sync your aliases across different machines

Aliaser modifies your shell configuration file (`.zshrc`, `.bashrc`, etc.) in a safe, controlled way by only managing aliases within a specially marked section.

## ✨ Features

- Create new aliases that persist across shell sessions
- List all managed aliases in a formatted table
- Update existing aliases
- Delete aliases you no longer need
- Support for multiple shells (zsh, bash, fish)
- Validation to prevent conflicts with system commands
- Safe file handling with automatic backups

## 🔧 Installation

### Using uv (recommended)

The recommended way to install aliaser is using [uv](https://github.com/astral-sh/uv):

```bash
# Install directly from the repository
uv pip install git+https://github.com/yourusername/aliaser.git

# Or install locally after cloning
git clone https://github.com/yourusername/aliaser.git
cd aliaser
uv pip install .
```

### From Source with Development Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/aliaser.git
cd aliaser

# Install with dev dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## 🚀 Usage

### Creating an Alias

```bash
aliaser create gs "git status"
```

This adds the alias `gs` for the command `git status` to your shell configuration file.

### Listing All Aliases

```bash
aliaser list
```

This displays a formatted table of all aliases managed by aliaser.

### Updating an Alias

```bash
aliaser update gs "git status -sb"
```

This updates the `gs` alias to run `git status -sb` instead.

### Deleting an Alias

```bash
aliaser delete gs
```

This removes the `gs` alias from your shell configuration.

## 🐚 Shell Compatibility

Aliaser currently supports the following shells:

- **Zsh** (configuration file: `~/.zshrc`)
- **Bash** (configuration files: `~/.bash_profile` or `~/.bashrc`)
- **Fish** (configuration file: `~/.config/fish/config.fish`)

After adding or modifying aliases, you need to reload your shell configuration:

```bash
# For Zsh
source ~/.zshrc

# For Bash
source ~/.bashrc  # or ~/.bash_profile

# For Fish
source ~/.config/fish/config.fish
```

## 🛠️ Development

### Setting Up the Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/aliaser.git
cd aliaser

# Create and activate the virtual environment
uv venv
source .venv/bin/activate  # On Unix/macOS
# or
# .venv\Scripts\activate  # On Windows

# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Development Commands

We use a Makefile to simplify common development tasks:

```bash
# Install the package in development mode
make install-dev

# Run tests
make test

# Run linting checks
make lint

# Format code with black
make format

# Run pre-commit hooks on all files
make pre-commit

# Clean up build artifacts
make clean
```

### Project Structure

```
aliaser/
├── app/                # Main package
│   ├── __init__.py
│   ├── main.py         # Typer app entry point
│   ├── shell.py        # Shell detection & editing
│   └── utils.py        # Helper functions
├── tests/              # Test suite
│   ├── __init__.py
│   ├── test_main.py
│   ├── test_shell.py
│   └── test_utils.py
├── pyproject.toml      # Project configuration
├── .pre-commit-config.yaml  # Pre-commit hooks
├── Makefile            # Development automation
├── README.md           # This file
└── LICENSE             # MIT License
```

## 📋 Testing

Run the tests with pytest:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app

# Run a specific test file
pytest tests/test_main.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
