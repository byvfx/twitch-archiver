"""
Test script for downloading Twitch VOD chat
This is separate from the main app to help with debugging
"""

import os
import sys
import json
import time
import argparse
import logging
from twitch_chat import TwitchChatRetriever

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ChatDownloadTest")

def load_credentials():
    """Load API credentials from config file"""
    config_file = os.path.join(os.path.expanduser("~"), ".twitch_archiver", "config.json")
    
    if not os.path.exists(config_file):
        logger.error(f"Config file not found: {config_file}")
        return None, None
        
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        return config.get("client_id"), config.get("client_secret")
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        return None, None

def progress_callback(progress):
    """Display download progress in console"""
    progress_str = f"{progress:.1%}"
    print(f"Download progress: {progress_str}", end='\r')

def main():
    parser = argparse.ArgumentParser(description="Test chat download for Twitch VODs")
    parser.add_argument("video_id", help="Twitch video ID (numeric part only)")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    args = parser.parse_args()
    
    # Clean video ID
    video_id = args.video_id
    if video_id.startswith("v"):
        video_id = video_id[1:]
    
    # Load credentials
    client_id, client_secret = load_credentials()
    
    if not client_id or not client_secret:
        logger.error("Missing API credentials. Please set them up in the main app first.")
        return 1
    
    logger.info(f"Testing chat download for video ID: {video_id}")
    logger.info(f"Output directory: {args.output}")
    
    # Create chat retriever
    retriever = TwitchChatRetriever(client_id, client_secret)
    
    # Authenticate
    if not retriever.authenticate():
        logger.error("Failed to authenticate with Twitch API")
        return 1
    
    # Get video info
    video_info = retriever.get_video_info(video_id)
    if not video_info:
        logger.error(f"Failed to get video info for ID: {video_id}")
        return 1
    
    logger.info(f"Video title: {video_info.get('title')}")
    logger.info(f"Channel: {video_info.get('user_name')}")
    logger.info(f"Duration: {video_info.get('duration')}")
    
    # Download chat
    start_time = time.time()
    success = retriever.download_chat(video_id, args.output, progress_callback)
    elapsed = time.time() - start_time
    
    if success:
        logger.info(f"Chat download completed in {elapsed:.2f} seconds")
        return 0
    else:
        logger.error(f"Chat download failed after {elapsed:.2f} seconds")
        return 1

if __name__ == "__main__":
    sys.exit(main())
