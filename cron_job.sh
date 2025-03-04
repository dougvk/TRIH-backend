#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the project directory
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export ENV_MODE="prod"  # Use production mode for cron jobs
export LOG_FILE="logs/cron_$(date +%Y%m%d_%H%M%S).log"

# Run the full pipeline
echo "Starting feed processing at $(date)" >> "$LOG_FILE"

# Ingest new episodes
python -m src.main ingest >> "$LOG_FILE" 2>&1

# Clean pending episodes
python -m src.main clean --all >> "$LOG_FILE" 2>&1

# Tag cleaned episodes
python -m src.main tag --all >> "$LOG_FILE" 2>&1

# Export the data (optional)
# Uncomment the following line to enable automatic exports
# python -m src.main export --format json --output "data/exports/export_$(date +%Y%m%d_%H%M%S).json" >> "$LOG_FILE" 2>&1

# Validate tags
python -m src.main validate --report "data/reports/validation_$(date +%Y%m%d_%H%M%S).json" >> "$LOG_FILE" 2>&1

echo "Completed feed processing at $(date)" >> "$LOG_FILE"

# Deactivate virtual environment
deactivate

# Example crontab entry (run daily at 2 AM):
# 0 2 * * * /path/to/cron_job.sh 