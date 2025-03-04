import pytest
from unittest.mock import patch, MagicMock
from src.main import main

def test_ingest_command():
    with patch('src.main.handle_ingest') as mock_ingest:
        with patch('sys.argv', ['main.py', 'ingest', '--feed', 'http://example.com/feed.xml']):
            main()
            mock_ingest.assert_called_once_with('http://example.com/feed.xml')

def test_clean_command():
    with patch('src.main.handle_clean') as mock_clean:
        with patch('sys.argv', ['main.py', 'clean']):
            main()
            mock_clean.assert_called_once()

def test_tag_command():
    with patch('src.main.handle_tag') as mock_tag:
        with patch('sys.argv', ['main.py', 'tag']):
            main()
            mock_tag.assert_called_once()

def test_export_command():
    with patch('src.main.handle_export') as mock_export:
        with patch('sys.argv', ['main.py', 'export', '--format', 'json', '--output', 'output.json']):
            main()
            mock_export.assert_called_once_with('json', 'output.json')

def test_validate_command():
    with patch('src.main.handle_validate') as mock_validate:
        with patch('sys.argv', ['main.py', 'validate']):
            main()
            mock_validate.assert_called_once()

def test_invalid_command():
    with patch('sys.argv', ['main.py', 'invalid']):
        with pytest.raises(SystemExit):
            main()

def test_no_command():
    with patch('sys.argv', ['main.py']):
        with pytest.raises(SystemExit):
            main()

def test_help_command():
    with patch('sys.argv', ['main.py', '--help']):
        with pytest.raises(SystemExit):
            main() 