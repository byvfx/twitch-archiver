"""
Configuration settings for Twitch VOD Archiver
"""

# Options for fetching VOD information
FETCH_OPTS = {
    'quiet': False,
    'extract_flat': True,
    'force_generic_extractor': True,
    'verbose': True,
    'ignoreerrors': True,     # Continue on download errors
    'no_warnings': False,     # Show warnings
    'socket_timeout': 30,     # Timeout for socket connections
    'geo_bypass': True,       # Try to bypass geo-restrictions
}

# Base options for downloading VODs
DOWNLOAD_OPTS = {
    'quiet': False,
    'verbose': True,
    'progress_bar': True,
    'format': 'best',
    'ignoreerrors': True,     # Continue on download errors
    'retries': 10,            # Retry failed downloads
    'fragment_retries': 10,   # Retry failed fragments
    'skip_unavailable_fragments': True,  # Skip unavailable fragments
    'geo_bypass': True,       # Try to bypass geo-restrictions
    'continuedl': True,       # Continue partial downloads
    'no_warnings': False,     # Show warnings
    'socket_timeout': 30,     # Timeout for socket connections
    'concurrent_fragment_downloads': 5,  # Number of fragments to download concurrently
    'hls_prefer_native': True,          # Prefer native HLS implementation
}

# Default file naming template
DEFAULT_OUTPUT_TEMPLATE = '%(title)s - %(uploader)s - %(upload_date)s.%(ext)s'