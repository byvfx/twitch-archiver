"""
Main application file for Twitch VOD Archiver
"""

import datetime
import threading
import os
import yt_dlp
from twitch_ui import TwitchUI

class TwitchVODArchiver:
    def __init__(self):
        self.ui = TwitchUI()
        self._setup_callbacks()

    def _setup_callbacks(self):
        """Set up button callbacks"""
        self.ui.fetch_button.configure(command=self.fetch_vods)
        self.ui.browse_button.configure(command=self.browse_path)
        self.ui.download_button.configure(command=self.download_selected)
        self.ui.select_all_button.configure(command=self.select_all_vods)

    def browse_path(self):
        """Open directory browser"""
        path = ctk.filedialog.askdirectory()
        if path:
            self.ui.path_entry.delete(0, "end")
            self.ui.path_entry.insert(0, path)

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

    def _fetch_vods_thread(self, channel_name: str):
        """Background thread for fetching VODs"""
        try:
            url = f"https://www.twitch.tv/{channel_name}/videos?filter=archives"
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'force_generic_extractor': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(url, download=False)
                entries = result.get('entries', [])

                for vod in entries:
                    title = vod.get('title', 'Untitled')
                    duration = vod.get('duration', 0)
                    upload_date = vod.get('upload_date', '')
                    if upload_date:
                        upload_date = datetime.strptime(upload_date, '%Y%m%d').strftime('%Y-%m-%d')
                    
                    self.ui.after(0, lambda t=title, d=duration, ud=upload_date, u=vod.get('url'):
                        self.ui.add_vod_checkbox(t, d, ud, u))

                self.ui.after(0, lambda: self.ui.update_status(f"Found {len(entries)} VODs"))
        except Exception as e:
            self.ui.after(0, lambda: self.ui.update_status(f"Error fetching VODs: {str(e)}"))
        finally:
            self.ui.after(0, lambda: self.ui.fetch_button.configure(state="normal"))

    def select_all_vods(self):
        """Select all VODs in the list"""
        for checkbox, _ in self.ui.vod_checkboxes:
            checkbox.select()

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
            except Exception as e:
                self.ui.update_status(f"Error creating download directory: {str(e)}")
                return

        self.ui.download_queue.extend(selected_vods)
        
        if not self.ui.currently_downloading:
            self._process_download_queue()

    def _process_download_queue(self):
        """Process the download queue"""
        if not self.ui.download_queue:
            self.ui.currently_downloading = False
            self.ui.update_status("All downloads completed")
            return

        self.ui.currently_downloading = True
        checkbox, url = self.ui.download_queue.pop(0)
        
        thread = threading.Thread(target=self._download_vod_thread, args=(checkbox, url))
        thread.daemon = True
        thread.start()

    def _download_vod_thread(self, checkbox, url):
        """Background thread for downloading a VOD"""
        try:
            self.ui.after(0, lambda: self.ui.update_status(f"Downloading: {checkbox.cget('text')}"))
            
            ydl_opts = {
                'outtmpl': os.path.join(self.ui.get_download_path(), '%(title)s-%(id)s.%(ext)s'),
                'format': 'best',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.ui.after(0, lambda: checkbox.configure(state="disabled"))
        except Exception as e:
            self.ui.after(0, lambda: self.ui.update_status(f"Error downloading VOD: {str(e)}"))
        finally:
            self.ui.after(0, self._process_download_queue)

    def run(self):
        """Start the application"""
        self.ui.mainloop()

if __name__ == "__main__":
    app = TwitchVODArchiver()
    app.run()