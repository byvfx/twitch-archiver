# Twitch VOD Archiver

A desktop application for downloading Twitch VODs (Video on Demand) with a user-friendly interface.

## Screenshots

![UI Screenshot](/img/ui_ss.png)

## Features

- Clean and modern dark theme UI matching Twitch's style
- Fetch VODs from any Twitch channel thats public or you are subscribed to
- Select multiple VODs for batch downloading
- Download progress tracking
- Pause and resume in-progress downloads
- Customizable download location
- Quick access to download folder
- Captures original video titles and dates
- Supports downloading clips, highlights, collections
- Supports downloading chat logs

## Requirements

- Python 3.7+
- Required packages:
  see requirements.txt

## Installation

1. Clone the repository
  
   ```bash
   git clone https://github.com/byvfx/twitch-archiver.git
   ```

2. Install dependencies using pip:

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
1. Optionally, click "Pause Download" to pause the download, and click "Resume Download" to resume the download
2. API settings button will open a new window with instructions on how to get the API key

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
- **Resume Download**: Resumes paused downloads
- **API Key**: Enter your Twitch API key (only needed for downloading chat logs)

## Notes

- Downloads are processed sequentially to avoid overwhelming the network ( might add the option to download multiple at once in the future)
- The application uses the Twitch API to fetch VODs, which requires an API key
- Different filter types access different kinds of content:
  - All Videos typically contains past broadcasts (stored for 14-60 days depending on user level)
  - Highlights are permanently stored stream segments marked by the streamer
  - Uploads are non-stream videos uploaded directly to the channel
  - Collections are curated playlists of videos
  - Clips can be filtered by time range (24h, 7d, 30d, or all time)
- VODs are saved in their best available quality
- Downloaded VODs are marked as disabled in the UI
- The application preserves original video titles and dates
- After the download is complete, the VODs are automatically converted to MP4 format using yt-dlp which seems to take a while to convert so be patient, i am looking into this.
- Chat logs are saved in a separate file with the same name as the video
- The API key is only needed for downloading chat logs, and can be obtained from the Twitch Developer Dashboard, i put insructions on how to get the API key in the application itself.
- The application saves the API key in a file called `config.json` in the user's home directory. I made a button to explore to the location or print it out in the UI.
- Currently looking into encrypt the API key in the config file for future releases.

## TODO

- [x] Add support for downloading clips, highlights, collections
- [x] Add support for capturing chat logs
- [x] Add download progress bar - in the current version, not the release
- [ ] Add support for downloading VODs from specific dates
- [ ] Speed up encoding from the yt-dlp output
- [ ] Add encryption for the API key in the config file
- [ ] Add quality options for downloads
