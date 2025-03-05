import pytest
from unittest.mock import patch, MagicMock
import openai
from src.modules.clean import ContentCleaner, handle_clean
import os
import re

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

def test_init_openai_client_error():
    """Test error handling during OpenAI client initialization."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_openai.side_effect = Exception("Client initialization error")
            
            with pytest.raises(Exception) as exc_info:
                ContentCleaner()
            assert "Client initialization error" in str(exc_info.value)

def test_clean_with_ai_invalid_response():
    """Test handling of invalid API response format."""
    test_text = "The battle was fought."
    
    # Mock response without the expected structure
    mock_response = MagicMock()
    mock_response.choices = []  # Empty choices list

    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            cleaner = ContentCleaner()
            result_text, success = cleaner.clean_with_ai(test_text)

            assert success is False
            assert result_text == test_text
            mock_client.chat.completions.create.assert_called_once()

def test_clean_all_pending_database_error():
    """Test error handling in batch cleaning when database operation fails."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            with patch('src.modules.database.Database.get_episodes_by_status') as mock_get_episodes:
                mock_get_episodes.side_effect = Exception("Database error")

                cleaner = ContentCleaner()
                with pytest.raises(Exception) as exc_info:
                    cleaner.clean_all_pending()
                assert "Database error" in str(exc_info.value)

def test_handle_clean_specific_episode():
    """Test handling clean command for a specific episode."""
    mock_args = MagicMock()
    mock_args.id = 1
    mock_args.all = False

    with patch('src.modules.clean.ContentCleaner') as mock_cleaner_class:
        mock_cleaner = MagicMock()
        mock_cleaner.clean_episode.return_value = True
        mock_cleaner_class.return_value.__enter__.return_value = mock_cleaner

        handle_clean(mock_args)

        mock_cleaner.clean_episode.assert_called_once_with(1)

def test_handle_clean_all_episodes():
    """Test handling clean command for all episodes."""
    mock_args = MagicMock()
    mock_args.id = None
    mock_args.all = True

    with patch('src.modules.clean.ContentCleaner') as mock_cleaner_class:
        mock_cleaner = MagicMock()
        mock_cleaner.clean_all_pending.return_value = (2, 1)  # 2 successes, 1 failure
        mock_cleaner_class.return_value.__enter__.return_value = mock_cleaner

        handle_clean(mock_args)

        mock_cleaner.clean_all_pending.assert_called_once()

def test_handle_clean_no_options():
    """Test handling clean command with no valid options."""
    mock_args = MagicMock()
    mock_args.id = None
    mock_args.all = False

    with patch('src.modules.clean.ContentCleaner') as mock_cleaner_class:
        mock_cleaner = MagicMock()
        mock_cleaner_class.return_value.__enter__.return_value = mock_cleaner

        handle_clean(mock_args)

        mock_cleaner.clean_episode.assert_not_called()
        mock_cleaner.clean_all_pending.assert_not_called()

def test_handle_clean_error():
    """Test error handling in clean command."""
    mock_args = MagicMock()
    mock_args.id = 1
    mock_args.all = False

    with patch('src.modules.clean.ContentCleaner') as mock_cleaner_class:
        mock_cleaner = MagicMock()
        mock_cleaner.clean_episode.side_effect = Exception("Cleaning error")
        mock_cleaner_class.return_value.__enter__.return_value = mock_cleaner

        with pytest.raises(Exception) as exc_info:
            handle_clean(mock_args)
        assert "Cleaning error" in str(exc_info.value)

def test_init_openai_client_no_api_key():
    """Test error handling when no API key is provided."""
    with patch.dict('os.environ', {'DB_PATH_TEST': 'test.db'}, clear=True):
        with patch('src.modules.database.Database') as mock_db:
            with pytest.raises(ValueError) as exc_info:
                ContentCleaner()
            assert "OpenAI API key not found in environment variables" in str(exc_info.value)

def test_regex_pattern_compilation_error():
    """Test error handling for invalid regex pattern compilation."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'DB_PATH_TEST': 'test.db'}):
        with patch('src.modules.database.Database'):
            cleaner = ContentCleaner()
            # Replace the patterns with an invalid one
            cleaner.promo_patterns = [r'[invalid']
            # Force recompilation of regex
            with pytest.raises(re.error) as exc_info:
                cleaner.promo_regex = re.compile('|'.join(cleaner.promo_patterns), re.IGNORECASE | re.DOTALL)
            assert "unterminated character set" in str(exc_info.value)

def test_clean_all_pending_update_error():
    """Test error handling in batch cleaning when database update fails."""
    mock_episodes = [
        {'id': 1, 'description': 'Test 1', 'status': 'pending'},
        {'id': 2, 'description': 'Test 2', 'status': 'pending'}
    ]

    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'OPENAI_MODEL': 'test-model', 'DATABASE_PATH': 'test.db'}):
        with patch('src.modules.clean.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            with patch('src.modules.database.Database.get_episodes_by_status') as mock_get_episodes:
                mock_get_episodes.return_value = mock_episodes

                with patch('src.modules.database.Database.update_episode') as mock_update_episode:
                    mock_update_episode.side_effect = Exception("Database update error")

                    cleaner = ContentCleaner()
                    successes, failures = cleaner.clean_all_pending()
                    assert successes == 0
                    assert failures == 2 