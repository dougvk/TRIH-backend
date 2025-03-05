"""
Module for automated tagging of podcast episodes using OpenAI.
"""

import json
import logging
import os
import re
from datetime import datetime, UTC
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
                                                 List[str],
                                                 Optional[int]]:
        """
        Generate format, theme, and track tags using OpenAI.
        Returns tuple of (format_tags, theme_tags, track_tags, episode_number).
        """
        try:
            # Prepare taxonomy text
            format_options = '\n'.join(
                [f"- {tag}: {desc}" for tag, desc in FORMAT_TAGS.items()])
            theme_options = '\n'.join(
                [f"- {tag}: {desc}" for tag, desc in THEME_TAGS.items()])
            track_options = '\n'.join(
                [f"- {tag}: {desc}" for tag, desc in TRACK_TAGS.items()])

            taxonomy_text = f"""Available Tags:

FORMAT TAGS:
{format_options}

THEME TAGS:
{theme_options}

TRACK TAGS:
{track_options}"""

            prompt = f"""You are a history podcast episode tagger. Your task is to analyze this episode and assign ALL relevant tags from the taxonomy below.

Episode Title: {title}
Episode Description: {description}

IMPORTANT RULES:
1. An episode MUST be tagged as "Series Episodes" if ANY of these are true:
   - The title contains "(Ep X)" or "(Part X)" where X is any number
   - The title contains "Part" followed by a number
   - The episode is part of a named series (e.g. "Young Churchill", "The French Revolution")
2. An episode MUST be tagged as "RIHC Series" if the title starts with "RIHC:"
   - RIHC episodes should ALWAYS have both "RIHC Series" and "Series Episodes" in their Format tags
3. An episode can and should have multiple tags from each category if applicable
4. If none of the above rules apply, tag it as "Standalone Episodes"
5. For series episodes, you MUST extract the episode number:
   - Look for patterns like "(Ep X)", "(Part X)", "Part X", where X is a number
   - Include the number in your response as "episode_number"
   - If no explicit number is found, use null for episode_number

{taxonomy_text}

IMPORTANT:
1. You MUST ONLY use tags EXACTLY as they appear in the taxonomy above
2. You MUST include Format, Theme, Track, and episode_number in your response
3. Make sure themes and tracks are from their correct categories (don't use track names as themes)
4. For Theme and Track:
   - Apply ALL relevant themes and tracks that match the content
   - It's common for an episode to have 2-3 themes and 2-3 tracks
   - Make sure themes and tracks are from their correct categories (don't use track names as themes)

Example responses:

For a RIHC episode about ancient Rome and military history:
{{"Format": ["RIHC Series", "Series Episodes"], "Theme": ["Ancient & Classical Civilizations", "Military History & Battles"], "Track": ["Roman Track", "Military & Battles Track", "The RIHC Bonus Track"], "episode_number": null}}

For a standalone episode about British history:
{{"Format": ["Standalone Episodes"], "Theme": ["Regional & National Histories", "Modern Political History & Leadership"], "Track": ["British History Track", "Modern Political History Track"], "episode_number": null}}

For part 3 of a series about Napoleon:
{{"Format": ["Series Episodes"], "Theme": ["Modern Political History & Leadership", "Military History & Battles"], "Track": ["Modern Political History Track", "Military & Battles Track", "Historical Figures Track"], "episode_number": 3}}

Return tags in this exact JSON format:
{{"Format": ["tag1", "tag2"], "Theme": ["tag1", "tag2"], "Track": ["tag1", "tag2"], "episode_number": number_or_null}}
"""

            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a history podcast episode tagging assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            # Parse the response
            tags = json.loads(response.choices[0].message.content)

            # Extract tags and episode number
            format_tags = tags.get('Format', [])
            theme_tags = tags.get('Theme', [])
            track_tags = tags.get('Track', [])
            episode_number = tags.get('episode_number')

            invalid_tags = validate_tags(format_tags, theme_tags, track_tags)
            if invalid_tags:
                logger.warning(f"Invalid tags detected: {invalid_tags}")
                # Remove invalid tags but keep valid ones
                format_tags = [tag for tag in format_tags if tag in FORMAT_TAGS]
                theme_tags = [tag for tag in theme_tags if tag in THEME_TAGS]
                track_tags = [tag for tag in track_tags if tag in TRACK_TAGS]

                # Only use defaults if no valid tags remain
                if not format_tags:
                    format_tags = ['Standalone Episodes']  # Default format
                if not theme_tags:
                    theme_tags = ['General History']  # Default theme
                if not track_tags:
                    track_tags = ['General History Track']  # Default track

            return format_tags, theme_tags, track_tags, episode_number

        except Exception as e:
            logger.error(f"Error generating tags: {str(e)}")
            return ['Standalone Episodes'], ['General History'], ['General History Track'], None

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
                format_tags, theme_tags, track_tags, episode_number = self.generate_tags(
                    episode['title'],
                    description
                )

                # Update database
                update_data = {
                    'format_tags': ','.join(format_tags),
                    'theme_tags': ','.join(theme_tags),
                    'track_tags': ','.join(track_tags),
                    'episode_number': episode_number,
                    'updated_at': datetime.now(UTC).isoformat(),
                    'status': 'tagged'  # Update status to tagged
                }

                success = db.update_episode(episode_id, update_data)

                if success:
                    logger.info(
                        f"Successfully tagged episode {episode_id} with "
                        f"format: {format_tags}, "
                        f"theme: {theme_tags}, "
                        f"track: {track_tags}, "
                        f"episode_number: {episode_number}"
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
