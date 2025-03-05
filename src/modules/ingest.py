"""
Module for ingesting podcast RSS feeds and storing episodes in the database.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

import requests
from lxml import etree

from .database import Database

logger = logging.getLogger(__name__)


class RSSFeedIngestor:
    """Handles the ingestion of podcast RSS feeds."""

    def __init__(self, feed_url: Optional[str] = None):
        """Initialize the ingestor with an optional feed URL."""
        self.feed_url = feed_url or os.getenv('RSS_FEED_URL')
        if not self.feed_url:
            raise ValueError(
                "RSS feed URL not provided and not found in environment variables")

    def fetch_feed(self) -> bytes:
        """Fetch the RSS feed content."""
        try:
            response = requests.get(self.feed_url, timeout=30)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Error fetching RSS feed: {str(e)}")
            raise

    def parse_duration(self, duration_str: Optional[str]) -> Optional[str]:
        """Parse and normalize episode duration."""
        if not duration_str:
            return None

        try:
            # Handle HH:MM:SS format
            if ':' in duration_str:
                parts = duration_str.split(':')
                if len(parts) == 3:
                    hours, minutes, seconds = map(int, parts)
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                elif len(parts) == 2:
                    minutes, seconds = map(int, parts)
                    return f"00:{minutes:02d}:{seconds:02d}"

            # Handle seconds format
            seconds = int(duration_str)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        except (ValueError, TypeError):
            logger.warning(f"Could not parse duration: {duration_str}")
            return duration_str

    def extract_episode_number(self, title: str) -> Optional[int]:
        """Extract episode number from title if present."""
        import re

        # Common patterns for episode numbers
        patterns = [
            r'#(\d+)',            # Matches "#123"
            r'Episode (\d+)',     # Matches "Episode 123"
            r'Ep\.? (\d+)',       # Matches "Ep. 123" or "Ep 123"
            r'E(\d+)',            # Matches "E123"
        ]

        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def parse_feed(self, content: bytes) -> List[Dict[str, Union[str, int]]]:
        """Parse the RSS feed content and extract episode data."""
        try:
            # Parse XML content
            parser = etree.XMLParser(recover=True)
            root = etree.fromstring(content, parser=parser)

            # Define XML namespaces
            namespaces = {
                'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
                'content': 'http://purl.org/rss/1.0/modules/content/'
            }

            episodes = []

            # Process each item (episode)
            for item in root.findall('.//item'):
                try:
                    # Extract basic episode data
                    title = item.findtext('title', '').strip()
                    guid = item.findtext('guid', '').strip()

                    if not title or not guid:
                        logger.warning(
                            "Skipping episode with missing title or GUID")
                        continue

                    # Extract other fields
                    description = item.findtext('description', '').strip()
                    link = item.findtext('link', '').strip()
                    pub_date_str = item.findtext('pubDate', '').strip()

                    # Parse publication date
                    try:
                        pub_date = datetime.strptime(
                            pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                        pub_date_iso = pub_date.isoformat()
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Could not parse publication date: {pub_date_str}")
                        pub_date_iso = None

                    # Extract audio URL from enclosure
                    audio_url = None
                    enclosure = item.find('enclosure')
                    if enclosure is not None:
                        audio_url = enclosure.get('url', '').strip()

                    # Extract duration
                    duration = item.findtext('duration') or item.findtext(
                        'itunes:duration', '', namespaces)
                    duration = self.parse_duration(duration)

                    # Extract episode number from title
                    episode_number = self.extract_episode_number(title)

                    episode = {
                        'guid': guid,
                        'title': title,
                        'description': description,
                        'link': link,
                        'published_date': pub_date_iso,
                        'duration': duration,
                        'audio_url': audio_url,
                        'episode_number': episode_number,
                        'cleaning_status': 'pending'
                    }

                    episodes.append(episode)

                except Exception as e:
                    logger.error(f"Error processing episode: {str(e)}")
                    continue

            return episodes

        except etree.XMLSyntaxError as e:
            logger.error(f"Error parsing RSS feed XML: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing RSS feed: {str(e)}")
            raise

    def ingest(self) -> tuple[int, int]:
        """
        Ingest episodes from the RSS feed into the database.
        Returns a tuple of (new_episodes_count, duplicate_count).
        """
        try:
            # Fetch and parse feed
            content = self.fetch_feed()
            episodes = self.parse_feed(content)

            new_count = 0
            duplicate_count = 0

            # Store episodes in database
            with Database() as db:
                for episode in episodes:
                    episode_id = db.insert_episode(episode)
                    if episode_id:
                        new_count += 1
                    else:
                        duplicate_count += 1

            logger.info(
                f"Ingestion complete. New episodes: {new_count}, "
                f"Duplicates: {duplicate_count}"
            )
            return new_count, duplicate_count

        except Exception as e:
            logger.error(f"Error during ingestion: {str(e)}")
            raise


def handle_ingest(args):
    """Handle the ingest command from the CLI."""
    try:
        # Get feed URL from args or environment
        feed_url = args.feed or os.getenv('RSS_FEED_URL')
        if not feed_url:
            raise ValueError("No RSS feed URL provided in args or environment")

        # Reset database if requested
        if args.reset:
            db_path = 'data/episodes.db' if os.getenv('ENV_MODE') == 'prod' else 'data/test_episodes.db'
            try:
                os.remove(db_path)
                logger.info(f"Reset: Removed existing database at {db_path}")
            except FileNotFoundError:
                logger.info(f"Reset: No existing database found at {db_path}")

        # Perform ingestion
        ingestor = RSSFeedIngestor(feed_url)
        new_count, duplicate_count = ingestor.ingest()
        logger.info("Feed ingestion completed successfully")

    except Exception as e:
        logger.error(f"Failed to execute ingest command: {str(e)}")
        raise
