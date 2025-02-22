import customtkinter as ctk
import yt_dlp
import os
import re
from typing import List
import threading
from datetime import datetime

class TwitchVODArchiver(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Twitch VOD Archiver")
        self.geometry("800x600")
        
        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Give more weight to the VOD list

        # Channel input frame
        self.channel_frame = ctk.CTkFrame(self)
        self.channel_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        self.channel_label = ctk.CTkLabel(self.channel_frame, text="Channel Name:")
        self.channel_label.pack(side="left", padx=5)
        
        self.channel_entry = ctk.CTkEntry(self.channel_frame, width=200)
        self.channel_entry.pack(side="left", padx=5)
        
        self.fetch_button = ctk.CTkButton(self.channel_frame, text="Fetch VODs", command=self.fetch_vods)
        self.fetch_button.pack(side="left", padx=5)

        # Download path frame
        self.path_frame = ctk.CTkFrame(self)
        self.path_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.path_label = ctk.CTkLabel(self.path_frame, text="Download Path:")
        self.path_label.pack(side="left", padx=5)
        
        self.path_entry = ctk.CTkEntry(self.path_frame, width=300)
        self.path_entry.pack(side="left", padx=5)
        self.path_entry.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
        
        self.browse_button = ctk.CTkButton(self.path_frame, text="Browse", command=self.browse_path)
        self.browse_button.pack(side="left", padx=5)

        # VOD list frame
        self.vod_frame = ctk.CTkFrame(self)
        self.vod_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        self.vod_scrollable_frame = ctk.CTkScrollableFrame(self.vod_frame, height=300)
        self.vod_scrollable_frame.pack(fill="both", expand=True)
        
        self.vod_checkboxes = []

        # Status and control frame
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready")
        self.status_label.pack(side="left", padx=5)
        
        self.download_button = ctk.CTkButton(self.status_frame, text="Download Selected", command=self.download_selected)
        self.download_button.pack(side="right", padx=5)
        
        self.select_all_button = ctk.CTkButton(self.status_frame, text="Select All", command=self.select_all_vods)
        self.select_all_button.pack(side="right", padx=5)

        # Download queue
        self.download_queue = []
        self.currently_downloading = False

    def browse_path(self):
        path = ctk.filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, path)

    def fetch_vods(self):
        channel_name = self.channel_entry.get().strip()
        if not channel_name:
            self.update_status("Please enter a channel name")
            return

        self.update_status(f"Fetching VODs for {channel_name}...")
        self.fetch_button.configure(state="disabled")
        
        # Clear existing VODs
        for checkbox in self.vod_checkboxes:
            checkbox.destroy()
        self.vod_checkboxes.clear()

        # Start fetching in a separate thread
        thread = threading.Thread(target=self._fetch_vods_thread, args=(channel_name,))
        thread.daemon = True
        thread.start()

    def _fetch_vods_thread(self, channel_name: str):
        try:
            url = f"https://www.twitch.tv/{channel_name}/videos?filter=all&sort=time"
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'force_generic_extractor': True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(url, download=False)
                entries = result.get('entries', [])

                self.after(0, lambda: self._populate_vod_list(entries))
                self.after(0, lambda: self.update_status(f"Found {len(entries)} VODs"))
        except Exception as e:
            self.after(0, lambda: self.update_status(f"Error fetching VODs: {str(e)}"))
        finally:
            self.after(0, lambda: self.fetch_button.configure(state="normal"))

    def _populate_vod_list(self, vods: List[dict]):
        for vod in vods:
            title = vod.get('title', 'Untitled')
            duration = vod.get('duration', 0)
            upload_date = vod.get('upload_date', '')
            
            if upload_date:
                upload_date = datetime.strptime(upload_date, '%Y%m%d').strftime('%Y-%m-%d')
            
            checkbox_text = f"{title} ({duration}s) - {upload_date}"
            var = ctk.StringVar()
            checkbox = ctk.CTkCheckBox(self.vod_scrollable_frame, text=checkbox_text, variable=var)
            checkbox.pack(anchor="w", padx=5, pady=2)
            self.vod_checkboxes.append((checkbox, vod.get('url')))

    def select_all_vods(self):
        for checkbox, _ in self.vod_checkboxes:
            checkbox.select()

    def download_selected(self):
        selected_vods = [(cb, url) for cb, url in self.vod_checkboxes if cb.get()]
        if not selected_vods:
            self.update_status("No VODs selected")
            return

        download_path = self.path_entry.get()
        if not os.path.exists(download_path):
            try:
                os.makedirs(download_path)
            except Exception as e:
                self.update_status(f"Error creating download directory: {str(e)}")
                return

        # Add selected VODs to queue
        self.download_queue.extend(selected_vods)
        
        # Start download process if not already running
        if not self.currently_downloading:
            self._process_download_queue()

    def _process_download_queue(self):
        if not self.download_queue:
            self.currently_downloading = False
            self.update_status("All downloads completed")
            return

        self.currently_downloading = True
        checkbox, url = self.download_queue.pop(0)
        
        # Start download in separate thread
        thread = threading.Thread(target=self._download_vod_thread, args=(checkbox, url))
        thread.daemon = True
        thread.start()

    def _download_vod_thread(self, checkbox, url):
        try:
            self.after(0, lambda: self.update_status(f"Downloading: {checkbox.cget('text')}"))
            
            ydl_opts = {
                'outtmpl': os.path.join(self.path_entry.get(), '%(title)s-%(id)s.%(ext)s'),
                'format': 'best',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.after(0, lambda: checkbox.configure(state="disabled"))
        except Exception as e:
            self.after(0, lambda: self.update_status(f"Error downloading VOD: {str(e)}"))
        finally:
            # Process next download in queue
            self.after(0, self._process_download_queue)

    def update_status(self, message: str):
        self.status_label.configure(text=message)

if __name__ == "__main__":
    app = TwitchVODArchiver()
    app.mainloop()