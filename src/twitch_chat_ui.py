"""
UI Integration for Twitch Chat Downloader
"""

import customtkinter as ctk
import os
import json
import logging
import requests
from typing import Dict
import webbrowser
import subprocess

logger = logging.getLogger("TwitchChatUI")

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
        self.api_status_label = None
        
        # Load saved credentials if available
        self._load_credentials()
        
        # Create UI components
        self._create_api_frame()
        self._create_chat_option()
        
        logger.info("TwitchChatUI initialized")
        
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
        self.api_window.geometry("600x380")  # Made window taller to accommodate status text and file location
        self.api_window.transient(self.master)
        self.api_window.grab_set()
        
        # Create the content frame
        frame = ctk.CTkFrame(self.api_window)
        frame.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Add first part of instructions
        ctk.CTkLabel(
            frame, 
            text="To download chat logs, you need Twitch API credentials.",
            justify="left",
            wraplength=480
        ).pack(pady=(10, 2))
        
        # First instruction with link
        instructions_frame = ctk.CTkFrame(frame, fg_color="transparent")
        instructions_frame.pack(fill="x", pady=(0, 20))

        # Create hyperlink as a button
        link = "https://dev.twitch.tv/console/apps"
        link_button = ctk.CTkButton(
            instructions_frame,
            text="1. Go to Twitch Developer Console",
            fg_color="#9147FF",  # Twitch purple
            hover_color="#772CE8",
            command=lambda: self._open_link(link),
            width=350
        )
        link_button.pack(fill="x", padx=10, pady=5)

        # Continue with the rest of the instructions
        instructions2 = (
            "2. Register a new application\n"
            "3. Enter any name and set OAuth Redirect URL to http://localhost\n"
            "4. Select Confidential for the Client Type\n"
            "5. Get the Client ID and generate a Client Secret\n"
            "6. Enter them below"
        )
        
        ctk.CTkLabel(
            instructions_frame, 
            text=instructions2,
            justify="left",
            wraplength=480
        ).pack(anchor="w", padx=10, pady=2)
        
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
        
        # File location info
        file_location_frame = ctk.CTkFrame(frame, fg_color="transparent")
        file_location_frame.pack(fill="x", pady=5)
        
        config_file = os.path.join(os.path.expanduser("~"), ".twitch_archiver", "config.json")
        
        ctk.CTkLabel(
            file_location_frame, 
            text="Credentials File:", 
            width=100
        ).pack(side="left", padx=5)
        
        show_location_btn = ctk.CTkButton(
            file_location_frame,
            text="Show Location",
            width=100,
            height=28,
            fg_color="#555555",
            hover_color="#777777",
            command=lambda: self._update_api_status(f"Credentials stored at: {config_file}", "#4CAF50")
        )
        show_location_btn.pack(side="left", padx=5)
        
        open_folder_btn = ctk.CTkButton(
            file_location_frame,
            text="Open Folder",
            width=100,
            height=28,
            fg_color="#555555",
            hover_color="#777777",
            command=lambda: self._open_config_folder()
        )
        open_folder_btn.pack(side="left", padx=5)
        
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
        
        # Add status label at bottom
        status_frame = ctk.CTkFrame(frame, fg_color="transparent", height=30)
        status_frame.pack(fill="x", side="bottom", padx=10, pady=5)
        
        self.api_status_label = ctk.CTkLabel(
            status_frame, 
            text="Enter your Twitch API credentials to enable chat downloading",
            text_color="#999999",
            height=20,
            font=("", 12)
        )
        self.api_status_label.pack(fill="x")
        
        # Show status of current configuration
        if self.is_configured:
            self._update_api_status("API credentials are configured and ready to use", "#4CAF50")
        
    def _update_api_status(self, message, color="#999999"):
        """Update the status text in the API settings window"""
        if self.api_status_label:
            self.api_status_label.configure(text=message, text_color=color)
            self.api_status_label.update()
        
    def _open_link(self, url):
        """Open a link in the default web browser"""
        webbrowser.open_new(url)
    
    def _save_credentials(self):
        """Save the API credentials"""
        client_id = self.client_id_var.get().strip()
        client_secret = self.client_secret_var.get().strip()
        
        if not client_id or not client_secret:
            self._show_error("Both Client ID and Client Secret are required.")
            return
        
        # Verify the credentials by attempting to get an access token
        try:
            self._update_api_status("Verifying credentials with Twitch API...", "#FFA500")
            
            auth_url = "https://id.twitch.tv/oauth2/token"
            params = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials"
            }
            
            self.master.update_status("Verifying API credentials...")
            response = requests.post(auth_url, params=params)
            
            if response.status_code != 200:
                self._update_api_status("Invalid credentials. Please check your Client ID and Secret.", "#FF0000")
                self._show_error("Invalid credentials. Please check your Client ID and Secret.")
                logger.error(f"API credential verification failed: {response.status_code}")
                return
                
            logger.info("API credentials verified successfully")
            self._update_api_status("Credentials verified successfully! Saving...", "#4CAF50")
                
        except Exception as e:
            self._update_api_status(f"Error: {str(e)}", "#FF0000")
            self._show_error(f"Error verifying credentials: {str(e)}")
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
            self._update_api_status("Credentials saved successfully!", "#4CAF50")
            self.master.after(1000, self.api_window.destroy)  # Close after 1 second
            self.master.update_status("API credentials verified and saved successfully.")
        except Exception as e:
            self._update_api_status(f"Error saving: {str(e)}", "#FF0000")
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
        # Only enable if configured and checkbox is checked
        enabled = self.chat_download_var.get() == "1"
        configured = self.is_configured
        
        logger.info(f"Chat download enabled: {enabled}, configured: {configured}")
        
        if enabled and not configured:
            logger.warning("Chat download requested but API not configured")
            self._show_error("API credentials must be configured first. Click 'API Settings' to set them up.")
            self.chat_download_var.set("0")
            return False
            
        return enabled and configured

    def get_api_credentials(self) -> Dict[str, str]:
        """Get the API credentials"""
        credentials = {
            "client_id": self.client_id_var.get().strip(),
            "client_secret": self.client_secret_var.get().strip()
        }
        
        # Check if credentials are valid
        if not credentials["client_id"] or not credentials["client_secret"]:
            logger.warning("Attempting to get empty API credentials")
            
        return credentials

    def _open_config_folder(self):
        """Open the folder containing the config file"""
        config_dir = os.path.join(os.path.expanduser("~"), ".twitch_archiver")
        
        # Create directory if it doesn't exist
        os.makedirs(config_dir, exist_ok=True)
        
        # Open the directory using the appropriate method for the OS
        try:
            if os.name == 'nt':  # Windows
                os.startfile(config_dir)
            elif os.name == 'posix':  # macOS or Linux
                if 'darwin' in os.sys.platform:  # macOS
                    subprocess.Popen(['open', config_dir])
                else:  # Linux
                    subprocess.Popen(['xdg-open', config_dir])
                    
            self._update_api_status(f"Opened folder: {config_dir}", "#4CAF50")
        except Exception as e:
            logger.error(f"Error opening config folder: {e}")
            self._update_api_status(f"Error opening folder: {str(e)}", "#FF0000")