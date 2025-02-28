"""
Twitch Chat Retriever Module for Twitch VOD Archiver
"""

import os
import json
import time
import logging
import requests
import datetime
import threading
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("TwitchChatRetriever")

class TwitchChatRetriever:
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize the Twitch Chat Retriever
        
        Args:
            client_id: Your Twitch API Client ID
            client_secret: Your Twitch API Client Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = 0
        self.base_url = "https://api.twitch.tv/helix"
        
    def authenticate(self) -> bool:
        """
        Authenticate with Twitch API and get access token
        
        Returns:
            bool: True if authentication was successful
        """
        # Check if we already have a valid token
        if self.access_token and time.time() < self.token_expiry:
            return True
            
        try:
            auth_url = "https://id.twitch.tv/oauth2/token"
            params = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
            
            response = requests.post(auth_url, params=params)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                # Set expiry with a small buffer before actual expiry
                self.token_expiry = time.time() + data["expires_in"] - 100
                logger.info("Successfully authenticated with Twitch API")
                return True
            else:
                logger.error(f"Failed to authenticate: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return False
    
    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """
        Get video information from Twitch API
        
        Args:
            video_id: Twitch video ID (numeric part only)
            
        Returns:
            dict: Video information or None if not found
        """
        if not self.authenticate():
            return None
            
        try:
            # Remove "v" prefix if present
            if video_id.startswith("v"):
                video_id = video_id[1:]
                
            url = f"{self.base_url}/videos"
            headers = {
                "Client-ID": self.client_id,
                "Authorization": f"Bearer {self.access_token}"
            }
            params = {"id": video_id}
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data["data"]:
                    return data["data"][0]
                else:
                    logger.warning(f"Video not found: {video_id}")
                    return None
            else:
                logger.error(f"Failed to get video info: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}", exc_info=True)
            return None
    
    def download_chat(self, video_id: str, output_path: str, progress_callback=None) -> bool:
        """
        Download chat for a specific VOD
        
        Args:
            video_id: Twitch video ID
            output_path: Directory to save the chat file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            bool: True if download was successful
        """
        if not self.authenticate():
            return False
            
        try:
            # Remove "v" prefix if present
            if video_id.startswith("v"):
                video_id = video_id[1:]
                
            # Get video information to get duration
            video_info = self.get_video_info(video_id)
            if not video_info:
                return False
                
            # Create output directory if it doesn't exist
            os.makedirs(output_path, exist_ok=True)
            
            # Format output filename
            stream_date = datetime.datetime.fromisoformat(video_info["created_at"].replace("Z", "+00:00"))
            formatted_date = stream_date.strftime("%Y-%m-%d")
            title = video_info["title"]
            filename = f"{title} - {formatted_date} - Chat.json"
            safe_filename = "".join(c for c in filename if c.isalnum() or c in " -_.").strip()
            output_file = os.path.join(output_path, safe_filename)
            
            # Get comments in batches
            cursor = None
            all_comments = []
            url = f"{self.base_url}/videos/{video_id}/comments"
            headers = {
                "Client-ID": self.client_id,
                "Authorization": f"Bearer {self.access_token}"
            }
            
            total_duration_seconds = self._parse_duration(video_info["duration"])
            
            logger.info(f"Downloading chat for video {video_id} (Duration: {video_info['duration']})")
            
            while True:
                params = {"first": 100}  # Maximum allowed by API
                if cursor:
                    params["cursor"] = cursor
                    
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    logger.error(f"Failed to get comments: {response.status_code} - {response.text}")
                    break
                    
                data = response.json()
                batch_comments = data.get("data", [])
                all_comments.extend(batch_comments)
                
                # Update progress if callback provided
                if progress_callback and total_duration_seconds > 0 and batch_comments:
                    latest_comment_time = int(batch_comments[-1].get("content_offset_seconds", 0))
                    progress = min(1.0, latest_comment_time / total_duration_seconds)
                    progress_callback(progress)
                
                # Check if there are more comments
                cursor = data.get("pagination", {}).get("cursor")
                if not cursor:
                    break
                    
                # Add a small delay to avoid rate limiting
                time.sleep(0.25)
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "video_id": video_id,
                    "title": video_info["title"],
                    "streamer": video_info["user_name"],
                    "created_at": video_info["created_at"],
                    "comments": all_comments
                }, f, indent=2)
                
            logger.info(f"Successfully downloaded {len(all_comments)} chat messages to {output_file}")
            
            # Also save as plain text for easier reading
            txt_file = output_file.replace(".json", ".txt")
            self._save_as_text(all_comments, txt_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading chat: {str(e)}", exc_info=True)
            return False
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse Twitch duration string (e.g., '1h2m3s') to seconds"""
        seconds = 0
        current_num = ""
        
        for char in duration_str:
            if char.isdigit():
                current_num += char
            elif char == 'h' and current_num:
                seconds += int(current_num) * 3600
                current_num = ""
            elif char == 'm' and current_num:
                seconds += int(current_num) * 60
                current_num = ""
            elif char == 's' and current_num:
                seconds += int(current_num)
                current_num = ""
                
        return seconds
    
    def _save_as_text(self, comments: List[Dict], output_file: str):
        """Save comments as readable text file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for comment in comments:
                    timestamp = self._format_seconds(comment.get("content_offset_seconds", 0))
                    username = comment.get("commenter", {}).get("display_name", "Unknown")
                    message = comment.get("message", {}).get("body", "")
                    f.write(f"[{timestamp}] {username}: {message}\n")
                    
            logger.info(f"Saved chat as text to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving chat as text: {str(e)}", exc_info=True)
    
    def _format_seconds(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from Twitch URL
    
    Args:
        url: Twitch video URL
        
    Returns:
        str: Video ID or None if not found
    """
    if not url:
        return None
        
    if "twitch.tv/videos/" in url:
        # Extract the numeric part after /videos/
        import re
        match = re.search(r'twitch\.tv/videos/(\d+)', url)
        if match:
            return match.group(1)
    
    return None