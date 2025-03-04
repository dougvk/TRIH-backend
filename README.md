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
# Run all tests with coverage
pytest --cov=src.modules tests/

# Current coverage:
# - Overall: 91%
# - database.py: 94%
# - validate.py: 93%
# - tag.py: 89%
# - ingest.py: 89%
# - main.py: 93%

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