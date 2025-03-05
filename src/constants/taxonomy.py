"""
Static taxonomy definitions for podcast episode tagging.
"""

# Format tags describe the type of episode
FORMAT_TAGS = {
    'Series Episodes': 'Episodes that are part of a series',
    'Standalone Episodes': 'Individual, self-contained episodes',
    'RIHC Series': 'Episodes specifically part of the RIHC series'
}

# Theme tags describe the main historical topics or subjects covered
THEME_TAGS = {
    'Ancient & Classical Civilizations': 'Ancient & Classical Civilizations',
    'Medieval History': 'Medieval & Renaissance Europe',
    'Empire & Colonialism': 'Empire, Colonialism & Exploration',
    'Modern Political History & Leadership': 'Modern Political History & Leadership',
    'Military History & Battles': 'Military History & Battles',
    'Social & Cultural History': 'Cultural, Social & Intellectual History',
    'Science & Technology': 'Science, Technology & Economic History',
    'Religious & Philosophical History': 'Religious, Ideological & Philosophical History',
    'Historical Mysteries': 'Historical Mysteries, Conspiracies & Scandals',
    'Regional & National Histories': 'Regional & National Histories',
    'General History': 'General History Topics'
}

# Track tags describe the specific historical track or series
TRACK_TAGS = {
    'Roman Track': 'Roman History Track',
    'Medieval Track': 'Medieval & Renaissance Track',
    'Colonial Track': 'Colonialism & Exploration Track',
    'American History Track': 'American History Track',
    'Military & Battles Track': 'Military & Battles Track',
    'Modern Political History Track': 'Modern Political History Track',
    'Social History Track': 'Cultural & Social History Track',
    'Science & Technology Track': 'Science, Technology & Economic History Track',
    'Religious History Track': 'Religious & Ideological History Track',
    'Historical Mysteries Track': 'Historical Mysteries & Conspiracies Track',
    'British History Track': 'British History Track',
    'Global Empires Track': 'Global Empires Track',
    'World Wars Track': 'World Wars Track',
    'Ancient Civilizations Track': 'Ancient Civilizations Track',
    'Latin America Track': 'Regional Spotlight: Latin America Track',
    'Asia & Middle East Track': 'Regional Spotlight: Asia & the Middle East Track',
    'European History Track': 'Regional Spotlight: Europe Track',
    'African History Track': 'Regional Spotlight: Africa Track',
    'Historical Figures Track': 'Historical Figures Track',
    'The RIHC Bonus Track': 'The RIHC Bonus Track',
    'Archive Track': 'Archive Editions Track',
    'Contemporary History Track': 'Contemporary Issues Through History Track',
    'General History Track': 'General History Track'
}

# All available tags combined
ALL_TAGS = {
    'format': FORMAT_TAGS,
    'theme': THEME_TAGS,
    'track': TRACK_TAGS
}


def validate_tags(
        format_tags: list,
        theme_tags: list,
        track_tags: list) -> dict:
    """
    Validate that provided tags exist in the taxonomy.
    Returns a dictionary of invalid tags by category.

    Special validations:
    1. If 'RIHC Series' is in format_tags, 'Series Episodes' must also be present
    2. At least one theme tag is required
    3. At least one track tag is required
    """
    invalid_tags = {
        'format': [tag for tag in format_tags if tag not in FORMAT_TAGS],
        'theme': [tag for tag in theme_tags if tag not in THEME_TAGS],
        'track': [tag for tag in track_tags if tag not in TRACK_TAGS]
    }

    # Special validation for RIHC Series requirement
    if 'RIHC Series' in format_tags and 'Series Episodes' not in format_tags:
        if 'format' not in invalid_tags:
            invalid_tags['format'] = []
        invalid_tags['format'].append('MISSING_SERIES_EPISODES_FOR_RIHC')

    # Validate minimum requirements
    if not theme_tags:
        if 'theme' not in invalid_tags:
            invalid_tags['theme'] = []
        invalid_tags['theme'].append('MISSING_THEME')

    if not track_tags:
        if 'track' not in invalid_tags:
            invalid_tags['track'] = []
        invalid_tags['track'].append('MISSING_TRACK')

    # Only return categories with invalid tags
    return {k: v for k, v in invalid_tags.items() if v}
