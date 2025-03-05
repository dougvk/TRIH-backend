# Podcast RSS Feed Processor

A high-performance Python CLI application for ingesting podcast RSS feeds, cleaning episode content, and automatically tagging episodes using a predefined taxonomy.

## Features

- RSS feed ingestion with duplicate detection
- Two-stage content cleaning (regex + AI)
- Automated episode tagging using OpenAI
- Export to JSON and CSV formats
- Tag validation against predefined taxonomy
- Comprehensive logging
- Test/Production mode separation

## Requirements

- Python 3.13+
- OpenAI API key
- RSS feed URL

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd podcast-rss-processor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # OR
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```bash
   cp .env.template .env
   ```

5. Edit `.env` and add your configuration:
   ```
   ENV_MODE=test
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-3.5-turbo
   RSS_FEED_URL=your_feed_url_here
   ```

## Usage

The application provides several commands for processing podcast episodes:

### Run Full Pipeline

```bash
# Run the complete pipeline and save output to file
python -m src.main ingest && python -m src.main clean --all && python -m src.main tag --all && python -m src.main validate > output.txt
```

### Ingest Episodes

```bash
# Ingest from configured RSS feed
python -m src.main ingest

# Ingest from specific URL
python -m src.main ingest --feed "https://example.com/feed.xml"
```

### Clean Episode Descriptions

```bash
# Clean a specific episode
python -m src.main clean --id 123

# Clean all pending episodes
python -m src.main clean --all
```

### Tag Episodes

```bash
# Tag a specific episode
python -m src.main tag --id 123

# Tag all untagged episodes
python -m src.main tag --all
```

### Export Data

```bash
# Export to JSON (default)
python -m src.main export

# Export to specific JSON file
python -m src.main export --format json --output latest_episodes.json

# Export to CSV
python -m src.main export --format csv --output episodes.csv
```

### Validate Tags

```bash
# Run validation and generate report
python -m src.main validate

# Specify custom report path
python -m src.main validate --report custom_report.json
```

### Production Mode

Add the `--prod` flag to any command to run in production mode:

```bash
python -m src.main --prod ingest
```

## Directory Structure

```
podcast-rss-processor/
├── src/
│   ├── main.py              # CLI entry point
│   ├── modules/
│   │   ├── ingest.py        # RSS feed ingestion
│   │   ├── clean.py         # Content cleaning
│   │   ├── tag.py          # Episode tagging
│   │   ├── export.py       # Data export
│   │   ├── validate.py     # Tag validation
│   │   └── database.py     # Database operations
│   └── constants/
│       └── taxonomy.py     # Tag taxonomy definitions
├── data/
│   ├── episodes.db         # Production database
│   ├── test_episodes.db    # Test database
│   ├── exports/           # Export directory
│   └── reports/           # Validation reports
├── logs/                  # Log files
├── tests/                 # Test files
├── .env                   # Configuration
├── .env.template          # Configuration template
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Development

### Running Tests

```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run all tests with coverage report
python -m pytest --cov=src tests/ --cov-report=term-missing

# Current coverage:
# - Overall: 96%
# - database.py: 94%
# - validate.py: 93%
# - tag.py: 89%
# - ingest.py: 89%
# - main.py: 93%
# - taxonomy.py: 100%

# Run specific test file
pytest tests/test_ingest.py -v
```

### Automated Testing

The project includes a test runner script:
```bash
./run_tests.sh
```

### Deployment

1. Use the deployment script:
   ```bash
   ./run.sh
   ```

2. For scheduled execution, use the cron job script:
   ```bash
   ./cron_job.sh
   ```

### Adding New Features

1. Create a new module in `src/modules/` if needed
2. Update the CLI interface in `src/main.py`
3. Add appropriate tests in `tests/`
4. Update documentation

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For support, please open an issue in the GitHub repository.

### Tag Validation Rules

The system enforces several validation rules for episode tags:

1. **Minimum Requirements**:
   - Each episode must have at least one theme tag
   - Each episode must have at least one track tag
   - Format tags are optional but follow special rules

2. **Format Tag Rules**:
   - An episode must be tagged as "Series Episodes" if:
     - The title contains "(Ep X)" or "(Part X)" where X is any number
     - The title contains "Part" followed by a number
     - The episode is part of a named series
   - An episode must be tagged as "RIHC Series" if the title starts with "RIHC:"
     - RIHC episodes must also have the "Series Episodes" tag
   - If no series rules apply, the episode should be tagged as "Standalone Episodes"

3. **Tag Limits**:
   - Format tags: Maximum of 2 tags allowed
   - Theme tags: No limit
   - Track tags: No limit

### Data Export

The export command supports two formats:

1. **JSON Format** (default):
   - Exports complete episode data
   - Preserves all metadata
   - Suitable for backups and data analysis

2. **CSV Format**:
   - Exports in a spreadsheet-friendly format
   - Includes essential fields
   - Suitable for quick analysis and sharing

Example export files are stored in the `data/exports/` directory by default. 