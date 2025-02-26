"""
Configuration settings for Twitch VOD Archiver
"""

# Options for fetching VOD information
FETCH_OPTS = {
    'quiet': False,
    'extract_flat': True,
    'force_generic_extractor': True,
    'verbose': True,
}

# Base options for downloading VODs
DOWNLOAD_OPTS = {
    'quiet': False,
    'verbose': True,
    'progress_bar': True,
    'format': 'best',
}