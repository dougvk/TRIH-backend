import pytest
import json
import csv
import os
from unittest.mock import patch, MagicMock
from src.modules.export import DataExporter

@pytest.fixture
def sample_episodes():
    """Return sample episodes for testing."""
    return [
        {
            "id": 1,
            "guid": "test-guid-1",
            "title": "Test Episode 1",
            "description": "Description 1",
            "cleaned_description": "Cleaned Description 1",
            "link": "https://example.com/1",
            "published_date": "2024-03-04T12:00:00Z",
            "duration": "01:00:00",
            "audio_url": "https://example.com/1.mp3",
            "cleaning_status": "cleaned",
            "format_tags": "Series Episodes",
            "theme_tags": "Military History & Battles",
            "track_tags": "Military & Battles Track",
            "episode_number": 1,
            "cleaning_timestamp": "2024-03-04T12:30:00Z",
            "created_at": "2024-03-04T12:00:00Z",
            "updated_at": "2024-03-04T12:30:00Z"
        },
        {
            "id": 2,
            "guid": "test-guid-2",
            "title": "Test Episode 2",
            "description": "Description 2",
            "cleaned_description": "Cleaned Description 2",
            "link": "https://example.com/2",
            "published_date": "2024-03-04T13:00:00Z",
            "duration": "00:45:00",
            "audio_url": "https://example.com/2.mp3",
            "cleaning_status": "cleaned",
            "format_tags": "Series Episodes",
            "theme_tags": "Cultural, Social & Intellectual History",
            "track_tags": "Cultural & Social History Track",
            "episode_number": 2,
            "cleaning_timestamp": "2024-03-04T13:30:00Z",
            "created_at": "2024-03-04T13:00:00Z",
            "updated_at": "2024-03-04T13:30:00Z"
        }
    ]

def test_prepare_episode_data(sample_episodes):
    """Test preparation of episode data for export."""
    exporter = DataExporter()
    prepared_data = exporter._prepare_episode_data(sample_episodes[0])
    
    assert isinstance(prepared_data, dict)
    assert prepared_data["guid"] == "test-guid-1"
    assert isinstance(prepared_data["format_tags"], list)
    assert prepared_data["format_tags"] == ["Series Episodes"]
    assert prepared_data["theme_tags"] == ["Military History & Battles"]
    assert prepared_data["track_tags"] == ["Military & Battles Track"]

def test_prepare_episode_data_missing_fields():
    """Test preparation of episode data with missing fields."""
    exporter = DataExporter()
    episode = {
        "id": 1,
        "guid": "test-guid-1",
        "title": "Test Episode 1",
        # Missing most fields
    }
    
    prepared_data = exporter._prepare_episode_data(episode)
    
    assert isinstance(prepared_data, dict)
    assert prepared_data["guid"] == "test-guid-1"
    assert prepared_data["format_tags"] == []
    assert prepared_data["theme_tags"] == []
    assert prepared_data["track_tags"] == []
    assert prepared_data["description"] is None
    assert prepared_data["cleaned_description"] is None

@patch('src.modules.database.Database.get_all_episodes')
def test_export_to_json(mock_get_all_episodes, sample_episodes, tmp_path):
    """Test exporting episodes to JSON."""
    mock_get_all_episodes.return_value = sample_episodes
    output_path = tmp_path / "test_export.json"
    
    exporter = DataExporter()
    
    # Test with output path
    result = exporter.export_to_json(sample_episodes, str(output_path))
    assert result is True
    assert output_path.exists()
    with open(output_path) as f:
        exported_data = json.load(f)
        assert isinstance(exported_data, list)
        assert len(exported_data) == 2
        assert exported_data[0]["guid"] == "test-guid-1"
        assert exported_data[1]["guid"] == "test-guid-2"
        assert isinstance(exported_data[0]["format_tags"], list)
    
    # Test without output path
    result = exporter.export_to_json(sample_episodes)
    assert isinstance(result, str)
    exported_data = json.loads(result)
    assert isinstance(exported_data, list)
    assert len(exported_data) == 2
    assert exported_data[0]["guid"] == "test-guid-1"
    assert exported_data[1]["guid"] == "test-guid-2"
    assert isinstance(exported_data[0]["format_tags"], list)

@patch('src.modules.database.Database.get_all_episodes')
def test_export_to_csv(mock_get_all_episodes, sample_episodes, tmp_path):
    """Test exporting episodes to CSV."""
    mock_get_all_episodes.return_value = sample_episodes
    output_path = tmp_path / "test_export.csv"
    
    exporter = DataExporter()
    result = exporter.export_to_csv(sample_episodes, str(output_path))
    
    assert result is True
    assert output_path.exists()
    
    # Verify CSV content
    with open(output_path, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["guid"] == "test-guid-1"
        assert rows[1]["guid"] == "test-guid-2"
        assert "format_tags" in rows[0]  # format_tags should be JSON string in CSV

@patch('src.modules.database.Database.get_all_episodes')
def test_export_to_json_no_episodes(mock_get_all_episodes, tmp_path):
    """Test exporting when there are no episodes."""
    mock_get_all_episodes.return_value = []
    output_path = tmp_path / "empty_export.json"
    
    exporter = DataExporter()
    result = exporter.export_to_json([], str(output_path))
    
    assert result is True
    assert output_path.exists()
    
    with open(output_path) as f:
        exported_data = json.load(f)
        assert len(exported_data) == 0

@patch('src.modules.database.Database.get_all_episodes')
def test_export_to_csv_no_episodes(mock_get_all_episodes, tmp_path):
    """Test exporting when there are no episodes."""
    mock_get_all_episodes.return_value = []
    output_path = tmp_path / "empty_export.csv"
    
    exporter = DataExporter()
    result = exporter.export_to_csv([], str(output_path))
    
    assert result is True
    assert output_path.exists()
    
    with open(output_path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header row
        rows = list(reader)
        assert len(rows) == 0

@patch('src.modules.database.Database.get_all_episodes')
def test_export_main_function(mock_get_episodes, sample_episodes, tmp_path):
    """Test the main export function."""
    mock_get_episodes.return_value = sample_episodes
    
    # Test JSON export
    json_path = tmp_path / "export.json"
    exporter = DataExporter()
    result = exporter.export(str(json_path), "json")
    assert result is True
    assert json_path.exists()
    
    # Test CSV export
    csv_path = tmp_path / "export.csv"
    result = exporter.export(str(csv_path), "csv")
    assert result is True
    assert csv_path.exists()

def test_export_invalid_format(tmp_path):
    """Test export with invalid format."""
    output_path = tmp_path / "test_export.txt"
    
    exporter = DataExporter()
    with pytest.raises(ValueError):
        exporter.export(str(output_path), "invalid_format")

@patch('src.modules.database.Database.get_all_episodes')
def test_export_with_limit(mock_get_all_episodes, sample_episodes, tmp_path):
    """Test exporting with a limit on the number of episodes."""
    mock_get_all_episodes.return_value = sample_episodes
    output_path = tmp_path / "test_export_limit.json"
    
    exporter = DataExporter()
    result = exporter.export(str(output_path), format='json', limit=1)
    
    assert result is True
    assert output_path.exists()
    
    with open(output_path) as f:
        exported_data = json.load(f)
        assert len(exported_data) == 1
        # Should get the most recent episode (sample_episodes[1] has later date)
        assert exported_data[0]["guid"] == "test-guid-2" 