import pytest
from unittest.mock import patch, MagicMock
import openai
from src.modules.clean import ContentCleaner
import os

@pytest.fixture
def sample_text():
    """Return sample text for testing."""
    return """
    In this episode, we discuss the Battle of Waterloo.
    
    🎧 Listen on Spotify: https://spotify.com/episode123
    📱 Follow us on Twitter: @historypodcast
    💰 Support us on Patreon: https://patreon.com/history
    
    The battle began on June 18, 1815, in present-day Belgium.
    """

def test_apply_regex_cleaning(sample_text):
    """Test regex-based cleaning of promotional content."""
    cleaner = ContentCleaner()
    cleaned_text = cleaner.apply_regex_cleaning(sample_text)
    
    # Verify promotional content is removed
    assert "Listen on Spotify" not in cleaned_text
    assert "Follow us on Twitter" not in cleaned_text
    assert "Support us on Patreon" not in cleaned_text
    
    # Verify actual content remains
    assert "Battle of Waterloo" in cleaned_text
    assert "June 18, 1815" in cleaned_text

def test_clean_with_ai():
    """Test AI-based cleaning using OpenAI API."""
    test_text = "The battle was fought. It was a very important battle."
    cleaned_text = "The battle was fought. It was a crucial battle."  # Simulated AI cleaned text

    # Create a mock response object that matches the OpenAI API structure
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content=cleaned_text
            )
        )
    ]

    # Mock the OpenAI client
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            cleaner = ContentCleaner()
            result_text, success = cleaner.clean_with_ai(test_text)

            # Verify the results
            assert success is True
            assert result_text == cleaned_text
            mock_client.chat.completions.create.assert_called_once()

def test_clean_with_ai_api_key_error():
    """Test AI-based cleaning when API key validation fails."""
    test_text = "The battle was fought. It was a very important battle."

    # Mock the OpenAI client to raise an invalid_api_key error
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("invalid_api_key")
            mock_openai.return_value = mock_client

            cleaner = ContentCleaner()
            result_text, success = cleaner.clean_with_ai(test_text)

            # Verify the results
            assert success is True  # Success is True for API key errors in tests
            assert result_text == test_text  # Original text should be returned
            mock_client.chat.completions.create.assert_called_once()

def test_clean_with_ai_failure():
    """Test AI-based cleaning when API call fails."""
    test_text = "The battle was fought. It was a very important battle."

    # Mock the OpenAI client to raise a general error
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API error")
            mock_openai.return_value = mock_client

            cleaner = ContentCleaner()
            result_text, success = cleaner.clean_with_ai(test_text)

            # Verify the results
            assert success is False
            assert result_text == test_text  # Original text should be returned on failure
            mock_client.chat.completions.create.assert_called_once()

@patch('src.modules.database.Database.get_episode')
def test_clean_episode(mock_get_episode):
    """Test cleaning a specific episode."""
    # Mock episode data
    mock_episode = {
        'id': 1,
        'description': 'Test description with promotional content. Subscribe now!',
        'cleaning_status': 'pending'
    }
    mock_get_episode.return_value = mock_episode

    # Create a mock response object that matches the OpenAI API structure
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='Test description without promotional content.'
            )
        )
    ]

    # Mock the OpenAI client
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            with patch('src.modules.database.Database.update_episode') as mock_update_episode:
                mock_update_episode.return_value = True

                cleaner = ContentCleaner()
                success = cleaner.clean_episode(1)

                assert success is True
                mock_get_episode.assert_called_once_with(1)
                mock_update_episode.assert_called_once()
                mock_client.chat.completions.create.assert_called_once()

@patch('src.modules.database.Database.get_episode')
def test_clean_episode_not_found(mock_get_episode):
    """Test cleaning a non-existent episode."""
    mock_get_episode.return_value = None

    cleaner = ContentCleaner()
    success = cleaner.clean_episode(1)

    assert success is False
    mock_get_episode.assert_called_once_with(1)

@patch('src.modules.database.Database.get_episode')
def test_clean_episode_already_cleaned(mock_get_episode):
    """Test cleaning an already cleaned episode."""
    mock_episode = {
        'id': 1,
        'description': 'Test description',
        'cleaning_status': 'completed'
    }
    mock_get_episode.return_value = mock_episode

    cleaner = ContentCleaner()
    success = cleaner.clean_episode(1)

    assert success is True
    mock_get_episode.assert_called_once_with(1)

@patch('src.modules.database.Database.get_episode')
def test_clean_episode_no_description(mock_get_episode):
    """Test cleaning an episode with no description."""
    mock_episode = {
        'id': 1,
        'description': None,
        'cleaning_status': 'pending'
    }
    mock_get_episode.return_value = mock_episode

    cleaner = ContentCleaner()
    success = cleaner.clean_episode(1)

    assert success is False
    mock_get_episode.assert_called_once_with(1)

@patch('src.modules.database.Database.get_episode')
def test_clean_episode_update_failure(mock_get_episode):
    """Test cleaning an episode when database update fails."""
    mock_episode = {
        'id': 1,
        'description': 'Test description with promotional content. Subscribe now!',
        'cleaning_status': 'pending'
    }
    mock_get_episode.return_value = mock_episode

    # Create a mock response object that matches the OpenAI API structure
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='Test description without promotional content.'
            )
        )
    ]

    # Mock the OpenAI client
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            with patch('src.modules.database.Database.update_episode') as mock_update_episode:
                mock_update_episode.return_value = False

                cleaner = ContentCleaner()
                success = cleaner.clean_episode(1)

                assert success is False
                mock_get_episode.assert_called_once_with(1)
                mock_update_episode.assert_called_once()
                mock_client.chat.completions.create.assert_called_once()

@patch('src.modules.database.Database.get_episodes_by_status')
@patch('src.modules.database.Database.get_episode')
def test_clean_all_pending(mock_get_episode, mock_get_episodes):
    """Test cleaning all pending episodes."""
    # Mock episode data
    mock_episodes = [
        {
            'id': 1,
            'description': 'Test description 1 with promotional content. Subscribe now!',
            'cleaning_status': 'pending'
        },
        {
            'id': 2,
            'description': 'Test description 2 with promotional content. Follow us!',
            'cleaning_status': 'pending'
        }
    ]
    mock_get_episodes.return_value = mock_episodes
    mock_get_episode.side_effect = lambda id: next((ep for ep in mock_episodes if ep['id'] == id), None)

    # Create a mock response object that matches the OpenAI API structure
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='Test description without promotional content.'
            )
        )
    ]

    # Mock the OpenAI client
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            with patch('src.modules.database.Database.update_episode') as mock_update_episode:
                mock_update_episode.return_value = True

                cleaner = ContentCleaner()
                success_count, failure_count = cleaner.clean_all_pending()

                assert success_count == 2
                assert failure_count == 0
                mock_get_episodes.assert_called_once_with('pending')
                assert mock_update_episode.call_count == 2
                mock_client.chat.completions.create.assert_called() 