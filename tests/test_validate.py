import pytest
import json
from unittest.mock import patch, MagicMock
from src.modules.validate import TagValidator, handle_validate
from pathlib import Path
import os

@pytest.fixture
def sample_episode():
    """Return a sample episode with tags for testing."""
    return {
        "guid": "test-guid-1",
        "title": "Test Episode 1",
        "format_tags": "Series Episodes",
        "theme_tags": "Military History & Battles",
        "track_tags": "Military & Battles Track"
    }

@pytest.fixture
def invalid_episode():
    """Return a sample episode with invalid tags for testing."""
    return {
        "guid": "test-guid-2",
        "title": "Test Episode 2",
        "format_tags": "Invalid Format",
        "theme_tags": "Invalid Theme",
        "track_tags": "Invalid Track"
    }

def test_get_tag_sets():
    validator = TagValidator()
    episode = {
        'format_tags': 'INTERVIEW,PANEL',
        'theme_tags': 'MILITARY_BATTLES,MODERN_POLITICAL,REGIONAL_NATIONAL',
        'track_tags': 'MILITARY_BATTLES_TRACK'
    }
    format_tags, theme_tags, track_tags = validator.get_tag_sets(episode)
    assert format_tags == {'INTERVIEW', 'PANEL'}
    assert theme_tags == {'MILITARY_BATTLES', 'MODERN_POLITICAL', 'REGIONAL_NATIONAL'}
    assert track_tags == {'MILITARY_BATTLES_TRACK'}

