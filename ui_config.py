"""
UI Configuration file for Twitch VOD Archiver
Contains all UI-related constants and theme settings
"""

# Window settings
WINDOW_SIZE = "800x600"
WINDOW_TITLE = "Twitch VOD Archiver"

# Twitch theme colors
COLORS = {
    "BUTTON": "#9147FF",         # Twitch purple
    "BUTTON_HOVER": "#772CE8",   # Darker Twitch purple
    "ACTIVE": "#9147FF",         # Twitch teal accent
    "ACTIVE_HOVER": "#772CE8",   # Darker teal
    "BACKGROUND": "#0E0E10",     # Twitch dark background
    "FRAME": "#18181B",          # Twitch darker gray
}

# Padding and spacing
PADDING = {
    "FRAME": {"padx": 10, "pady": 5},
    "WIDGET": {"padx": 5, "pady": 2},
}

# Widget dimensions
DIMENSIONS = {
    "CHANNEL_ENTRY_WIDTH": 200,
    "PATH_ENTRY_WIDTH": 300,
    "VOD_LIST_HEIGHT": 300,
}

# Text content
LABELS = {
    "CHANNEL": "Channel Name:",
    "PATH": "Download Path:",
    "FETCH": "Fetch VODs",
    "BROWSE": "Browse",
    "DOWNLOAD": "Download Selected",
    "SELECT_ALL": "Select All",
    "READY": "Ready",
    "CANCEL": "Cancel Downloads",
}

