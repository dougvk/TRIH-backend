import os
import pytest
import sqlite3
from dotenv import load_dotenv
import tempfile
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables for testing."""
    load_dotenv()
    os.environ["ENV_MODE"] = "test"

@pytest.fixture(autouse=True)
def test_db_path(tmp_path):
    """Create a temporary database path and set it in environment."""
    db_path = tmp_path / "test.db"
    old_db_path = os.environ.get('DB_PATH_TEST')
    os.environ['DB_PATH_TEST'] = str(db_path)
    yield str(db_path)
    # Clean up
    if db_path.exists():
        db_path.unlink()
    if old_db_path:
        os.environ['DB_PATH_TEST'] = old_db_path
    else:
        del os.environ['DB_PATH_TEST']

@pytest.fixture
def test_db(test_db_path):
    """Create a temporary test database."""
    # Create a new database connection
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    
    # Create the episodes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guid TEXT UNIQUE,
        title TEXT,
        description TEXT,
        cleaned_description TEXT,
        link TEXT,
        published_date TIMESTAMP,
        duration TEXT,
        audio_url TEXT,
        cleaning_timestamp TIMESTAMP,
        cleaning_status TEXT,
        tags TEXT,
        tagging_timestamp TIMESTAMP,
        episode_number INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guid ON episodes(guid)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_date ON episodes(published_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cleaning_status ON episodes(cleaning_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_episode_number ON episodes(episode_number)")
    
    conn.commit()
    
    yield conn
    
    # Cleanup
    conn.close()

@pytest.fixture
def sample_episode():
    """Return a sample episode dictionary for testing."""
    return {
        "guid": "test-guid-123",
        "title": "Test Episode",
        "description": "This is a test episode description.",
        "link": "https://example.com/episode1",
        "published_date": "2024-03-04T12:00:00Z",
        "duration": "01:00:00",
        "audio_url": "https://example.com/episode1.mp3",
        "cleaning_status": "pending",
        "tags": '{"format": ["Series Episodes"], "theme": ["Military History & Battles"], "track": ["Military & Battles Track"]}',
        "episode_number": 1
    } 