def test_validate_episode_not_found():
    validator = TagValidator()
    mock_db = MagicMock()
    mock_db.get_episode.return_value = None
    with patch('src.modules.validate.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        result = validator.validate_episode(1)
        assert result is False
        mock_db.get_episode.assert_called_once_with(1)

def test_validate_episode_not_tagged():
    validator = TagValidator()
    episode = {
        'id': 1,
        'status': 'cleaned',
        'format_tags': None,
        'theme_tags': None,
        'track_tags': None
    }
    mock_db = MagicMock()
    mock_db.get_episode.return_value = episode
    with patch('src.modules.validate.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        result = validator.validate_episode(1)
        assert result is False
        mock_db.get_episode.assert_called_once_with(1)

def test_validate_episode_invalid_tags():
    validator = TagValidator()
    episode = {
        'id': 1,
        'status': 'tagged',
        'format_tags': 'invalid_format',
        'theme_tags': 'invalid_theme',
        'track_tags': 'invalid_track'
    }
    mock_db = MagicMock()
    mock_db.get_episode.return_value = episode
    with patch('src.modules.validate.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        result = validator.validate_episode(1)
        assert result is False
        mock_db.get_episode.assert_called_once_with(1)

def test_validate_episode_update_failure():
    validator = TagValidator()
    episode = {
        'id': 1,
        'status': 'tagged',
        'format_tags': 'INTERVIEW',
        'theme_tags': 'MODERN_POLITICAL',
        'track_tags': 'MILITARY_BATTLES_TRACK'
    }
    mock_db = MagicMock()
    mock_db.get_episode.return_value = episode
    mock_db.update_episode.side_effect = Exception('Update failed')
    with patch('src.modules.validate.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        result = validator.validate_episode(1)
        assert result is False
        mock_db.get_episode.assert_called_once_with(1)
        mock_db.update_episode.assert_called_once()

def test_validate_all_episodes():
    validator = TagValidator()
    episodes = [
        {'id': 1, 'status': 'tagged'},
        {'id': 2, 'status': 'validated'},
        {'id': 3, 'status': 'tagged'}
    ]
    mock_db = MagicMock()
    mock_db.get_episodes_by_status.return_value = episodes
    with patch('src.modules.validate.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        with patch.object(validator, 'validate_episode', return_value=True) as mock_validate:
            validator.validate_all_pending()
            assert mock_validate.call_count == 2
            mock_validate.assert_any_call(1)
            mock_validate.assert_any_call(3)

def test_get_tag_sets_empty():
    validator = TagValidator()
    episode = {
        'id': 1,
        'status': 'tagged',
        'format_tags': [],
        'theme_tags': [],
        'track_tags': []
    }
    format_tags, theme_tags, track_tags = validator.get_tag_sets(episode)
    assert format_tags == set()
    assert theme_tags == set()
    assert track_tags == set()

def test_validate_all_success():
    validator = TagValidator()
    episodes = [
        {'id': 1, 'title': 'Episode 1', 'status': 'tagged'},
        {'id': 2, 'title': 'Episode 2', 'status': 'tagged'}
    ]
    mock_db = MagicMock()
    mock_db.get_all_episodes.return_value = episodes
    with patch('src.modules.validate.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        with patch.object(validator, 'validate_episode', return_value=True) as mock_validate:
            results = validator.validate_all()
            assert results == []  # No issues found
            assert mock_validate.call_count == 2
            mock_validate.assert_any_call(1)
            mock_validate.assert_any_call(2)

def test_validate_all_with_issues():
    validator = TagValidator()
    episodes = [
        {'id': 1, 'title': 'Episode 1', 'status': 'tagged'},
        {'id': 2, 'title': 'Episode 2', 'status': 'tagged'}
    ]
    mock_db = MagicMock()
    mock_db.get_all_episodes.return_value = episodes
    with patch('src.modules.validate.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        with patch.object(validator, 'validate_episode', return_value=False) as mock_validate:
            results = validator.validate_all()
            assert len(results) == 2
            assert all(r['has_issues'] for r in results)
            assert mock_validate.call_count == 2

def test_validate_all_database_error():
    validator = TagValidator()
    mock_db = MagicMock()
    mock_db.get_all_episodes.side_effect = Exception('Database error')
    with patch('src.modules.validate.Database') as mock_db_class:
        mock_db_class.return_value.__enter__.return_value = mock_db
        with pytest.raises(Exception) as exc_info:
            validator.validate_all()
        assert str(exc_info.value) == 'Database error'

def test_generate_report_without_path():
    validator = TagValidator()
    results = [
        {'episode_id': 1, 'title': 'Episode 1', 'has_issues': True},
        {'episode_id': 2, 'title': 'Episode 2', 'has_issues': True}
    ]
    report_json = validator.generate_report(results)
    report = json.loads(report_json)
    assert report['total_issues'] == 2
    assert len(report['results']) == 2
    assert report['environment'] == 'test'

def test_generate_report_with_path(tmp_path):
    validator = TagValidator()
    results = [{'episode_id': 1, 'title': 'Episode 1', 'has_issues': True}]
    output_path = tmp_path / 'reports' / 'test_report.json'
    report_json = validator.generate_report(results, str(output_path))
    
    # Verify file was created and contains correct data
    assert output_path.exists()
    with open(output_path) as f:
        report = json.load(f)
        assert report['total_issues'] == 1
        assert len(report['results']) == 1

def test_generate_report_file_error():
    validator = TagValidator()
    results = [{'episode_id': 1, 'title': 'Episode 1', 'has_issues': True}]
    with patch('builtins.open', side_effect=IOError('File error')):
        with pytest.raises(Exception) as exc_info:
            validator.generate_report(results, '/invalid/path/report.json')

def test_handle_validate_success():
    mock_args = MagicMock()
    mock_args.report = None
    
    with patch('src.modules.validate.TagValidator') as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate_all.return_value = []
        mock_validator_class.return_value = mock_validator
        
        handle_validate(mock_args)
        
        mock_validator.validate_all.assert_called_once()
        mock_validator.generate_report.assert_called_once()

def test_handle_validate_with_issues():
    mock_args = MagicMock()
    mock_args.report = 'custom_report.json'
    
    with patch('src.modules.validate.TagValidator') as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate_all.return_value = [
            {'episode_id': 1, 'title': 'Episode 1', 'has_issues': True}
        ]
        mock_validator_class.return_value = mock_validator
        
        handle_validate(mock_args)
        
        mock_validator.validate_all.assert_called_once()
        mock_validator.generate_report.assert_called_once_with(
            mock_validator.validate_all.return_value,
            'custom_report.json'
        )

def test_handle_validate_error():
    mock_args = MagicMock()
    mock_args.report = None
    
    with patch('src.modules.validate.TagValidator') as mock_validator_class:
        mock_validator = MagicMock()
        mock_validator.validate_all.side_effect = Exception('Validation error')
        mock_validator_class.return_value = mock_validator
        
        with pytest.raises(Exception) as exc_info:
            handle_validate(mock_args)
        assert str(exc_info.value) == 'Validation error'