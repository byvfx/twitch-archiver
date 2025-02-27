"""
UI Implementation for Twitch VOD Archiver
"""

import customtkinter as ctk
from ui_config import COLORS, PADDING, DIMENSIONS, LABELS, WINDOW_SIZE, WINDOW_TITLE, VIDEO_FILTERS, CLIP_RANGES
import os

class TwitchUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        
        # Initialize variables first
        self.vod_checkboxes = []
        self.download_queue = []
        self.currently_downloading = False
        self.filter_var = ctk.StringVar()
        self.clip_range_var = ctk.StringVar()
        
        # Set default values
        self.filter_var.set("All Videos")
        self.clip_range_var.set("All Time")
        
        # Setup UI
        self._setup_theme()
        self._setup_grid()
        self._create_widgets()

    def _setup_theme(self):
        """Configure the application theme"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=COLORS["BACKGROUND"])

    def _setup_grid(self):
        """Configure the grid layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

    def _create_widgets(self):
        """Create all UI widgets"""
        self._create_channel_frame()
        self._create_path_frame()
        self._create_vod_frame()
        self._create_status_frame()

    def _create_channel_frame(self):
        """Create the channel input frame"""
        self.channel_frame = ctk.CTkFrame(self, fg_color=COLORS["FRAME"])
        self.channel_frame.grid(row=0, column=0, **PADDING["FRAME"], sticky="ew")
        
        # Channel input
        channel_input = ctk.CTkFrame(self.channel_frame, fg_color="transparent")
        channel_input.pack(side="left", **PADDING["WIDGET"], fill="x", expand=True)
        
        ctk.CTkLabel(channel_input, text=LABELS["CHANNEL"]).pack(side="left", **PADDING["WIDGET"])
        self.channel_entry = ctk.CTkEntry(channel_input, width=DIMENSIONS["CHANNEL_ENTRY_WIDTH"])
        self.channel_entry.pack(side="left", **PADDING["WIDGET"])
        
        # Filter options
        filter_frame = ctk.CTkFrame(self.channel_frame, fg_color="transparent")
        filter_frame.pack(side="left", **PADDING["WIDGET"])
        
        ctk.CTkLabel(filter_frame, text=LABELS["FILTER_TYPE"]).pack(side="left", **PADDING["WIDGET"])
        self.filter_dropdown = ctk.CTkOptionMenu(
            filter_frame,
            values=list(VIDEO_FILTERS.keys()),
            variable=self.filter_var,
            fg_color=COLORS["BUTTON"],
            button_color=COLORS["BUTTON"],
            button_hover_color=COLORS["BUTTON_HOVER"]
        )
        self.filter_dropdown.pack(side="left", **PADDING["WIDGET"])
        
        self.clip_range_dropdown = ctk.CTkOptionMenu(
            filter_frame,
            values=list(CLIP_RANGES.keys()),
            variable=self.clip_range_var,
            fg_color=COLORS["BUTTON"],
            button_color=COLORS["BUTTON"],
            button_hover_color=COLORS["BUTTON_HOVER"]
        )
        self.clip_range_dropdown.pack(side="left", **PADDING["WIDGET"])
        
        # Initially hide clip range dropdown
        self.clip_range_dropdown.pack_forget()
        
        # Bind filter change event
        self.filter_var.trace_add("write", self._on_filter_change)
        
        self.fetch_button = ctk.CTkButton(
            self.channel_frame,
            text=LABELS["FETCH"],
            fg_color=COLORS["BUTTON"],
            hover_color=COLORS["BUTTON_HOVER"]
        )
        self.fetch_button.pack(side="left", **PADDING["WIDGET"])

    def _create_path_frame(self):
        """Create the download path frame"""
        self.path_frame = ctk.CTkFrame(self, fg_color=COLORS["FRAME"])
        self.path_frame.grid(row=1, column=0, **PADDING["FRAME"], sticky="ew")
        
        ctk.CTkLabel(self.path_frame, text=LABELS["PATH"]).pack(side="left", **PADDING["WIDGET"])
        
        self.path_entry = ctk.CTkEntry(
            self.path_frame,
            width=DIMENSIONS["PATH_ENTRY_WIDTH"]
        )
        self.path_entry.pack(side="left", **PADDING["WIDGET"])
        self.path_entry.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
        
        self.browse_button = ctk.CTkButton(
            self.path_frame,
            text=LABELS["BROWSE"],
            fg_color=COLORS["BUTTON"],
            hover_color=COLORS["BUTTON_HOVER"]
        )
        self.browse_button.pack(side="left", **PADDING["WIDGET"])

        self.explore_button = ctk.CTkButton(
            self.path_frame,
            text="Explore",
            fg_color=COLORS["BUTTON"],
            hover_color=COLORS["BUTTON_HOVER"],
            command=lambda: os.startfile(self.path_entry.get())
        )
        self.explore_button.pack(side="left", **PADDING["WIDGET"])

    def _create_vod_frame(self):
        """Create the VOD list frame"""
        self.vod_frame = ctk.CTkFrame(self, fg_color=COLORS["FRAME"])
        self.vod_frame.grid(row=2, column=0, **PADDING["FRAME"], sticky="nsew")
        
        self.vod_scrollable_frame = ctk.CTkScrollableFrame(
            self.vod_frame,
            height=DIMENSIONS["VOD_LIST_HEIGHT"]
        )
        self.vod_scrollable_frame.pack(fill="both", expand=True)

    def _create_status_frame(self):
        """Create the status and control frame"""
        self.status_frame = ctk.CTkFrame(self, fg_color=COLORS["FRAME"])
        self.status_frame.grid(row=3, column=0, **PADDING["FRAME"], sticky="ew")
        
        # Add a container for status label and progress bar
        status_container = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        status_container.pack(side="left", fill="both", expand=True, **PADDING["WIDGET"])
        
        self.status_label = ctk.CTkLabel(status_container, text=LABELS["READY"])
        self.status_label.pack(side="top", anchor="w", **PADDING["WIDGET"])
        
        # Add progress bar (initially hidden)
        self.progress_bar = ctk.CTkProgressBar(status_container, width=400)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="top", fill="x", **PADDING["WIDGET"])
        self.progress_bar.pack_forget()  # Hide initially
        
        self.pause_button = ctk.CTkButton(
            self.status_frame,
            text=LABELS["PAUSE"],
            fg_color="darkred",
            hover_color="#8B0000"
        )
        self.pause_button.pack(side="right", **PADDING["WIDGET"])
        
        self.download_button = ctk.CTkButton(
            self.status_frame,
            text=LABELS["DOWNLOAD"],
            fg_color=COLORS["ACTIVE"],
            hover_color=COLORS["ACTIVE_HOVER"]
        )
        self.download_button.pack(side="right", **PADDING["WIDGET"])
        
        self.select_all_button = ctk.CTkButton(
            self.status_frame,
            text=LABELS["SELECT_ALL"],
            fg_color=COLORS["BUTTON"],
            hover_color=COLORS["BUTTON_HOVER"]
        )
        self.select_all_button.pack(side="right", **PADDING["WIDGET"])

    def add_vod_checkbox(self, title, duration, upload_date, url):
        """Add a VOD checkbox to the list"""
        checkbox_text = f"{title} ({duration}s) - {upload_date}"
        var = ctk.StringVar()
        checkbox = ctk.CTkCheckBox(self.vod_scrollable_frame, text=checkbox_text, variable=var)
        checkbox.pack(anchor="w", **PADDING["WIDGET"])
        self.vod_checkboxes.append((checkbox, url))

    def clear_vod_list(self):
        """Clear all VODs from the list"""
        for checkbox, _ in self.vod_checkboxes:
            checkbox.destroy()
        self.vod_checkboxes.clear()

    def update_status(self, message: str):
        """Update the status label"""
        self.status_label.configure(text=message)

    def get_channel_name(self) -> str:
        """Get the entered channel name"""
        return self.channel_entry.get().strip()

    def get_download_path(self) -> str:
        """Get the selected download path"""
        return self.path_entry.get()

    def get_selected_vods(self):
        """Get list of selected VODs"""
        return [(cb, url) for cb, url in self.vod_checkboxes if cb.get()]

    def _on_filter_change(self, *args):
        """Show/hide clip range dropdown based on filter selection"""
        if self.filter_var.get() == "Clips":
            self.clip_range_dropdown.pack(side="left", **PADDING["WIDGET"])
        else:
            self.clip_range_dropdown.pack_forget()

    def get_selected_filter(self):
        """Get the currently selected filter URL"""
        filter_type = self.filter_var.get()
        if (filter_type == "Clips"):
            range_value = CLIP_RANGES[self.clip_range_var.get()]
            return f"clips?filter=clips&range={range_value}"
        return VIDEO_FILTERS[filter_type]

    def show_progress_bar(self):
        """Show the progress bar and reset it to 0"""
        self.progress_bar.set(0)
        self.progress_bar.pack(side="top", fill="x", **PADDING["WIDGET"])

    def hide_progress_bar(self):
        """Hide the progress bar"""
        self.progress_bar.pack_forget()

    def update_progress_bar(self, progress):
        """Update the progress bar value (0-1)"""
        self.progress_bar.set(progress)