#!/usr/bin/env python3
"""
Podcast RSS Feed Processor CLI
A tool for ingesting, cleaning, and tagging podcast RSS feeds.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Import handlers at module level
from src.modules.ingest import handle_ingest
from src.modules.clean import handle_clean
from src.modules.tag import handle_tag
from src.modules.export import handle_export
from src.modules.validate import handle_validate

# Load environment variables
load_dotenv()


def setup_logging():
    """Configure logging to both file and console."""
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    log_level = os.getenv('LOG_LEVEL', 'INFO')

    # Create logs directory if it doesn't exist
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def create_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='Process podcast RSS feeds: ingest, clean, tag, and export episode data.')

    # Global flags
    parser.add_argument(
        '--prod',
        action='store_true',
        help='Run in production mode (default: test mode)'
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        dest='command', help='Available commands')

    # Ingest command
    ingest_parser = subparsers.add_parser(
        'ingest', help='Ingest episodes from RSS feed')
    ingest_parser.add_argument('--feed', help='RSS feed URL (overrides .env)')
    ingest_parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset the database before ingesting (removes existing database file)'
    )

    # Clean command
    clean_parser = subparsers.add_parser(
        'clean', help='Clean episode descriptions')
    clean_parser.add_argument(
        '--all',
        action='store_true',
        help='Clean all uncleaned episodes')
    clean_parser.add_argument(
        '--id',
        type=int,
        help='Clean specific episode by ID')

    # Tag command
    tag_parser = subparsers.add_parser('tag', help='Tag episodes')
    tag_parser.add_argument(
        '--all',
        action='store_true',
        help='Tag all untagged episodes')
    tag_parser.add_argument(
        '--id',
        type=int,
        help='Tag specific episode by ID')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export episode data')
    export_parser.add_argument(
        '--format',
        choices=['json', 'csv'],
        default='json',
        help='Export format (default: json)'
    )
    export_parser.add_argument('--output', help='Output file path')
    export_parser.add_argument(
        '--limit',
        type=int,
        help='Limit the number of episodes to export (ordered by most recent first)'
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        'validate', help='Validate episode tags')
    validate_parser.add_argument('--report', help='Path for validation report')

    return parser


def main():
    """Main entry point for the CLI application."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # Set environment mode
    os.environ['ENV_MODE'] = 'prod' if args.prod else 'test'
    logger.info("Running in %s mode", os.getenv('ENV_MODE'))

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'ingest':
            handle_ingest(args)
        elif args.command == 'clean':
            handle_clean(args)
        elif args.command == 'tag':
            handle_tag(args)
        elif args.command == 'export':
            handle_export(args)
        elif args.command == 'validate':
            handle_validate(args)
    except Exception as e:
        logger.error("Error executing command %s: %s", args.command, str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
