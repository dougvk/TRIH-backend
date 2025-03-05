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
        "Format": ["Standalone Episodes"],
        "Theme": ["Military History & Battles", "Modern Political History & Leadership", "Regional & National Histories"],
        "Track": ["Military & Battles Track"],
        "episode_number": None
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
        format_tags, theme_tags, track_tags, episode_number = tagger.generate_tags(title, description)

        # Verify that the mock was called correctly
        mock_client.chat.completions.create.assert_called_once()
        assert format_tags == ["Standalone Episodes"]
        assert set(theme_tags) == set(["Military History & Battles", "Modern Political History & Leadership", "Regional & National Histories"])
        assert track_tags == ["Military & Battles Track"]
        assert episode_number is None

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
        format_tags, theme_tags, track_tags, episode_number = tagger.generate_tags("Test Title", "Test Description")
        assert format_tags == ['Standalone Episodes']
        assert theme_tags == ['General History']
        assert track_tags == ['General History Track']
        assert episode_number is None

def test_generate_tags_invalid_response():
    tagger = EpisodeTagger()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"Format": ["INVALID_TAG"], "Theme": ["INVALID_THEME"], "Track": ["INVALID_TRACK"], "episode_number": null}'
    
    with patch.object(tagger.client.chat.completions, 'create', return_value=mock_response):
        format_tags, theme_tags, track_tags, episode_number = tagger.generate_tags("Test Title", "Test Description")
        assert format_tags == ['Standalone Episodes']  # Default when all tags are invalid
        assert theme_tags == ['General History']
        assert track_tags == ['General History Track']
        assert episode_number is None

def test_generate_tags_partial_invalid():
    tagger = EpisodeTagger()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"Format": ["Series Episodes", "INVALID_TAG"], "Theme": ["Ancient & Classical Civilizations", "INVALID_THEME"], "Track": ["Roman Track", "INVALID_TRACK"], "episode_number": null}'
    
    with patch.object(tagger.client.chat.completions, 'create', return_value=mock_response):
        format_tags, theme_tags, track_tags, episode_number = tagger.generate_tags("Test Title", "Test Description")
        assert format_tags == ['Series Episodes']  # Valid tag kept
        assert theme_tags == ['Ancient & Classical Civilizations']  # Valid tag kept
        assert track_tags == ['Roman Track']  # Valid tag kept
        assert episode_number is None

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

def test_generate_tags_rihc_series():
    """Test RIHC series detection and tagging."""
    title = "RIHC: The Roman Republic"
    description = "In this episode, we explore the rise of the Roman Republic."
    
    mock_response = {
        "Format": ["RIHC Series", "Series Episodes"],
        "Theme": ["Ancient & Classical Civilizations"],
        "Track": ["Roman Track"],
        "episode_number": None
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
        tagger.client = mock_client
        format_tags, theme_tags, track_tags, episode_number = tagger.generate_tags(title, description)

        assert "RIHC Series" in format_tags
        assert "Series Episodes" in format_tags
        assert episode_number is None

def test_generate_tags_series_with_episode_number():
    """Test series episode detection with episode number extraction."""
    test_cases = [
        ("The French Revolution (Ep 3): The Terror", 3),
        ("World War II Part 4: D-Day", 4),
        ("Ancient Rome (Part 2): The Republic", 2),
        ("The Civil War - Part 5", 5)
    ]

    mock_base_response = {
        "Format": ["Series Episodes"],
        "Theme": ["Military History & Battles"],
        "Track": ["Military & Battles Track"]
    }

    for title, expected_number in test_cases:
        mock_response = mock_base_response.copy()
        mock_response["episode_number"] = expected_number

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
            tagger.client = mock_client
            format_tags, theme_tags, track_tags, episode_number = tagger.generate_tags(
                title, 
                "Test description"
            )

            assert "Series Episodes" in format_tags
            assert episode_number == expected_number

def test_generate_tags_standalone_episode():
    """Test standalone episode detection."""
    title = "The Battle of Hastings"
    description = "A one-off episode about the Norman Conquest of England."
    
    mock_response = {
        "Format": ["Standalone Episodes"],
        "Theme": ["Medieval History", "Military History & Battles"],
        "Track": ["Military & Battles Track", "British History Track"],
        "episode_number": None
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
        tagger.client = mock_client
        format_tags, theme_tags, track_tags, episode_number = tagger.generate_tags(title, description)

        assert "Standalone Episodes" in format_tags
        assert len(format_tags) == 1  # Should only have Standalone Episodes
        assert episode_number is None

def test_generate_tags_named_series():
    """Test named series detection without explicit episode number."""
    title = "Young Churchill: The Early Years"
    description = "Exploring Winston Churchill's formative years."
    
    mock_response = {
        "Format": ["Series Episodes"],
        "Theme": ["Modern Political History & Leadership", "Regional & National Histories"],
        "Track": ["British History Track", "Historical Figures Track"],
        "episode_number": None
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
        tagger.client = mock_client
        format_tags, theme_tags, track_tags, episode_number = tagger.generate_tags(title, description)

        assert "Series Episodes" in format_tags
        assert episode_number is None  # No explicit episode number

def test_generate_tags_multiple_themes_and_tracks():
    """Test handling of multiple themes and tracks."""
    title = "The Industrial Revolution: Technology and Society"
    description = "Exploring the technological and social changes of the Industrial Revolution."
    
    mock_response = {
        "Format": ["Standalone Episodes"],
        "Theme": ["Modern Political History & Leadership", "Social & Cultural History", "Science & Technology"],
        "Track": ["Modern Political History Track", "Social History Track", "Science & Technology Track"],
        "episode_number": None
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
        tagger.client = mock_client
        format_tags, theme_tags, track_tags, episode_number = tagger.generate_tags(title, description)

        assert len(theme_tags) > 1  # Should have multiple themes
        assert len(track_tags) > 1  # Should have multiple tracks
        assert episode_number is None

def test_tag_episode_with_episode_number():
    """Test that episode number is correctly stored in database."""
    tagger = EpisodeTagger()
    episode = {
        'id': 1,
        'title': 'The French Revolution (Ep 3)',
        'description': 'Test Description',
        'cleaned_description': 'Cleaned Test Description'
    }
    
    mock_db = MagicMock()
    mock_db.get_episode.return_value = episode
    mock_db.update_episode.return_value = True
    
    mock_response = {
        "Format": ["Series Episodes"],
        "Theme": ["Modern Political History & Leadership"],
        "Track": ["Modern Political History Track"],
        "episode_number": 3
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

    with patch('src.modules.tag.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        tagger.client = mock_client
        result = tagger.tag_episode(1)
        
        assert result is True
        mock_db.update_episode.assert_called_once()
        
        # Check that episode_number was included in the update
        call_args = mock_db.update_episode.call_args
        assert call_args is not None
        args, kwargs = call_args
        update_data = args[1]  # Second argument to update_episode
        assert 'episode_number' in update_data
        assert update_data['episode_number'] == 3