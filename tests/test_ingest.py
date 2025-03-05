import pytest
from unittest.mock import patch, MagicMock
from src.modules.ingest import RSSFeedIngestor, handle_ingest
import requests
from lxml import etree
import os
from pathlib import Path

@pytest.fixture
def sample_rss_content():
    """Return sample RSS content for testing."""
    return """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>Test Podcast</title>
            <item>
                <title>Test Episode 1</title>
                <guid>test-guid-123</guid>
                <description>Test description 1</description>
                <link>https://example.com/episode1</link>
                <pubDate>Mon, 04 Mar 2024 12:00:00 GMT</pubDate>
                <duration>01:00:00</duration>
                <enclosure url="https://example.com/episode1.mp3" type="audio/mpeg" />
            </item>
            <item>
                <title>Test Episode 2</title>
                <guid>test-guid-456</guid>
                <description>Test description 2</description>
                <link>https://example.com/episode2</link>
                <pubDate>Mon, 04 Mar 2024 13:00:00 GMT</pubDate>
                <duration>00:45:00</duration>
                <enclosure url="https://example.com/episode2.mp3" type="audio/mpeg" />
            </item>
        </channel>
    </rss>"""

def test_fetch_feed():
    """Test fetching RSS feed content."""
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'<rss><channel></channel></rss>'
        
        ingestor = RSSFeedIngestor()
        content = ingestor.fetch_feed()
        
        assert content is not None
        assert b'<rss>' in content
        mock_get.assert_called_once()

