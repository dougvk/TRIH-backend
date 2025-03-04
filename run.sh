#!/bin/bash

# Default to test mode
ENV_MODE="test"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prod)
            ENV_MODE="prod"
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Activate virtual environment
source venv/bin/activate

# Set environment mode
export ENV_MODE=$ENV_MODE

# Run the CLI with any remaining arguments
python -m src.main "$@"

# Deactivate virtual environment
deactivate 