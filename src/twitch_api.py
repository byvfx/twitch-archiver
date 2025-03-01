import requests
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class TwitchAPI:
    def __init__(self, client_id: str, oauth_token: Optional[str] = None):
        self.client_id = client_id
        self.oauth_token = oauth_token
        self.base_url = "https://api.twitch.tv/helix"
        self.gql_url = "https://gql.twitch.tv/gql"
    
    def get_headers(self) -> Dict[str, str]:
        """Get the headers for API requests."""
        headers = {
            "Client-ID": self.client_id,
            "Content-Type": "application/json"
        }
        
        if self.oauth_token:
            headers["Authorization"] = f"Bearer {self.oauth_token}"
            
        return headers
    
    def check_vod_access(self, video_id: str) -> Tuple[bool, str]:
        """
        Check if a VOD is subscriber-only and if the current authentication allows access.
        
        Returns:
            Tuple[bool, str]: (can_access, reason)
        """
        # First try with the Helix API
        url = f"{self.base_url}/videos"
        params = {"id": video_id}
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data.get("data"):
                return False, "Video not found"
                
            video_data = data["data"][0]
            
            # Check if video is subscriber-only
            if video_data.get("type") == "archive" and video_data.get("viewable") == "subscription":
                if not self.oauth_token:
                    return False, "This is a subscriber-only VOD and no authentication provided"
                
                # Try to access with current token
                # This is a simplified check - in reality you'd verify if the token has subscriber permissions
                return True if self.oauth_token else False, "Subscriber-only VOD"
                
            return True, "Public VOD"
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking VOD access: {e}")
            # Fallback check could be implemented here with GQL
            return False, f"Error checking access: {str(e)}"
    
    def get_vod_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a VOD."""
        url = f"{self.base_url}/videos"
        params = {"id": video_id}
        
        try:
            response = requests.get(url, headers=self.get_headers(), params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("data"):
                return data["data"][0]
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting VOD info: {e}")
            return None
