"""
Module for automated tagging of podcast episodes using OpenAI.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from openai import OpenAI

from .database import Database
from ..constants.taxonomy import FORMAT_TAGS, THEME_TAGS, TRACK_TAGS, validate_tags

logger = logging.getLogger(__name__)


class EpisodeTagger:
    """Handles automated tagging of podcast episodes."""

    def __init__(self):
        """Initialize the episode tagger."""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

        if not self.openai_api_key:
            raise ValueError(
                "OpenAI API key not found in environment variables")

        self.client = OpenAI(api_key=self.openai_api_key)

    def generate_tags(self,
                      title: str,
                      description: str) -> Tuple[List[str],
                                                 List[str],
                                                 List[str]]:
        """
        Generate format, theme, and track tags using OpenAI.
        Returns tuple of (format_tags, theme_tags, track_tags).
        """
        try:
            # Prepare available tags for the prompt
            format_options = '\n'.join(
                [f"- {tag}: {desc}" for tag, desc in FORMAT_TAGS.items()])
            theme_options = '\n'.join(
                [f"- {tag}: {desc}" for tag, desc in THEME_TAGS.items()])
            track_options = '\n'.join(
                [f"- {tag}: {desc}" for tag, desc in TRACK_TAGS.items()])

            prompt = f"""
            Analyze this podcast episode and assign appropriate tags from each category.

            Episode Title: {title}
            Episode Description: {description}

            Available Format Tags (choose 1-2):
            {format_options}

            Available Theme Tags (choose 1-3):
            {theme_options}

            Available Track Tags (choose 1):
            {track_options}

            Return your response as a JSON object with three arrays: format_tags, theme_tags, and track_tags.
            Only use tags from the provided lists. Do not make up new tags.
            Example response format:
            {{
                "format_tags": ["INTERVIEW"],
                "theme_tags": ["TECHNOLOGY", "BUSINESS"],
                "track_tags": ["MAIN_SERIES"]
            }}
            """

            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a podcast episode tagging assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            # Parse the response
            tags = json.loads(response.choices[0].message.content)

            # Validate tags
            format_tags = tags.get('format_tags', [])
            theme_tags = tags.get('theme_tags', [])
            track_tags = tags.get('track_tags', [])

            invalid_tags = validate_tags(format_tags, theme_tags, track_tags)
            if invalid_tags:
                logger.warning(f"Invalid tags detected: {invalid_tags}")
                # Remove invalid tags but keep valid ones
                format_tags = [tag for tag in format_tags if tag in FORMAT_TAGS]
                theme_tags = [tag for tag in theme_tags if tag in THEME_TAGS]
                track_tags = [tag for tag in track_tags if tag in TRACK_TAGS]

                # Only use defaults if no valid tags remain
                if not format_tags:
                    format_tags = ['MONOLOGUE']  # Default format
                if not theme_tags:
                    theme_tags = ['GENERAL']  # Default theme
                if not track_tags:
                    track_tags = ['MAIN_SERIES']  # Default track

            return format_tags, theme_tags, track_tags

        except Exception as e:
            logger.error(f"Error generating tags: {str(e)}")
            return ['MONOLOGUE'], ['GENERAL'], ['MAIN_SERIES']

    def tag_episode(self, episode_id: int) -> bool:
        """
        Tag a specific episode.
        Returns True if tagging was successful.
        """
        try:
            with Database() as db:
                # Get episode
                episode = db.get_episode(episode_id)
                if not episode:
                    logger.warning(f"Episode not found: {episode_id}")
                    return False

                # Use cleaned description if available, otherwise use original
                description = episode['cleaned_description'] or episode['description']
                if not description:
                    logger.warning(
                        f"Episode {episode_id} has no description for tagging")
                    return False

                # Generate tags
                format_tags, theme_tags, track_tags = self.generate_tags(
                    episode['title'],
                    description
                )

                # Update database
                update_data = {
                    'format_tags': ','.join(format_tags),
                    'theme_tags': ','.join(theme_tags),
                    'track_tags': ','.join(track_tags),
                    'updated_at': datetime.utcnow().isoformat()
                }

                success = db.update_episode(episode_id, update_data)

                if success:
                    logger.info(
                        f"Successfully tagged episode {episode_id} with "
                        f"format: {format_tags}, "
                        f"theme: {theme_tags}, "
                        f"track: {track_tags}"
                    )
                else:
                    logger.error(
                        f"Failed to update episode {episode_id} with tags")

                return success

        except Exception as e:
            logger.error(f"Error tagging episode {episode_id}: {str(e)}")
            return False

    def tag_all_untagged(self) -> Tuple[int, int]:
        """
        Tag all episodes that don't have tags.
        Returns tuple of (success_count, failure_count).
        """
        try:
            success_count = 0
            failure_count = 0

            with Database() as db:
                # Get all episodes
                episodes = db.get_all_episodes()

                for episode in episodes:
                    # Check if episode needs tagging
                    if not any([
                        episode['format_tags'],
                        episode['theme_tags'],
                        episode['track_tags']
                    ]):
                        if self.tag_episode(episode['id']):
                            success_count += 1
                        else:
                            failure_count += 1

            logger.info(
                f"Batch tagging complete. "
                f"Successes: {success_count}, "
                f"Failures: {failure_count}"
            )
            return success_count, failure_count

        except Exception as e:
            logger.error(f"Error in batch tagging: {str(e)}")
            raise


def handle_tag(args):
    """Handle the tag command from the CLI."""
    try:
        tagger = EpisodeTagger()

        if hasattr(args, 'id') and args.id is not None:
            # Tag specific episode
            success = tagger.tag_episode(args.id)
            if success:
                logger.info(f"Successfully tagged episode {args.id}")
            else:
                logger.error(f"Failed to tag episode {args.id}")

        elif hasattr(args, 'all') and args.all:
            # Tag all untagged episodes
            success_count, failure_count = tagger.tag_all_untagged()
            logger.info(
                f"Batch tagging completed. "
                f"Successfully tagged {success_count} episodes. "
                f"Failed to tag {failure_count} episodes."
            )

        else:
            logger.error(
                "No valid tagging option specified (--id or --all required)")

    except Exception as e:
        logger.error(f"Failed to execute tag command: {str(e)}")
        raise
