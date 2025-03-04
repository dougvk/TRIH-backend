from unittest.mock import MagicMock, patch
import json
from src.modules.tag import EpisodeTagger, handle_tag
import pytest
import os

def test_generate_tags():
    """Test generating tags using OpenAI API."""
    title = "The Battle of Waterloo: Napoleon's Last Stand"
    description = "In this episode, we explore the decisive battle that ended Napoleon's reign."
    mock_response = {
        "format_tags": ["STANDALONE_EPISODES"],
        "theme_tags": ["MILITARY_BATTLES", "MODERN_POLITICAL", "REGIONAL_NATIONAL"],
        "track_tags": ["MILITARY_BATTLES_TRACK"]
    }

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content=json.dumps(mock_response)
                )
            )
        ]
    )

    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        tagger = EpisodeTagger()
        tagger.client = mock_client  # Replace the client directly
        format_tags, theme_tags, track_tags = tagger.generate_tags(title, description)

        # Verify that the mock was called correctly
        mock_client.chat.completions.create.assert_called_once()
        assert format_tags == ["STANDALONE_EPISODES"]
        assert set(theme_tags) == set(["MILITARY_BATTLES", "MODERN_POLITICAL", "REGIONAL_NATIONAL"])
        assert track_tags == ["MILITARY_BATTLES_TRACK"]

def test_tag_episode_not_found():
    tagger = EpisodeTagger()
    mock_db = MagicMock()
    mock_db.get_episode.return_value = None
    with patch('src.modules.tag.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        result = tagger.tag_episode(1)
        assert result is False
        mock_db.get_episode.assert_called_once_with(1)

def test_tag_episode_already_tagged():
    tagger = EpisodeTagger()
    episode = {
        'id': 1,
        'status': 'tagged',
        'format_tags': ['interview'],
        'theme_tags': ['technology'],
        'track_tags': ['software']
    }
    mock_db = MagicMock()
    mock_db.get_episode.return_value = episode
    with patch('src.modules.tag.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        result = tagger.tag_episode(1)
        assert result is False
        mock_db.get_episode.assert_called_once_with(1)

def test_tag_episode_not_cleaned():
    tagger = EpisodeTagger()
    episode = {
        'id': 1,
        'status': 'pending',
        'format_tags': None,
        'theme_tags': None,
        'track_tags': None
    }
    mock_db = MagicMock()
    mock_db.get_episode.return_value = episode
    with patch('src.modules.tag.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        result = tagger.tag_episode(1)
        assert result is False
        mock_db.get_episode.assert_called_once_with(1)

def test_tag_all_episodes():
    tagger = EpisodeTagger()
    episodes = [
        {'id': 1, 'format_tags': None, 'theme_tags': None, 'track_tags': None},
        {'id': 2, 'format_tags': ['INTERVIEW'], 'theme_tags': ['TECHNOLOGY'], 'track_tags': ['MAIN_SERIES']},
        {'id': 3, 'format_tags': None, 'theme_tags': None, 'track_tags': None}
    ]
    mock_db = MagicMock()
    mock_db.get_all_episodes.return_value = episodes
    with patch('src.modules.tag.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        with patch.object(tagger, 'tag_episode', return_value=True) as mock_tag:
            success_count, failure_count = tagger.tag_all_untagged()
            assert success_count == 2
            assert failure_count == 0
            assert mock_tag.call_count == 2
            mock_tag.assert_any_call(1)
            mock_tag.assert_any_call(3)

def test_tag_episode_update_failure():
    tagger = EpisodeTagger()
    episode = {
        'id': 1,
        'status': 'cleaned',
        'title': 'Test Episode',
        'description': 'Test Description',
        'cleaned_description': 'Cleaned Test Description'
    }
    mock_db = MagicMock()
    mock_db.get_episode.return_value = episode
    mock_db.update_episode.side_effect = Exception('Update failed')
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({
            'format_tags': ['INTERVIEW'],
            'theme_tags': ['TECHNOLOGY'],
            'track_tags': ['MAIN_SERIES']
        })))]
    )
    with patch('src.modules.tag.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        tagger.client = mock_client
        result = tagger.tag_episode(1)
        assert result is False
        mock_db.get_episode.assert_called_once_with(1)
        mock_db.update_episode.assert_called_once()

def test_init_missing_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            EpisodeTagger()
        assert str(exc_info.value) == "OpenAI API key not found in environment variables"

def test_generate_tags_api_error():
    tagger = EpisodeTagger()
    with patch.object(tagger.client.chat.completions, 'create') as mock_create:
        mock_create.side_effect = Exception("API Error")
        format_tags, theme_tags, track_tags = tagger.generate_tags("Test Title", "Test Description")
        assert format_tags == ['MONOLOGUE']
        assert theme_tags == ['GENERAL']
        assert track_tags == ['MAIN_SERIES']

def test_generate_tags_invalid_response():
    tagger = EpisodeTagger()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"format_tags": ["INVALID_TAG"], "theme_tags": ["INVALID_THEME"], "track_tags": ["INVALID_TRACK"]}'
    
    with patch.object(tagger.client.chat.completions, 'create', return_value=mock_response):
        format_tags, theme_tags, track_tags = tagger.generate_tags("Test Title", "Test Description")
        assert format_tags == ['MONOLOGUE']  # Default when all tags are invalid
        assert theme_tags == ['GENERAL']
        assert track_tags == ['MAIN_SERIES']

