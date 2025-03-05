"""
Tests for the taxonomy module.
"""

import pytest
from src.constants.taxonomy import (
    FORMAT_TAGS,
    THEME_TAGS,
    TRACK_TAGS,
    ALL_TAGS,
    validate_tags
)


def test_taxonomy_constants():
    """Test that taxonomy constants are properly defined."""
    assert 'Series Episodes' in FORMAT_TAGS
    assert 'Standalone Episodes' in FORMAT_TAGS
    assert 'RIHC Series' in FORMAT_TAGS

    assert 'Ancient & Classical Civilizations' in THEME_TAGS
    assert 'Medieval History' in THEME_TAGS
    assert 'Empire & Colonialism' in THEME_TAGS

    assert 'Roman Track' in TRACK_TAGS
    assert 'Medieval Track' in TRACK_TAGS
    assert 'Colonial Track' in TRACK_TAGS


def test_all_tags_structure():
    """Test that ALL_TAGS contains all tag categories."""
    assert 'format' in ALL_TAGS
    assert 'theme' in ALL_TAGS
    assert 'track' in ALL_TAGS

    assert ALL_TAGS['format'] == FORMAT_TAGS
    assert ALL_TAGS['theme'] == THEME_TAGS
    assert ALL_TAGS['track'] == TRACK_TAGS


def test_validate_tags_valid():
    """Test validation with valid tags."""
    format_tags = ['Series Episodes', 'RIHC Series']
    theme_tags = ['Medieval History', 'Military History & Battles']
    track_tags = ['Medieval Track', 'Military & Battles Track']

    invalid_tags = validate_tags(format_tags, theme_tags, track_tags)
    assert not invalid_tags  # Should be empty dict


def test_validate_tags_invalid():
    """Test validation with invalid tags."""
    format_tags = ['Invalid Format', 'Series Episodes']
    theme_tags = ['Invalid Theme', 'Medieval History']
    track_tags = ['Invalid Track', 'Medieval Track']

    invalid_tags = validate_tags(format_tags, theme_tags, track_tags)
    assert 'format' in invalid_tags
    assert 'theme' in invalid_tags
    assert 'track' in invalid_tags
    assert 'Invalid Format' in invalid_tags['format']
    assert 'Invalid Theme' in invalid_tags['theme']
    assert 'Invalid Track' in invalid_tags['track']


def test_validate_tags_empty():
    """Test validation with empty tag lists."""
    invalid_tags = validate_tags([], [], [])
    # Empty lists should fail validation since we require at least one theme and track
    assert 'theme' in invalid_tags
    assert 'track' in invalid_tags
    assert 'MISSING_THEME' in invalid_tags['theme']
    assert 'MISSING_TRACK' in invalid_tags['track']


def test_validate_rihc_series_requirement():
    """Test special validation for RIHC Series requirement."""
    # Test with RIHC Series but without Series Episodes
    format_tags = ['RIHC Series']
    theme_tags = ['Medieval History']  # Add required theme
    track_tags = ['Medieval Track']    # Add required track
    invalid_tags = validate_tags(format_tags, theme_tags, track_tags)
    assert 'format' in invalid_tags
    assert 'MISSING_SERIES_EPISODES_FOR_RIHC' in invalid_tags['format']

    # Test with both RIHC Series and Series Episodes
    format_tags = ['RIHC Series', 'Series Episodes']
    invalid_tags = validate_tags(format_tags, theme_tags, track_tags)
    assert not invalid_tags  # Should be empty dict since we have all required tags


def test_validate_tags_minimum_requirements():
    """Test validation requires at least one track and one theme."""
    # Test with no track
    format_tags = ['Series Episodes']
    theme_tags = ['Medieval History']
    track_tags = []

    invalid_tags = validate_tags(format_tags, theme_tags, track_tags)
    assert 'track' in invalid_tags
    assert 'MISSING_TRACK' in invalid_tags['track']

    # Test with no theme
    format_tags = ['Series Episodes']
    theme_tags = []
    track_tags = ['Medieval Track']

    invalid_tags = validate_tags(format_tags, theme_tags, track_tags)
    assert 'theme' in invalid_tags
    assert 'MISSING_THEME' in invalid_tags['theme']

    # Test with both track and theme - should be valid
    format_tags = ['Series Episodes']
    theme_tags = ['Medieval History']
    track_tags = ['Medieval Track']

    invalid_tags = validate_tags(format_tags, theme_tags, track_tags)
    assert not invalid_tags  # Should be empty dict 