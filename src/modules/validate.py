"""
Module for validating podcast episode tags against the defined taxonomy.
"""

import json
import logging
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional, Set

from .database import Database
from ..constants.taxonomy import FORMAT_TAGS, THEME_TAGS, TRACK_TAGS, validate_tags

logger = logging.getLogger(__name__)


class TagValidator:
    """Handles validation of podcast episode tags."""

    def __init__(self, db=None):
        """Initialize the tag validator."""
        self.env_mode = os.getenv('ENV_MODE', 'test')
        self.db = db
        self._should_cleanup_db = False

    def __enter__(self):
        """Context manager entry."""
        if self.db is None:
            self.db = Database().__enter__()
            self._should_cleanup_db = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._should_cleanup_db and self.db:
            self.db.__exit__(exc_type, exc_val, exc_tb)
            self.db = None

    def get_tag_sets(
            self, episode: Dict) -> tuple[Set[str], Set[str], Set[str]]:
        """Extract tag sets from an episode."""
        format_tags = set(episode['format_tags'].split(
            ',')) if episode['format_tags'] else set()
        theme_tags = set(episode['theme_tags'].split(
            ',')) if episode['theme_tags'] else set()
        track_tags = set(episode['track_tags'].split(
            ',')) if episode['track_tags'] else set()
        return format_tags, theme_tags, track_tags

    def validate_episode(self, episode_id: int) -> bool:
        """
        Validate tags for a single episode.
        Returns True if validation was successful.
        """
        try:
            if not self.db:
                with Database() as db:
                    return self._validate_episode_impl(episode_id, db)
            return self._validate_episode_impl(episode_id, self.db)
        except Exception as e:
            logger.error(f"Error validating episode {episode_id}: {str(e)}")
            return False

    def _validate_episode_impl(self, episode_id: int, db) -> bool:
        """Internal implementation of episode validation."""
        episode = db.get_episode(episode_id)
        if not episode:
            logger.warning(f"Episode not found: {episode_id}")
            return False

        format_tags, theme_tags, track_tags = self.get_tag_sets(episode)

        # Check for invalid tags
        invalid_tags = validate_tags(
            list(format_tags),
            list(theme_tags),
            list(track_tags))

        # Check for missing required tags
        missing_tags = {
            'format': not bool(format_tags),
            'theme': not bool(theme_tags),
            'track': not bool(track_tags)
        }

        # Only check format tag count constraint
        tag_count_issues = {
            'format': len(format_tags) > 2,  # Max 2 format tags
            'theme': False,  # No limit on theme tags
            'track': False   # No limit on track tags
        }

        has_issues = bool(
            invalid_tags or any(
                missing_tags.values()) or any(
                tag_count_issues.values()))

        if has_issues:
            logger.warning(
                f"Validation issues found for episode {episode_id}: "
                f"invalid_tags={invalid_tags}, "
                f"missing_tags={missing_tags}, "
                f"tag_count_issues={tag_count_issues}"
            )
            db.update_episode(episode_id, {'status': 'validation_failed'})
            return False

        db.update_episode(episode_id, {'status': 'validated'})
        return True

    def validate_all(self) -> List[Dict]:
        """
        Validate tags for all episodes.
        Returns a list of validation results.
        """
        try:
            if not self.db:
                with Database() as db:
                    return self._validate_all_impl(db)
            return self._validate_all_impl(self.db)
        except Exception as e:
            logger.error(f"Error validating episodes: {str(e)}")
            raise

    def _validate_all_impl(self, db) -> List[Dict]:
        """Internal implementation of validate_all."""
        results = []
        episodes = db.get_all_episodes()

        for episode in episodes:
            result = self.validate_episode(episode['id'])  # Use public method for mockability
            if not result:
                results.append({
                    'episode_id': episode['id'],
                    'title': episode['title'],
                    'has_issues': True
                })

        return results

    def validate_all_pending(self) -> List[Dict]:
        """
        Validate all episodes with 'tagged' status.
        Returns a list of validation results.
        """
        try:
            if not self.db:
                with Database() as db:
                    return self._validate_all_pending_impl(db)
            return self._validate_all_pending_impl(self.db)
        except Exception as e:
            logger.error(f"Error validating pending episodes: {str(e)}")
            raise

    def _validate_all_pending_impl(self, db) -> List[Dict]:
        """Internal implementation of validate_all_pending."""
        results = []
        episodes = db.get_episodes_by_status('tagged')

        for episode in episodes:
            if episode['status'] == 'tagged':  # Only validate episodes with 'tagged' status
                result = self.validate_episode(episode['id'])  # Use public method for mockability
                if not result:
                    results.append({
                        'episode_id': episode['id'],
                        'title': episode.get('title', 'Unknown'),
                        'has_issues': True
                    })

        return results

    def generate_report(
            self,
            results: List[Dict],
            output_path: Optional[str] = None) -> str:
        """
        Generate a validation report.
        If output_path is None, returns the report as a string.
        """
        try:
            # Prepare report data
            report = {
                'timestamp': datetime.now(UTC).isoformat(),
                'environment': self.env_mode,
                'total_issues': len(results),
                'results': results
            }

            # Generate JSON report
            report_json = json.dumps(report, indent=2, ensure_ascii=False)

            if output_path:
                # Ensure directory exists
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                # Write report to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report_json)
                logger.info(f"Validation report written to {output_path}")

            return report_json

        except Exception as e:
            logger.error(f"Error generating validation report: {str(e)}")
            raise


def handle_validate(args):
    """Handle the validate command from the CLI."""
    try:
        validator = TagValidator()
        with validator:
            results = validator.validate_all()

            # Determine report path
            report_path = args.report if hasattr(args, 'report') else None
            if not report_path:
                # Generate default report path
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"validation_report_{timestamp}.json"
                report_path = os.path.join('data', 'reports', filename)

            # Generate and save report
            validator.generate_report(results, report_path)

            # Log summary
            if results:
                logger.warning(
                    f"Found {len(results)} episodes with tag issues. "
                    f"See {report_path} for details."
                )
            else:
                logger.info("No tag issues found.")

    except Exception as e:
        logger.error(f"Failed to execute validate command: {str(e)}")
        raise