def test_fetch_feed_failure():
    """Test handling of feed fetch failures."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("Failed to fetch feed")
        
        ingestor = RSSFeedIngestor("http://example.com/feed")
        with pytest.raises(requests.RequestException):
            ingestor.fetch_feed()

def test_parse_feed(sample_rss_content):
    """Test parsing RSS feed content."""
    ingestor = RSSFeedIngestor()
    episodes = ingestor.parse_feed(sample_rss_content.encode())
    
    assert len(episodes) == 2
    
    # Verify first episode
    episode = episodes[0]
    assert episode["title"] == "Test Episode 1"
    assert episode["guid"] == "test-guid-123"
    assert episode["description"] == "Test description 1"
    assert episode["link"] == "https://example.com/episode1"
    assert episode["duration"] == "01:00:00"
    assert episode["audio_url"] == "https://example.com/episode1.mp3"

def test_parse_feed_with_missing_fields(sample_rss_content):
    """Test parsing RSS feed with missing optional fields."""
    modified_content = sample_rss_content.replace("<duration>01:00:00</duration>", "")
    
    ingestor = RSSFeedIngestor()
    episodes = ingestor.parse_feed(modified_content.encode())
    
    assert len(episodes) == 2
    assert episodes[0]["duration"] is None

@patch('src.modules.ingest.RSSFeedIngestor.fetch_feed')
@patch('src.modules.database.Database.insert_episode')
def test_ingest(mock_insert, mock_fetch, sample_rss_content):
    """Test ingesting episodes from RSS feed."""
    mock_fetch.return_value = sample_rss_content.encode()
    mock_insert.side_effect = [1, 2]  # Return episode IDs
    
    ingestor = RSSFeedIngestor()
    new_count, duplicate_count = ingestor.ingest()
    
    assert new_count == 2
    assert duplicate_count == 0
    assert mock_insert.call_count == 2

@patch('src.modules.ingest.RSSFeedIngestor.fetch_feed')
@patch('src.modules.database.Database.insert_episode')
def test_ingest_with_duplicates(mock_insert, mock_fetch, sample_rss_content):
    """Test ingesting episodes with duplicates."""
    mock_fetch.return_value = sample_rss_content.encode()
    mock_insert.side_effect = [1, None]  # First episode new, second duplicate
    
    ingestor = RSSFeedIngestor()
    new_count, duplicate_count = ingestor.ingest()
    
    assert new_count == 1
    assert duplicate_count == 1
    assert mock_insert.call_count == 2

def test_parse_duration_hhmmss():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.parse_duration('01:30:45') == '01:30:45'

def test_parse_duration_mmss():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.parse_duration('30:45') == '00:30:45'

def test_parse_duration_seconds():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.parse_duration('5445') == '01:30:45'  # 1h 30m 45s

def test_parse_duration_invalid():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.parse_duration('invalid') == 'invalid'

def test_parse_duration_none():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.parse_duration(None) is None

def test_extract_episode_number_hash():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.extract_episode_number('Title #123') == 123

def test_extract_episode_number_episode():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.extract_episode_number('Episode 123: Title') == 123

def test_extract_episode_number_ep():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.extract_episode_number('Ep. 123 - Title') == 123
    assert ingestor.extract_episode_number('Ep 123 - Title') == 123

def test_extract_episode_number_e():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.extract_episode_number('E123 - Title') == 123

def test_extract_episode_number_not_found():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    assert ingestor.extract_episode_number('Regular Title') is None

def test_parse_feed_malformed_xml():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    malformed_xml = b'<rss><channel><item><title>Test</title></channel></rss>'
    episodes = ingestor.parse_feed(malformed_xml)
    assert len(episodes) == 0  # Malformed XML should result in no episodes

def test_parse_feed_missing_required_fields():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    xml = b'''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <item>
                <title></title>
                <guid></guid>
            </item>
        </channel>
    </rss>'''
    episodes = ingestor.parse_feed(xml)
    assert len(episodes) == 0

def test_parse_feed_invalid_date():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    xml = b'''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Test Episode</title>
                <guid>test-guid</guid>
                <pubDate>Invalid Date</pubDate>
            </item>
        </channel>
    </rss>'''
    episodes = ingestor.parse_feed(xml)
    assert episodes[0]['published_date'] is None

def test_ingest_database_error():
    ingestor = RSSFeedIngestor('http://example.com/feed.xml')
    mock_content = b'''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>Test Episode</title>
                <guid>test-guid</guid>
            </item>
        </channel>
    </rss>'''
    
    with patch.object(ingestor, 'fetch_feed', return_value=mock_content):
        with patch('src.modules.ingest.Database') as mock_db_class:
            mock_db = MagicMock()
            mock_db.insert_episode.side_effect = Exception('Database error')
            mock_db_class.return_value.__enter__.return_value = mock_db
            
            with pytest.raises(Exception) as exc_info:
                ingestor.ingest()
            assert str(exc_info.value) == 'Database error'

def test_handle_ingest_success():
    mock_args = MagicMock()
    mock_args.feed = 'http://example.com/feed.xml'
    
    with patch('src.modules.ingest.RSSFeedIngestor') as mock_ingestor_class:
        mock_ingestor = MagicMock()
        mock_ingestor.ingest.return_value = (5, 2)
        mock_ingestor_class.return_value = mock_ingestor
        
        handle_ingest(mock_args)
        
        mock_ingestor_class.assert_called_once_with('http://example.com/feed.xml')
        mock_ingestor.ingest.assert_called_once()

def test_handle_ingest_no_feed_url():
    mock_args = MagicMock()
    mock_args.feed = None
    mock_args.reset = False

    with patch('src.modules.ingest.RSSFeedIngestor') as mock_ingestor_class, \
         patch.dict(os.environ, {'RSS_FEED_URL': ''}):  # Empty feed URL in env
        mock_ingestor = MagicMock()
        mock_ingestor.ingest.return_value = (3, 1)
        mock_ingestor_class.return_value = mock_ingestor

        with pytest.raises(ValueError) as exc_info:
            handle_ingest(mock_args)
        assert str(exc_info.value) == "No RSS feed URL provided in args or environment"

def test_handle_ingest_error():
    mock_args = MagicMock()
    mock_args.feed = 'http://example.com/feed.xml'
    
    with patch('src.modules.ingest.RSSFeedIngestor') as mock_ingestor_class:
        mock_ingestor = MagicMock()
        mock_ingestor.ingest.side_effect = Exception('Ingest error')
        mock_ingestor_class.return_value = mock_ingestor
        
        with pytest.raises(Exception) as exc_info:
            handle_ingest(mock_args)
        assert str(exc_info.value) == 'Ingest error'

@patch('src.modules.ingest.RSSFeedIngestor')
@patch('src.modules.database.Database')
def test_handle_ingest_with_reset(mock_db_class, mock_ingestor_class):
    """Test handling ingest command with reset flag."""
    # Set up mocks
    mock_ingestor = MagicMock()
    mock_ingestor.ingest.return_value = (5, 0)  # 5 new episodes, 0 duplicates
    mock_ingestor_class.return_value = mock_ingestor

    mock_db = MagicMock()
    mock_db_class.return_value = mock_db
    mock_db.__enter__.return_value = mock_db

    # Create a dummy database file
    test_db = 'data/test_episodes.db'
    os.makedirs('data', exist_ok=True)
    Path(test_db).touch()
    assert os.path.exists(test_db)
    old_mtime = os.path.getmtime(test_db)

    # Create args with reset flag
    args = MagicMock()
    args.feed = 'https://example.com/feed.xml'
    args.reset = True

    handle_ingest(args)

    # Check that database was reset
    assert not os.path.exists(test_db) or os.path.getmtime(test_db) > old_mtime
    mock_ingestor_class.assert_called_once_with('https://example.com/feed.xml')
    mock_ingestor.ingest.assert_called_once()

@patch('src.modules.ingest.RSSFeedIngestor')
def test_handle_ingest_without_reset(mock_ingestor_class):
    """Test handling ingest command without reset flag."""
    mock_ingestor = MagicMock()
    mock_ingestor.ingest.return_value = (5, 0)  # 5 new episodes, 0 duplicates
    mock_ingestor_class.return_value = mock_ingestor

    # Create a dummy database file
    test_db = 'data/test_episodes.db'
    os.makedirs('data', exist_ok=True)
    Path(test_db).touch()
    old_mtime = os.path.getmtime(test_db)

    # Create args without reset flag
    args = MagicMock()
    args.feed = 'https://example.com/feed.xml'
    args.reset = False

    handle_ingest(args)

    # Check that database file wasn't deleted (same modification time)
    assert os.path.getmtime(test_db) == old_mtime
    mock_ingestor_class.assert_called_once_with('https://example.com/feed.xml')
    mock_ingestor.ingest.assert_called_once() 