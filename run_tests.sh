#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Run pytest with specified options
# --maxfail=1: Stop after first failure
# --disable-warnings: Disable warning capture
# -v: Verbose output
# --cov=src: Enable coverage reporting for src directory
# --cov-report=term-missing: Show lines that need test coverage
pytest --maxfail=1 --disable-warnings -v --cov=src --cov-report=term-missing tests/

# Deactivate virtual environment
deactivate 