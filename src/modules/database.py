"""
Database module for managing SQLite operations.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for podcast episodes."""

    def __init__(self):
        """Initialize database connection based on environment."""
        self.env_mode = os.getenv('ENV_MODE', 'test')
        db_path = os.getenv(
            'DB_PATH_PROD' if self.env_mode == 'prod' else 'DB_PATH_TEST')

        if not db_path:
            raise ValueError(
                "Database path not configured in environment variables")

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

            # Enable foreign keys and JSON support
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")

            # Register timestamp converter
            sqlite3.register_adapter(
                datetime, lambda dt: dt.astimezone(
                    timezone.utc).isoformat())
            sqlite3.register_converter(
                "timestamp",
                lambda x: datetime.fromisoformat(
                    x.decode()))

            self._create_tables()
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        try:
            # Episodes table with updated schema
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guid TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    cleaned_description TEXT,
                    link TEXT,
                    published_date TIMESTAMP,
                    duration TEXT,
                    audio_url TEXT,
                    cleaning_timestamp TIMESTAMP,
                    cleaning_status TEXT DEFAULT 'pending',
                    format_tags TEXT,
                    theme_tags TEXT,
                    track_tags TEXT,
                    episode_number INTEGER,
                    tags TEXT,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                    updated_at TIMESTAMP DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
                )
            """)

            # Create indexes for performance
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_guid ON episodes(guid)")
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_published_date ON episodes(published_date)")
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_cleaning_status ON episodes(cleaning_status)")
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_episode_number ON episodes(episode_number)")
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_status ON episodes(status)")

            # Create trigger to update the updated_at timestamp
            self.cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS episodes_updated_at
                AFTER UPDATE ON episodes
                BEGIN
                    UPDATE episodes SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                    WHERE id = NEW.id;
                END;
            """)

            self.conn.commit()
            logger.info(
                "Database tables, indexes, and triggers created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise

    def insert_episode(
            self, episode_data: Dict[str, Union[str, int, dict]]) -> Optional[int]:
        """
        Insert a new episode into the database.
        Returns the ID of the inserted episode or None if it's a duplicate.
        """
        try:
            # Check for duplicate
            self.cursor.execute(
                "SELECT id FROM episodes WHERE guid = ?",
                (episode_data['guid'],)
            )
            if self.cursor.fetchone():
                logger.info(
                    f"Duplicate episode found with GUID: {
                        episode_data['guid']}")
                return None

            # Convert tags dict to JSON string if present
            if 'tags' in episode_data and isinstance(
                    episode_data['tags'], dict):
                episode_data['tags'] = json.dumps(episode_data['tags'])

            # Prepare the insert query
            columns = ', '.join(episode_data.keys())
            placeholders = ', '.join(['?' for _ in episode_data])
            query = f"INSERT INTO episodes ({columns}) VALUES ({placeholders})"

            # Execute insert
            self.cursor.execute(query, list(episode_data.values()))
            self.conn.commit()

            episode_id = self.cursor.lastrowid
            logger.info(f"Successfully inserted episode with ID: {episode_id}")
            return episode_id

        except sqlite3.Error as e:
            logger.error(f"Error inserting episode: {str(e)}")
            self.conn.rollback()
            raise

    def update_episode(self, episode_id: int,
                       update_data: Dict[str, Union[str, int, dict]]) -> bool:
        """
        Update an existing episode in the database.
        Returns True if successful, False otherwise.
        """
        try:
            # Convert tags dict to JSON string if present
            if 'tags' in update_data and isinstance(update_data['tags'], dict):
                update_data['tags'] = json.dumps(update_data['tags'])

            set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
            query = f"UPDATE episodes SET {set_clause} WHERE id = ?"

            values = list(update_data.values()) + [episode_id]
            self.cursor.execute(query, values)
            self.conn.commit()

            success = self.cursor.rowcount > 0
            if success:
                logger.info(
                    f"Successfully updated episode with ID: {episode_id}")
            else:
                logger.warning(f"No episode found with ID: {episode_id}")
            return success

        except sqlite3.Error as e:
            logger.error(f"Error updating episode: {str(e)}")
            self.conn.rollback()
            raise

    def get_episode(self, episode_id: int) -> Optional[Dict]:
        """Retrieve a single episode by ID."""
        try:
            self.cursor.execute(
                "SELECT * FROM episodes WHERE id = ?", (episode_id,))
            row = self.cursor.fetchone()
            if row:
                result = dict(row)
                # Parse JSON tags if present
                if result.get('tags'):
                    result['tags'] = json.loads(result['tags'])
                return result
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving episode: {str(e)}")
            raise

    def get_episodes_by_status(self, status: str) -> List[Dict]:
        """Retrieve all episodes with a specific cleaning status."""
        try:
            self.cursor.execute(
                "SELECT * FROM episodes WHERE cleaning_status = ? ORDER BY published_date DESC",
                (status,)
            )
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving episodes by status: {str(e)}")
            raise

    def get_all_episodes(self) -> List[Dict]:
        """Retrieve all episodes ordered by published date."""
        try:
            self.cursor.execute(
                "SELECT * FROM episodes ORDER BY published_date DESC"
            )
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all episodes: {str(e)}")
            raise

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
