"""
Test utility for Twitch chat download - Async Version
"""

import os
import sys
import time
import json
import logging
from utils.logging_utils import setup_logging
import argparse
import asyncio
from twitch_chat import TwitchChatRetriever

# Set up logging
setup_logging(log_level=logging.DEBUG, log_file="chat_download_test.log")
logger = logging.getLogger("ChatTest")

def load_credentials():
    """Load API credentials from config file"""
    config_file = os.path.join(os.path.expanduser("~"), ".twitch_archiver", "config.json")
    
    if not os.path.exists(config_file):
        logger.error(f"Config file not found: {config_file}")
        return None, None
        
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        client_id = config.get("client_id", "")
        client_secret = config.get("client_secret", "")
        
        if not client_id or not client_secret:
            logger.error("Missing client_id or client_secret in config file")
            return None, None
            
        return client_id, client_secret
        
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None, None

def progress_callback(progress):
    """Display progress in console"""
    progress_str = f"{progress:.1%}"
    print(f"Download progress: {progress_str}", end='\r')

async def async_main():
    parser = argparse.ArgumentParser(description="Test Twitch chat download")
    parser.add_argument("video_id", help="Twitch video ID (with or without 'v' prefix)")
    parser.add_argument("--output", "-o", default=".", help="Output directory path")
    parser.add_argument("--method", "-m", choices=["cursor", "segments", "sampling", "all"], 
                       default="all", help="Download method to use")
    args = parser.parse_args()
    
    # Clean up video ID
    video_id = args.video_id
    if video_id.startswith("v"):
        video_id = video_id[1:]
        
    logger.info(f"Testing chat download for video ID: {video_id}")
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Method: {args.method}")
    
    # Load credentials
    client_id, client_secret = load_credentials()
    
    if not client_id or not client_secret:
        logger.error("Could not load credentials. Please configure them first.")
        return 1
        
    # Initialize chat retriever
    retriever = TwitchChatRetriever(client_id, client_secret)
    
    try:
        # Authenticate
        if not await retriever.authenticate():
            logger.error("Authentication failed")
            return 1
            
        # Get video info
        logger.info("Getting video info...")
        video_info = await retriever.get_video_info(video_id)
        
        if not video_info:
            logger.error("Failed to get video info")
            return 1
            
        logger.info(f"Video title: {video_info.get('title')}")
        logger.info(f"Channel: {video_info.get('user_name')}")
        logger.info(f"Duration: {video_info.get('duration')}")
        
        # Calculate duration in seconds
        duration_seconds = retriever._parse_duration(video_info.get('duration', '0h0m0s'))
        logger.info(f"Duration in seconds: {duration_seconds}")
        
        # Download chat
        logger.info("Starting chat download...")
        start_time = time.time()
        
        if args.method == "cursor":
            comments = await retriever._download_chat_by_cursor(video_id, duration_seconds, progress_callback)
            success = len(comments) > 0
            if success:
                # Save to file
                output_file = os.path.join(args.output, f"{video_id}_chat_cursor.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "video_id": video_id,
                        "title": video_info.get('title'),
                        "comments": comments
                    }, f, indent=2)
                logger.info(f"Saved {len(comments)} comments to {output_file}")
                
        elif args.method == "segments":
            comments = await retriever._download_chat_by_segments(video_id, duration_seconds, progress_callback)
            success = len(comments) > 0
            if success:
                # Save to file
                output_file = os.path.join(args.output, f"{video_id}_chat_segments.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "video_id": video_id,
                        "title": video_info.get('title'),
                        "comments": comments
                    }, f, indent=2)
                logger.info(f"Saved {len(comments)} comments to {output_file}")
                
        elif args.method == "sampling":
            comments = await retriever._download_chat_by_sampling(video_id, duration_seconds, progress_callback)
            success = len(comments) > 0
            if success:
                # Save to file
                output_file = os.path.join(args.output, f"{video_id}_chat_sampling.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "video_id": video_id,
                        "title": video_info.get('title'),
                        "comments": comments
                    }, f, indent=2)
                logger.info(f"Saved {len(comments)} comments to {output_file}")
                
        else:  # all - use the normal method
            success = await retriever.download_chat(video_id, args.output, progress_callback)
        
        elapsed = time.time() - start_time
        
        if success:
            logger.info(f"Chat download completed in {elapsed:.2f} seconds")
            return 0
        else:
            logger.error(f"Chat download failed after {elapsed:.2f} seconds")
            return 1
    finally:
        await retriever.close()

def main():
    """Run the async main function"""
    return asyncio.run(async_main())

if __name__ == "__main__":
    sys.exit(main())
