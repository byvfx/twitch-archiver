# Twitch VOD Archiver

A desktop application for downloading Twitch VODs (Video on Demand) with a user-friendly interface.

## Screenshots

![UI Screenshot](/img/ui_ss.png)

## Features

- Clean and modern dark theme UI matching Twitch's style
- Fetch VODs from any Twitch channel
- Select multiple VODs for batch downloading
- Download progress tracking
- Pause in-progress downloads
- Customizable download location
- Quick access to download folder

## Requirements

- Python 3.7+
- Required packages:
  - customtkinter
  - yt-dlp

## Installation

1. Clone the repository
2. Install dependencies using one of these methods:

   Using pip directly:

   ```bash
   pip install customtkinter yt-dlp
   ```

   Using requirements.txt:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:

```bash
python main.py
```

1. Enter a Twitch channel name
1. Click "Fetch VODs" to list available videos
1. Select the VODs you want to download
1. Choose download location (defaults to Downloads folder)
1. Click "Download Selected" to start downloading

## Controls

- **Fetch VODs**: Retrieves the list of available VODs for the specified channel
- **Filter Type**: Choose between different content types:
  - All Videos: Shows all recorded streams and uploads
  - Highlights: Shows only highlighted stream segments
  - Uploads: Shows only manually uploaded videos
  - Collections: Shows video collections/playlists
  - Clips: Shows channel clips (with time range options)
- **Browse**: Select download location
- **Explore**: Opens the current download folder
- **Select All**: Selects all VODs in the list
- **Download Selected**: Starts downloading selected VODs
- **Pause Download**: Pauses current and queued downloads

## Notes

- Downloads are processed sequentially to avoid overwhelming the network
- Different filter types access different kinds of content:
  - All Videos typically contains past broadcasts (stored for 14-60 days depending on user level)
  - Highlights are permanently stored stream segments marked by the streamer
  - Uploads are non-stream videos uploaded directly to the channel
  - Collections are curated playlists of videos
  - Clips can be filtered by time range (24h, 7d, 30d, or all time)
- VODs are saved in their best available quality
- Downloaded VODs are marked as disabled in the UI
- The application preserves original video titles and dates

## TODO

- [x] Add support for downloading clips, highlights, collections
- [ ] Add support for capturing chat logs
- [ ] Cancel individual downloads turns out yt-dlp doesn't support a native call to cancel a download
- [x] Add download progress bar - in the current version, not the release
