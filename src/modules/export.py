"""
Module for exporting podcast episode data to various formats.
"""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from .database import Database

logger = logging.getLogger(__name__)


class DataExporter:
    """Handles exporting of podcast episode data."""

    def __init__(self):
        """Initialize the data exporter."""
        self.env_mode = os.getenv('ENV_MODE', 'test')

    def _prepare_episode_data(self, episode: Dict) -> Dict:
        """Prepare episode data for export by converting to appropriate types."""
        # Convert comma-separated tags to lists, handling missing fields
        format_tags = episode.get('format_tags', '').split(',') if episode.get('format_tags') else []
        theme_tags = episode.get('theme_tags', '').split(',') if episode.get('theme_tags') else []
        track_tags = episode.get('track_tags', '').split(',') if episode.get('track_tags') else []

        return {
            'id': episode.get('id'),
            'guid': episode.get('guid'),
            'title': episode.get('title'),
            'description': episode.get('description'),
            'cleaned_description': episode.get('cleaned_description'),
            'link': episode.get('link'),
            'published_date': episode.get('published_date'),
            'duration': episode.get('duration'),
            'audio_url': episode.get('audio_url'),
            'episode_number': episode.get('episode_number'),
            'format_tags': format_tags,
            'theme_tags': theme_tags,
            'track_tags': track_tags,
            'cleaning_status': episode.get('cleaning_status'),
            'cleaning_timestamp': episode.get('cleaning_timestamp'),
            'created_at': episode.get('created_at'),
            'updated_at': episode.get('updated_at')
        }

    def export_to_json(self,
                       episodes: List[Dict],
                       output_path: Optional[str] = None) -> Union[bool,
                                                                   str]:
        """
        Export episodes to JSON format.
        If output_path is None, returns the JSON string.
        If output_path is provided, returns True on success.
        """
        try:
            # Prepare data
            export_data = [self._prepare_episode_data(
                episode) for episode in episodes]

            # Generate JSON
            json_data = json.dumps(
                export_data,
                indent=2,
                ensure_ascii=False
            )

            if output_path:
                # Ensure directory exists
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                # Write to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                logger.info(
                    f"Successfully exported {
                        len(episodes)} episodes to {output_path}")
                return True

            return json_data

        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            raise

    def export_to_csv(self, episodes: List[Dict], output_path: str) -> bool:
        """Export episodes to CSV format."""
        try:
            # Prepare data
            export_data = [self._prepare_episode_data(
                episode) for episode in episodes]

            # Define CSV fields
            fieldnames = [
                'id',
                'guid',
                'title',
                'description',
                'cleaned_description',
                'link',
                'published_date',
                'duration',
                'audio_url',
                'episode_number',
                'format_tags',
                'theme_tags',
                'track_tags',
                'cleaning_status',
                'cleaning_timestamp',
                'created_at',
                'updated_at']

            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Write to CSV
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                if not export_data:
                    logger.warning("No episodes to export")
                else:
                    for episode in export_data:
                        # Convert lists to JSON strings for CSV
                        episode_copy = episode.copy()
                        for field in [
                                'format_tags', 'theme_tags', 'track_tags']:
                            episode_copy[field] = json.dumps(
                                episode_copy[field])
                        writer.writerow(episode_copy)

            logger.info(
                f"Successfully exported {
                    len(episodes)} episodes to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise

    def export(self, output_path: str, format: str = "json", limit: Optional[int] = None) -> bool:
        """
        Export episodes to the specified format.

        Args:
            output_path: Path to save the exported file
            format: Export format ("json" or "csv")
            limit: Optional limit on number of episodes to export (ordered by most recent first)

        Returns:
            bool: True if export was successful

        Raises:
            ValueError: If format is invalid
        """
        try:
            # Get episodes from database
            with Database() as db:
                episodes = db.get_all_episodes()
                
            # Sort by published date (most recent first) and apply limit if specified
            episodes.sort(key=lambda x: x.get('published_date') or '', reverse=True)
            if limit is not None:
                episodes = episodes[:limit]

            # Export based on format
            if format.lower() == "json":
                return self.export_to_json(episodes, output_path)
            elif format.lower() == "csv":
                return self.export_to_csv(episodes, output_path)
            else:
                raise ValueError(f"Invalid export format: {format}")

        except Exception as e:
            logger.error(f"Error during export: {str(e)}")
            raise


def handle_export(args):
    """Handle the export command from the CLI."""
    try:
        exporter = DataExporter()

        # Determine output path
        output_path = args.output
        if not output_path:
            # Generate default output path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"podcast_episodes_{timestamp}.{args.format}"
            output_path = os.path.join('data', 'exports', filename)

        # Perform export
        exporter.export(output_path=output_path, format=args.format, limit=args.limit)
        logger.info(f"Export completed successfully to {output_path}")

    except Exception as e:
        logger.error(f"Failed to execute export command: {str(e)}")
        raise
