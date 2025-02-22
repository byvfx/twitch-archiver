# Twitch VOD Archiver

A desktop application for downloading Twitch VODs (Video on Demand) with a user-friendly interface.
## Screenshots
![UI Screenshot](/img/ui_ss.png)

## Features

- Clean and modern dark theme UI matching Twitch's style
- Fetch VODs from any Twitch channel
- Select multiple VODs for batch downloading
- Download progress tracking
- Cancel in-progress downloads - broken at the moment
- Customizable download location
- Quick access to download folder

## Requirements

- Python 3.7+
- Required packages:
  - customtkinter
  - yt-dlp

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install customtkinter yt-dlp
```

## Usage

1. Run the application:
```bash
python twitch_local_archiver.py
```

2. Enter a Twitch channel name
3. Click "Fetch VODs" to list available videos
4. Select the VODs you want to download
5. Choose download location (defaults to Downloads folder)
6. Click "Download Selected" to start downloading

## Controls

- **Fetch VODs**: Retrieves the list of available VODs for the specified channel
- **Browse**: Select download location
- **Explore**: Opens the current download folder
- **Select All**: Selects all VODs in the list
- **Download Selected**: Starts downloading selected VODs
- **Cancel Downloads**: Stops current and queued downloads

## Notes

- Downloads are processed sequentially to avoid overwhelming the network
- VODs are saved in their best available quality will
- Downloaded VODs are marked as disabled in the UI
- The application preserves original video titles and dates

## TODO
- [ ] Add support for downloading clips
- [ ] Add support for capturing chat logs
- [ ] Cancel individual downloads
