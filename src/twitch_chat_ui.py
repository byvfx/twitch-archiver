"""
UI Integration for Twitch Chat Downloader
"""

import tkinter as tk
import customtkinter as ctk
import os
import json
import threading
from typing import Dict, Optional

class TwitchChatUI:
    def __init__(self, master):
        """
        Initialize the Chat downloader UI components
        
        Args:
            master: Parent UI component (TwitchUI instance)
        """
        self.master = master
        self.api_frame = None
        self.chat_download_var = ctk.StringVar(value="0")  # 0 = off, 1 = on
        self.client_id_var = ctk.StringVar()
        self.client_secret_var = ctk.StringVar()
        self.is_configured = False
        
        # Load saved credentials if available
        self._load_credentials()
        
        # Create UI components
        self._create_api_frame()
        self._create_chat_option()
        
    def _create_api_frame(self):
        """Create the frame for Twitch API credentials"""
        # Create a button to open the API settings dialog
        self.settings_button = ctk.CTkButton(
            self.master.channel_frame,
            text="API Settings",
            fg_color="#555555",
            hover_color="#777777",
            command=self._show_api_settings
        )
        self.settings_button.pack(side="left", padx=5, pady=2)
        
    def _create_chat_option(self):
        """Create the chat download checkbox"""
        self.chat_checkbox = ctk.CTkCheckBox(
            self.master.status_frame,
            text="Download Chat",
            variable=self.chat_download_var,
            onvalue="1",
            offvalue="0"
        )
        self.chat_checkbox.pack(side="right", padx=5, pady=2)
        
    def _show_api_settings(self):
        """Show the API settings dialog"""
        # Create a toplevel window for API settings
        self.api_window = ctk.CTkToplevel(self.master)
        self.api_window.title("Twitch API Settings")
        self.api_window.geometry("500x250")
        self.api_window.transient(self.master)
        self.api_window.grab_set()
        
        # Create the content frame
        frame = ctk.CTkFrame(self.api_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add instructions
        instructions = (
            "To download chat logs, you need Twitch API credentials.\n"
            "1. Go to https://dev.twitch.tv/console/apps\n"
            "2. Register a new application\n"
            "3. Enter any name and set OAuth Redirect URL to http://localhost\n"
            "4. Get the Client ID and generate a Client Secret\n"
            "5. Enter them below"
        )
        
        ctk.CTkLabel(
            frame, 
            text=instructions,
            justify="left",
            wraplength=480
        ).pack(pady=(10, 20))
        
        # Client ID
        id_frame = ctk.CTkFrame(frame, fg_color="transparent")
        id_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(id_frame, text="Client ID:", width=100).pack(side="left", padx=5)
        
        id_entry = ctk.CTkEntry(id_frame, textvariable=self.client_id_var, width=350)
        id_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Client Secret
        secret_frame = ctk.CTkFrame(frame, fg_color="transparent")
        secret_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(secret_frame, text="Client Secret:", width=100).pack(side="left", padx=5)
        
        secret_entry = ctk.CTkEntry(secret_frame, textvariable=self.client_secret_var, width=350, show="•")
        secret_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=15)
        
        ctk.CTkButton(
            button_frame,
            text="Save",
            fg_color="#9147FF",
            hover_color="#772CE8",
            command=self._save_credentials
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#555555",
            hover_color="#777777",
            command=self.api_window.destroy
        ).pack(side="right", padx=5)
    
    def _save_credentials(self):
        """Save the API credentials"""
        client_id = self.client_id_var.get().strip()
        client_secret = self.client_secret_var.get().strip()
        
        if not client_id or not client_secret:
            self._show_error("Both Client ID and Client Secret are required.")
            return
        
        # Save credentials to a config file
        config_dir = os.path.join(os.path.expanduser("~"), ".twitch_archiver")
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, "config.json")
        config = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f)
            
            self.is_configured = True
            self.api_window.destroy()
            self.master.update_status("API credentials saved successfully.")
        except Exception as e:
            self._show_error(f"Error saving credentials: {str(e)}")
    
    def _load_credentials(self):
        """Load saved API credentials if available"""
        config_file = os.path.join(os.path.expanduser("~"), ".twitch_archiver", "config.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.client_id_var.set(config.get("client_id", ""))
                self.client_secret_var.set(config.get("client_secret", ""))
                
                # Mark as configured if both values are present
                if config.get("client_id") and config.get("client_secret"):
                    self.is_configured = True
        except Exception:
            # If there's an error loading the config, we'll just use empty values
            pass
    
    def _show_error(self, message):
        """Show an error message"""
        error_window = ctk.CTkToplevel(self.master)
        error_window.title("Error")
        error_window.geometry("400x150")
        error_window.transient(self.master)
        error_window.grab_set()
        
        ctk.CTkLabel(
            error_window,
            text=message,
            wraplength=380
        ).pack(pady=20)
        
        ctk.CTkButton(
            error_window,
            text="OK",
            command=error_window.destroy
        ).pack(pady=10)
    
    def is_chat_download_enabled(self) -> bool:
        """Check if chat download is enabled"""
        return self.is_configured and self.chat_download_var.get() == "1"
    
    def get_api_credentials(self) -> Dict[str, str]:
        """Get the API credentials"""
        return {
            "client_id": self.client_id_var.get().strip(),
            "client_secret": self.client_secret_var.get().strip()
        }