def test_generate_tags_partial_invalid():
    tagger = EpisodeTagger()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"format_tags": ["SERIES_EPISODES", "INVALID_TAG"], "theme_tags": ["ANCIENT_CLASSICAL", "INVALID_THEME"], "track_tags": ["ROMAN", "INVALID_TRACK"]}'
    
    with patch.object(tagger.client.chat.completions, 'create', return_value=mock_response):
        format_tags, theme_tags, track_tags = tagger.generate_tags("Test Title", "Test Description")
        assert format_tags == ['SERIES_EPISODES']  # Valid tag kept
        assert theme_tags == ['ANCIENT_CLASSICAL']  # Valid tag kept
        assert track_tags == ['ROMAN']  # Valid tag kept

def test_handle_tag_specific_episode_success():
    mock_args = MagicMock()
    mock_args.id = 123
    mock_args.all = False
    
    with patch('src.modules.tag.EpisodeTagger') as mock_tagger_class:
        mock_tagger = MagicMock()
        mock_tagger.tag_episode.return_value = True
        mock_tagger_class.return_value = mock_tagger
        
        handle_tag(mock_args)
        
        mock_tagger.tag_episode.assert_called_once_with(123)

def test_handle_tag_specific_episode_failure():
    mock_args = MagicMock()
    mock_args.id = 123
    mock_args.all = False
    
    with patch('src.modules.tag.EpisodeTagger') as mock_tagger_class:
        mock_tagger = MagicMock()
        mock_tagger.tag_episode.return_value = False
        mock_tagger_class.return_value = mock_tagger
        
        handle_tag(mock_args)
        
        mock_tagger.tag_episode.assert_called_once_with(123)

def test_handle_tag_all_episodes():
    mock_args = MagicMock()
    mock_args.id = None
    mock_args.all = True
    
    with patch('src.modules.tag.EpisodeTagger') as mock_tagger_class:
        mock_tagger = MagicMock()
        mock_tagger.tag_all_untagged.return_value = (5, 1)
        mock_tagger_class.return_value = mock_tagger
        
        handle_tag(mock_args)
        
        mock_tagger.tag_all_untagged.assert_called_once()

def test_handle_tag_no_options():
    mock_args = MagicMock()
    mock_args.id = None
    mock_args.all = False
    
    with patch('src.modules.tag.EpisodeTagger') as mock_tagger_class:
        mock_tagger = MagicMock()
        mock_tagger_class.return_value = mock_tagger
        
        handle_tag(mock_args)
        
        mock_tagger.tag_episode.assert_not_called()
        mock_tagger.tag_all_untagged.assert_not_called()

def test_handle_tag_error():
    mock_args = MagicMock()
    mock_args.id = 123
    mock_args.all = False
    
    with patch('src.modules.tag.EpisodeTagger') as mock_tagger_class:
        mock_tagger = MagicMock()
        mock_tagger.tag_episode.side_effect = Exception("Test error")
        mock_tagger_class.return_value = mock_tagger
        
        with pytest.raises(Exception) as exc_info:
            handle_tag(mock_args)
        assert str(exc_info.value) == "Test error"