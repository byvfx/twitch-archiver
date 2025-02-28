"""
Main application file for Twitch VOD Archiver
"""

import datetime
import threading
import os
import logging

import yt_dlp
import customtkinter as ctk

from twitch_ui import TwitchUI
from ytdlp_config import FETCH_OPTS, DOWNLOAD_OPTS, DEFAULT_OUTPUT_TEMPLATE
from twitch_chat import TwitchChatRetriever, extract_video_id
from twitch_chat_ui import TwitchChatUI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("twitch_archiver.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TwitchVODArchiver")
chat_logger = logging.getLogger("TwitchChatRetriever")
chat_logger.setLevel(logging.DEBUG)  # Set chat logger to DEBUG level

class TwitchVODArchiver:
    def __init__(self):
        self.ui = TwitchUI()
        self.is_paused = False
        self.current_ydl = None
        self.download_thread = None
        self._setup_callbacks()
        # Disable pause button initially since no downloads are active
        self.ui.pause_button.configure(state="disabled")
        logger.info("Application initialized")

        self.chat_ui = TwitchChatUI(self.ui)
        self.chat_retriever = None
        logger.info("Chat UI initialized")

    def _setup_callbacks(self):
        """Set up button callbacks"""
        self.ui.fetch_button.configure(command=self.fetch_vods)
        self.ui.browse_button.configure(command=self.browse_path)
        self.ui.download_button.configure(command=self.download_selected)
        self.ui.select_all_button.configure(command=self.select_all_vods)
        self.ui.pause_button.configure(command=self.pause_downloads)

    def browse_path(self):
        """Open directory browser"""
        path = ctk.filedialog.askdirectory()
        if path:
            self.ui.path_entry.delete(0, "end")
            self.ui.path_entry.insert(0, path)
            logger.info(f"Download path set to: {path}")

    def fetch_vods(self):
        """Fetch VODs for the specified channel"""
        channel_name = self.ui.get_channel_name()
        if not channel_name:
            self.ui.update_status("Please enter a channel name")
            return

        self.ui.update_status(f"Fetching VODs for {channel_name}...")
        self.ui.fetch_button.configure(state="disabled")
        self.ui.clear_vod_list()

        thread = threading.Thread(target=self._fetch_vods_thread, args=(channel_name,))
        thread.daemon = True
        thread.start()
        logger.info(f"Started fetching VODs for channel: {channel_name}")

    def _fetch_vods_thread(self, channel_name: str):
        """Background thread for fetching VODs"""
        try:
            filter_url = self.ui.get_selected_filter()
            url = f"https://www.twitch.tv/{channel_name}/{filter_url}"
            
            logger.info(f"Fetching VODs from URL: {url}")
            ydl_opts = FETCH_OPTS.copy()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(url, download=False)
                entries = result.get('entries', [])

                for vod in entries:
                    title = vod.get('title', 'Untitled')
                    duration = vod.get('duration', 0)
                    upload_date = vod.get('upload_date', '')
                    if upload_date:
                        try:
                            upload_date = datetime.datetime.strptime(upload_date, '%Y%m%d').strftime('%Y-%m-%d')
                        except ValueError:
                            upload_date = 'Unknown date'
                    
                    self.ui.after(0, lambda t=title, d=duration, ud=upload_date, u=vod.get('url'):
                        self.ui.add_vod_checkbox(t, d, ud, u))

                self.ui.after(0, lambda: self.ui.update_status(f"Found {len(entries)} VODs"))
                logger.info(f"Found {len(entries)} VODs for {channel_name}")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error fetching VODs: {error_msg}", exc_info=True)
            self.ui.after(0, lambda: self.ui.update_status(f"Error fetching VODs: {str(error_msg)}"))
        finally:
            self.ui.after(0, lambda: self.ui.fetch_button.configure(state="normal"))

    def select_all_vods(self):
        """Select all VODs in the list"""
        for checkbox, _ in self.ui.vod_checkboxes:
            checkbox.select()
        logger.debug("Selected all VODs")

    def pause_downloads(self):
        """Toggle between pause and resume downloads"""
        if self.is_paused:
            # Resume downloads
            self.is_paused = False
            self.ui.pause_button.configure(
                text="Pause Downloads",
                fg_color="darkred",
                hover_color="#8B0000"
            )
            self.ui.update_status("Resuming downloads...")
            logger.info("Downloads resumed by user")
            
            # If we still have items in the queue, process them
            if hasattr(self.ui, 'download_queue') and self.ui.download_queue:
                self._process_download_queue()
        else:
            # Pause downloads
            self.is_paused = True
            self.ui.pause_button.configure(
                text="Resume Downloads",
                fg_color="#006400",  # Dark green
                hover_color="#008000"  # Green
            )
            self.ui.update_status("Downloads paused")
            logger.info("Downloads paused by user")

    def download_selected(self):
        """Start downloading selected VODs"""
        selected_vods = self.ui.get_selected_vods()
        if not selected_vods:
            self.ui.update_status("No VODs selected")
            return

        download_path = self.ui.get_download_path()
        if not os.path.exists(download_path):
            try:
                os.makedirs(download_path)
                logger.info(f"Created download directory: {download_path}")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error creating download directory: {error_msg}", exc_info=True)
                self.ui.update_status(f"Error creating download directory: {error_msg}")
                return

        self.ui.download_queue = getattr(self.ui, 'download_queue', [])
        self.ui.download_queue.extend(selected_vods)
        
        logger.info(f"Added {len(selected_vods)} VODs to download queue")
        
        # Reset pause state if it was paused before
        if self.is_paused:
            self.is_paused = False
            self.ui.pause_button.configure(
                text="Pause Downloads",
                fg_color="darkred",
                hover_color="#8B0000"
            )
        
        # Enable pause button when starting downloads
        self.ui.pause_button.configure(state="normal")
        
        if not self.ui.currently_downloading:
            self._process_download_queue()

    def _process_download_queue(self):
        """Process the download queue"""
        if not hasattr(self.ui, 'download_queue') or not self.ui.download_queue or self.is_paused:
            self.ui.currently_downloading = False
            self.ui.update_status("Ready" if not self.is_paused else "Downloads paused")
            # If queue is empty, disable the pause button
            if not hasattr(self.ui, 'download_queue') or not self.ui.download_queue:
                self.ui.pause_button.configure(state="disabled")
            return

        self.ui.currently_downloading = True
        checkbox, url = self.ui.download_queue.pop(0)
        
        thread = threading.Thread(target=self._download_vod_thread, args=(checkbox, url))
        thread.daemon = True
        thread.start()
        logger.info(f"Started download thread for: {checkbox.cget('text')}")

    def _download_vod_thread(self, checkbox, url):
        """Background thread for downloading a VOD"""
        vod_title = checkbox.cget('text')
        self.ui.after(0, lambda: [
            self.ui.update_status(f"Downloading: {vod_title}"),
            self.ui.show_progress_bar()
        ])
        
        download_path = self.ui.get_download_path()
        ydl_opts = DOWNLOAD_OPTS.copy()
        ydl_opts['outtmpl'] = os.path.join(download_path, DEFAULT_OUTPUT_TEMPLATE)
        
        # Define the progress hook with progress bar updates
        def progress_hook(d):
            if self.is_paused:
                raise Exception("Download paused by user")
            
            if d['status'] == 'downloading':
                # Calculate download progress
                progress = 0
                if 'total_bytes' in d and d['total_bytes'] > 0:
                    progress = d['downloaded_bytes'] / d['total_bytes']
                elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                    progress = d['downloaded_bytes'] / d['total_bytes_estimate']
                
                # Update progress bar in main thread
                self.ui.after(0, lambda: self.ui.update_progress_bar(progress))
                
                # Log progress occasionally
                if int(progress * 100) % 10 == 0:  # Log every 10%
                    logger.debug(f"Download progress for {vod_title}: {progress:.1%}")
        
        # Add the progress hook to options
        ydl_opts['progress_hooks'] = [progress_hook]
        
        try:
            logger.info(f"Starting download for: {vod_title}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.current_ydl = ydl
                self.download_thread = threading.current_thread()
                
                # Download the video
                ydl.download([url])
                logger.info(f"Successfully downloaded: {vod_title}")
                self.ui.after(0, lambda: checkbox.configure(state="disabled"))

                # Check if chat download is enabled
                if self.chat_ui.is_chat_download_enabled():
                    logger.info(f"Chat download is enabled, attempting to download chat for: {vod_title}")
                    self.ui.after(0, lambda: [
                        self.ui.update_status(f"Downloading chat for: {vod_title}"),
                        self.ui.show_progress_bar(),
                        self.ui.update_progress_bar(0)  # Reset progress bar for chat download
                    ])

                    # Extract video ID from URL
                    video_id = extract_video_id(url)
                    logger.info(f"Extracted video ID: {video_id} from URL: {url}")
                    
                    if video_id:
                        # Initialize chat retriever if needed
                        if not self.chat_retriever:
                            credentials = self.chat_ui.get_api_credentials()
                            logger.info(f"Initializing chat retriever with client ID: [REDACTED]")
                            
                            # Ensure we have valid credentials
                            if not credentials['client_id'] or not credentials['client_secret']:
                                logger.error("Missing API credentials")
                                self.ui.after(0, lambda: self.ui.update_status("Error: Missing API credentials"))
                                return
                                
                            self.chat_retriever = TwitchChatRetriever(
                                client_id=credentials["client_id"],
                                client_secret=credentials["client_secret"]
                            )
                        
                        # Make callback to update chat download progress
                        def chat_progress_callback(progress):
                            self.ui.after(0, lambda: self.ui.update_progress_bar(progress))
                            if progress % 0.1 < 0.01:  # Log every ~10%
                                logger.debug(f"Chat download progress: {progress:.1%}")

                        # Download chat to same directory as VOD
                        logger.info(f"Starting chat download for video ID {video_id}")
                        success = self.chat_retriever.download_chat(
                            video_id, 
                            download_path,
                            progress_callback=chat_progress_callback
                        )
                        
                        if success:
                            logger.info(f"Chat downloaded successfully for: {vod_title}")
                            self.ui.after(0, lambda: self.ui.update_status(f"Chat downloaded successfully"))
                        else:
                            logger.error(f"Error downloading chat for: {vod_title}")
                            self.ui.after(0, lambda: self.ui.update_status(f"Error downloading chat"))
                    else:
                        logger.warning(f"Could not extract video ID from URL: {url}")
                        self.ui.after(0, lambda: self.ui.update_status("Could not extract video ID for chat download"))
                else:
                    logger.info(f"Chat download is disabled or not configured properly")

        except Exception as e:
            error_msg = str(e)
            if "paused" in error_msg.lower():
                logger.info(f"Download paused for: {vod_title}")
                self.ui.after(0, lambda: self.ui.update_status("Download paused"))
            else:
                logger.error(f"Error downloading {vod_title}: {error_msg}", exc_info=True)
                self.ui.after(0, lambda: self.ui.update_status(f"Error downloading: {error_msg}"))
        finally:
            # Clean up after download
            self.ui.after(0, lambda: self._cleanup_download_state(vod_title))

    def _cleanup_download_state(self, vod_title=None):
        """Clean up the download state and process the next item in queue"""
        self.current_ydl = None
        self.download_thread = None
        
        self.ui.currently_downloading = False
        self.ui.download_button.configure(state="normal")
        self.ui.hide_progress_bar()
        
        if vod_title:
            logger.debug(f"Cleaned up after download: {vod_title}")
            
        # Process next in queue if not paused
        if not self.is_paused and hasattr(self.ui, 'download_queue') and self.ui.download_queue:
            self._process_download_queue()
        else:
            self.ui.update_status("Ready" if not self.is_paused else "Downloads paused")
            # If queue is empty or we're done, disable the pause button
            if not hasattr(self.ui, 'download_queue') or not self.ui.download_queue:
                self.ui.pause_button.configure(state="disabled")
            
    def run(self):
        """Start the application"""
        logger.info("Starting application")
        self.ui.mainloop()

if __name__ == "__main__":
    app = TwitchVODArchiver()
    app.run()