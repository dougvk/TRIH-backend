import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from datetime import datetime
import os
import json
from pathlib import Path
from src.modules.database import Database

@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database path."""
    db_file = tmp_path / "test.db"
    return str(db_file)

@pytest.fixture
def sample_episode():
    """Return a sample episode for testing."""
    return {
        'guid': 'test-guid-123',
        'title': 'Test Episode',
        'description': 'Test description',
        'link': 'https://example.com/episode1',
        'published_date': datetime.utcnow().isoformat(),
        'duration': '00:30:00',
        'audio_url': 'https://example.com/episode1.mp3'
    }

def test_database_init_test_mode(test_db_path):
    """Test database initialization in test mode."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        db = Database()
        assert db.env_mode == 'test'
        assert db.db_path == test_db_path

def test_database_init_prod_mode(test_db_path):
    """Test database initialization in production mode."""
    with patch.dict(os.environ, {'ENV_MODE': 'prod', 'DB_PATH_PROD': test_db_path}):
        db = Database()
        assert db.env_mode == 'prod'
        assert db.db_path == test_db_path

def test_database_init_missing_path():
    """Test database initialization with missing path."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            Database()
        assert str(exc_info.value) == "Database path not configured in environment variables"

def test_database_connection_error(test_db_path):
    """Test database connection error handling."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with patch.object(Path, 'mkdir', side_effect=OSError("Test error")):
            with pytest.raises((sqlite3.Error, OSError)):
                db = Database()
                db.connect()

def test_table_creation(test_db_path):
    """Test database table and index creation."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            # Check if tables exist
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='episodes'")
            assert db.cursor.fetchone() is not None

            # Check if indexes exist
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_guid'")
            assert db.cursor.fetchone() is not None
            db.cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_published_date'")
            assert db.cursor.fetchone() is not None

def test_json_tag_handling(test_db_path):
    """Test JSON tag handling in insert and update operations."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            # Test insert with JSON tags
            episode_data = {
                'guid': 'test-guid-json',
                'title': 'Test JSON Tags',
                'tags': {'format': ['INTERVIEW'], 'theme': ['TECHNOLOGY']}
            }
            episode_id = db.insert_episode(episode_data)
            assert episode_id is not None

            # Verify JSON was stored correctly
            retrieved = db.get_episode(episode_id)
            assert isinstance(retrieved['tags'], dict)
            assert retrieved['tags']['format'] == ['INTERVIEW']

            # Test update with JSON tags
            update_data = {
                'tags': {'format': ['PANEL'], 'theme': ['BUSINESS']}
            }
            assert db.update_episode(episode_id, update_data)

            # Verify updated JSON
            retrieved = db.get_episode(episode_id)
            assert retrieved['tags']['format'] == ['PANEL']

def test_insert_error_handling(test_db_path):
    """Test error handling during episode insertion."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            # Test with invalid data type
            with pytest.raises(sqlite3.Error):
                db.insert_episode({'guid': 123, 'title': ['invalid']})

def test_update_error_handling(test_db_path):
    """Test error handling during episode update."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            # Insert a test episode
            episode_id = db.insert_episode({
                'guid': 'test-guid-update-error',
                'title': 'Test Update Error'
            })

            # Test with invalid data type
            with pytest.raises(sqlite3.Error):
                db.update_episode(episode_id, {'title': ['invalid']})

def test_get_episode_error_handling(test_db_path):
    """Test error handling in get_episode."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            # Close the connection to force an error
            db.conn.close()
            with pytest.raises(sqlite3.Error):
                db.get_episode(1)

def test_get_episodes_by_status_error_handling(test_db_path):
    """Test error handling in get_episodes_by_status."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            # Test with invalid status type
            with pytest.raises(sqlite3.Error):
                db.get_episodes_by_status(['invalid'])

def test_get_all_episodes_error_handling(test_db_path):
    """Test error handling in get_all_episodes."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        db = Database()
        db.connect()
        # Corrupt the database connection
        db.cursor.close()
        with pytest.raises(sqlite3.Error):
            db.get_all_episodes()
        db.disconnect()

def test_context_manager(test_db_path):
    """Test database context manager functionality."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            assert db.conn is not None
            assert db.cursor is not None
            # Test database operations work
            db.cursor.execute("SELECT 1")
            assert db.cursor.fetchone()[0] == 1

        # Verify connection is closed after context
        assert db.conn is None
        assert db.cursor is None

def test_context_manager_error_handling(test_db_path):
    """Test context manager error handling."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        try:
            with Database() as db:
                raise Exception("Test error")
        except Exception as e:
            assert str(e) == "Test error"
            assert db.conn is None
            assert db.cursor is None

def test_database_connection(test_db_path, sample_episode):
    """Test basic database connection and episode insertion."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            episode_id = db.insert_episode(sample_episode)
            assert episode_id is not None
            assert isinstance(episode_id, int)

def test_insert_episode(test_db_path, sample_episode):
    """Test episode insertion and retrieval."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            episode_id = db.insert_episode(sample_episode)
            retrieved = db.get_episode(episode_id)
            assert retrieved['guid'] == sample_episode['guid']
            assert retrieved['title'] == sample_episode['title']

def test_duplicate_episode(test_db_path, sample_episode):
    """Test handling of duplicate episodes."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            # First insertion should succeed
            first_id = db.insert_episode(sample_episode)
            assert first_id is not None

            # Second insertion should return None
            second_id = db.insert_episode(sample_episode)
            assert second_id is None

def test_get_episode(test_db_path, sample_episode):
    """Test retrieving a single episode."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            episode_id = db.insert_episode(sample_episode)
            retrieved = db.get_episode(episode_id)
            assert retrieved is not None
            assert retrieved['guid'] == sample_episode['guid']

            # Test non-existent episode
            assert db.get_episode(999999) is None

def test_update_episode(test_db_path, sample_episode):
    """Test updating an episode."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            episode_id = db.insert_episode(sample_episode)
            update_data = {
                'title': 'Updated Title',
                'cleaning_status': 'cleaned',
                'cleaning_timestamp': datetime.utcnow().isoformat()
            }
            assert db.update_episode(episode_id, update_data)

            # Verify update
            retrieved = db.get_episode(episode_id)
            assert retrieved['title'] == 'Updated Title'
            assert retrieved['cleaning_status'] == 'cleaned'

def test_get_all_episodes(test_db_path, sample_episode):
    """Test retrieving all episodes."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            # Insert multiple episodes
            db.insert_episode(sample_episode)
            db.insert_episode({**sample_episode, 'guid': 'test-guid-456'})

            episodes = db.get_all_episodes()
            assert len(episodes) == 2
            assert all(isinstance(ep, dict) for ep in episodes)

def test_get_episodes_by_status(test_db_path, sample_episode):
    """Test retrieving episodes by status."""
    with patch.dict(os.environ, {'DB_PATH_TEST': test_db_path}):
        with Database() as db:
            # Insert episodes with different statuses
            db.insert_episode({**sample_episode, 'cleaning_status': 'pending'})
            db.insert_episode({
                **sample_episode,
                'guid': 'test-guid-456',
                'cleaning_status': 'cleaned'
            })

            pending = db.get_episodes_by_status('pending')
            cleaned = db.get_episodes_by_status('cleaned')

            assert len(pending) == 1
            assert len(cleaned) == 1
            assert pending[0]['cleaning_status'] == 'pending'
            assert cleaned[0]['cleaning_status'] == 'cleaned' 