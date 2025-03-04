"""
Static taxonomy definitions for podcast episode tagging.
"""

# Format tags describe the type of episode
FORMAT_TAGS = {
    'SERIES_EPISODES': 'Episodes that are part of a series',
    'STANDALONE_EPISODES': 'Individual, self-contained episodes',
    'RIHC_SERIES': 'Episodes specifically part of the RIHC series'
}

# Theme tags describe the main historical topics or subjects covered
THEME_TAGS = {
    'ANCIENT_CLASSICAL': 'Ancient & Classical Civilizations',
    'MEDIEVAL_RENAISSANCE': 'Medieval & Renaissance Europe',
    'EMPIRE_COLONIALISM': 'Empire, Colonialism & Exploration',
    'MODERN_POLITICAL': 'Modern Political History & Leadership',
    'MILITARY_BATTLES': 'Military History & Battles',
    'CULTURAL_SOCIAL': 'Cultural, Social & Intellectual History',
    'SCIENCE_TECH_ECONOMIC': 'Science, Technology & Economic History',
    'RELIGIOUS_PHILOSOPHICAL': 'Religious, Ideological & Philosophical History',
    'HISTORICAL_MYSTERIES': 'Historical Mysteries, Conspiracies & Scandals',
    'REGIONAL_NATIONAL': 'Regional & National Histories'}

# Track tags describe the specific historical track or series
TRACK_TAGS = {
    'ROMAN': 'Roman Track',
    'MEDIEVAL_RENAISSANCE_TRACK': 'Medieval & Renaissance Track',
    'COLONIALISM_EXPLORATION': 'Colonialism & Exploration Track',
    'AMERICAN_HISTORY': 'American History Track',
    'MILITARY_BATTLES_TRACK': 'Military & Battles Track',
    'MODERN_POLITICAL_TRACK': 'Modern Political History Track',
    'CULTURAL_SOCIAL_TRACK': 'Cultural & Social History Track',
    'SCIENCE_TECH_ECONOMIC_TRACK': 'Science, Technology & Economic History Track',
    'RELIGIOUS_IDEOLOGICAL': 'Religious & Ideological History Track',
    'HISTORICAL_MYSTERIES_TRACK': 'Historical Mysteries & Conspiracies Track',
    'BRITISH_HISTORY': 'British History Track',
    'GLOBAL_EMPIRES': 'Global Empires Track',
    'WORLD_WARS': 'World Wars Track',
    'ANCIENT_CIVILIZATIONS': 'Ancient Civilizations Track',
    'REGIONAL_LATAM': 'Regional Spotlight: Latin America Track',
    'REGIONAL_ASIA_ME': 'Regional Spotlight: Asia & the Middle East Track',
    'REGIONAL_EUROPE': 'Regional Spotlight: Europe Track',
    'REGIONAL_AFRICA': 'Regional Spotlight: Africa Track',
    'HISTORICAL_FIGURES': 'Historical Figures Track',
    'RIHC_BONUS': 'The RIHC Bonus Track',
    'ARCHIVE_EDITIONS': 'Archive Editions Track',
    'CONTEMPORARY_ISSUES': 'Contemporary Issues Through History Track'}

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

    Special validation: If 'RIHC_SERIES' is in format_tags, 'SERIES_EPISODES' must also be present.
    """
    invalid_tags = {
        'format': [tag for tag in format_tags if tag not in FORMAT_TAGS],
        'theme': [tag for tag in theme_tags if tag not in THEME_TAGS],
        'track': [tag for tag in track_tags if tag not in TRACK_TAGS]
    }

    # Special validation for RIHC Series requirement
    if 'RIHC_SERIES' in format_tags and 'SERIES_EPISODES' not in format_tags:
        if 'format' not in invalid_tags:
            invalid_tags['format'] = []
        invalid_tags['format'].append('MISSING_SERIES_EPISODES_FOR_RIHC')

    # Only return categories with invalid tags
    return {k: v for k, v in invalid_tags.items() if v}
