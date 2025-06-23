"""
Twitch Chat Retriever Module for Twitch VOD Archiver - Async Version
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
import datetime
import threading
import re
from typing import Dict, List, Optional, Tuple, Callable, Any

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
        self.gql_url = "https://gql.twitch.tv/gql"
        self._session = None
        
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
        
    async def authenticate(self) -> bool:
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
            
            session = await self.get_session()
            async with session.post(auth_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data["access_token"]
                    # Set expiry with a small buffer before actual expiry
                    self.token_expiry = time.time() + data["expires_in"] - 100
                    logger.info("Successfully authenticated with Twitch API")
                    return True
                else:
                    logger.error(f"Failed to authenticate: {response.status} - Error response received")
                    return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return False
    
    async def get_video_info(self, video_id: str) -> Optional[Dict]:
        """
        Get video information from Twitch API
        
        Args:
            video_id: Twitch video ID (numeric part only)
            
        Returns:
            dict: Video information or None if not found
        """
        if not await self.authenticate():
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
            
            session = await self.get_session()
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["data"]:
                        return data["data"][0]
                    else:
                        logger.warning(f"Video not found: {video_id}")
                        return None
                else:
                    text = await response.text()
                    logger.error(f"Failed to get video info: {response.status} - {text}")
                    return None
                
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}", exc_info=True)
            return None
    
    async def download_chat(self, video_id: str, output_path: str, progress_callback=None) -> bool:
        """
        Download chat for a specific VOD using Twitch's GQL API
        
        Args:
            video_id: Twitch video ID
            output_path: Directory to save the chat file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            bool: True if download was successful
        """
        logger.info(f"Starting chat download for video ID: {video_id}")
        
        if not await self.authenticate():
            logger.error("Authentication failed - cannot download chat")
            return False
            
        try:
            # Remove "v" prefix if present
            if video_id.startswith("v"):
                video_id = video_id[1:]
            
            logger.info(f"Using cleaned video ID: {video_id}")
                
            # Get video information to get duration
            video_info = await self.get_video_info(video_id)
            if not video_info:
                logger.error(f"Could not get video info for video ID: {video_id}")
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
            
            # We'll use Twitch's GQL API to get chat comments
            total_duration_seconds = self._parse_duration(video_info["duration"])
            
            logger.info(f"Downloading chat for video {video_id} (Duration: {video_info['duration']})")
            logger.info(f"Chat will be saved to: {output_file}")
            
            # Try using the segment-based chat download approach first with parallel requests
            all_comments = await self._download_chat_by_segments(video_id, total_duration_seconds, progress_callback)
            
            if not all_comments:
                logger.warning("Segment method failed or returned no comments, trying cursor method...")
                all_comments = await self._download_chat_by_cursor(video_id, total_duration_seconds, progress_callback)
                
            if not all_comments:
                logger.warning("Both methods failed, falling back to offset sampling...")
                all_comments = await self._download_chat_by_sampling(video_id, total_duration_seconds, progress_callback)
                
            logger.info(f"Total comments retrieved: {len(all_comments)}")
            
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
        finally:
            # Ensure session is closed
            await self.close()

    async def _download_chat_by_cursor(self, video_id, total_duration_seconds, progress_callback=None):
        """Download chat using cursor-based pagination"""
        logger.info("Using cursor-based chat download method...")
        
        all_comments = []
        cursor = None
        has_next_page = True
        processed_edges = set()  # Track processed edges to avoid duplication
        
        # GQL headers with the website's client ID
        headers = {
            "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
            "Content-Type": "application/json"
        }
        
        # Optional: add authorization if we have a token
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        # Set a reasonable limit for iterations to prevent infinite loops
        max_iterations = 200
        iterations = 0
        
        # Get aiohttp session
        session = await self.get_session()
        
        while has_next_page and iterations < max_iterations:
            iterations += 1
            
            # GraphQL query for comments
            gql_query = {
                "operationName": "VideoCommentsByOffsetOrCursor",
                "variables": {
                    "videoID": video_id
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "b70a3591ff0f4e0313d126c6a1502d79a1c02baebb288227c582044aa76adf6a"
                    }
                }
            }
            
            # Decide whether to use cursor or offset
            if cursor:
                gql_query["variables"]["cursor"] = cursor
                logger.debug(f"Using cursor: {cursor}")
            else:
                # Start from the beginning
                gql_query["variables"]["contentOffsetSeconds"] = 0
                logger.debug("Starting from contentOffsetSeconds: 0")
                
            try:
                async with session.post(self.gql_url, json=gql_query, headers=headers) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"Failed to get comments: {response.status} - {text}")
                        break
                        
                    data = await response.json()
                    
                    if "errors" in data:
                        logger.error(f"GQL errors: {data['errors']}")
                        break
                        
                    comments_data = data.get("data", {}).get("video", {}).get("comments", {})
                    edges = comments_data.get("edges", [])
                    logger.debug(f"Retrieved {len(edges)} comments in iteration {iterations}")
                    
                    # Check if we got any new edges
                    if not edges:
                        logger.warning(f"No comments found in this batch")
                        break
                        
                    # Process edges
                    new_comments = 0
                    max_offset = 0
                    
                    for edge in edges:
                        # Generate a unique ID for this edge to avoid duplication
                        edge_id = f"{edge.get('cursor', '')}"
                        
                        # Skip if we've already processed this edge
                        if edge_id in processed_edges:
                            continue
                            
                        processed_edges.add(edge_id)
                        
                        node = edge.get("node", {})
                        offset_seconds = node.get("contentOffsetSeconds", 0)
                        max_offset = max(max_offset, offset_seconds)
                        
                        # Create a structured comment object
                        comment = {
                            "content_offset_seconds": offset_seconds,
                            "commenter": {
                                "display_name": node.get("commenter", {}).get("displayName", "Unknown"),
                                "id": node.get("commenter", {}).get("id", "")
                            },
                            "message": {
                                "body": self._extract_message_text(node.get("message", {})),
                            },
                            "timestamp": node.get("createdAt", "")
                        }
                        
                        all_comments.append(comment)
                        new_comments += 1
                    
                    # Check if we got any new comments
                    if new_comments == 0:
                        logger.warning("No new comments found, breaking loop")
                        break
                        
                    # Check for pagination
                    page_info = comments_data.get("pageInfo", {})
                    has_next_page = page_info.get("hasNextPage", False)
                    cursor = page_info.get("endCursor", None)
                    
                    # If hasNextPage is true but endCursor is None, something's wrong
                    if has_next_page and not cursor:
                        logger.warning("hasNextPage is true but no cursor provided, breaking loop")
                        break
                        
                    # Update progress
                    if progress_callback and total_duration_seconds > 0:
                        progress = min(0.95, max_offset / total_duration_seconds)  # Cap at 95% to account for final processing
                        progress_callback(progress)
                        
                    logger.debug(f"Progress: {max_offset}/{total_duration_seconds}s = {max_offset/total_duration_seconds:.1%}")
                    
                    # Add a small delay to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error during comment fetch: {str(e)}", exc_info=True)
                break
        
        # Sort comments by timestamp
        all_comments.sort(key=lambda c: c["content_offset_seconds"])
        return all_comments

    async def _download_chat_by_segments(self, video_id, total_duration_seconds, progress_callback=None):
        """Download chat by breaking video into segments with parallel requests"""
        logger.info("Using segment-based chat download method...")
        
        all_comments = []
        processed_comments = set()  # To avoid duplicates
        
        # Create segments of reasonable size (e.g., 5-10 minutes)
        segment_size = 300  # 5 minutes in seconds
        
        # If the video is very long, use larger segments
        if total_duration_seconds > 7200:  # 2 hours
            segment_size = 600  # 10 minutes
        
        # Calculate number of segments
        num_segments = max(1, int(total_duration_seconds / segment_size) + 1)
        
        # Cap at a reasonable number of segments
        max_segments = 50
        if num_segments > max_segments:
            logger.warning(f"Capping segments at {max_segments} (from {num_segments})")
            num_segments = max_segments
            segment_size = total_duration_seconds / max_segments
        
        logger.info(f"Breaking video into {num_segments} segments of ~{segment_size} seconds each")
        
        # Client ID for the Twitch website
        headers = {
            "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
            "Content-Type": "application/json"
        }
        
        # Get aiohttp session
        session = await self.get_session()
        
        # Create a list to store segment tasks
        segment_tasks = []
        
        # Function to process a segment
        async def process_segment(segment_id, offset_seconds):
            # GraphQL query for comments at this offset
            gql_query = {
                "operationName": "VideoCommentsByOffsetOrCursor",
                "variables": {
                    "videoID": video_id,
                    "contentOffsetSeconds": offset_seconds
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "b70a3591ff0f4e0313d126c6a1502d79a1c02baebb288227c582044aa76adf6a"
                    }
                }
            }
            
            logger.debug(f"Fetching segment {segment_id+1}/{num_segments} at offset {offset_seconds:.1f}s")
            
            try:
                async with session.post(self.gql_url, json=gql_query, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to get comments for segment {segment_id+1}: {response.status}")
                        return []
                        
                    data = await response.json()
                    
                    if "errors" in data:
                        logger.warning(f"GQL errors for segment {segment_id+1}: {data['errors']}")
                        return []
                        
                    video_comments = data.get("data", {}).get("video", {}).get("comments", {})
                    edges = video_comments.get("edges", [])
                    
                    logger.debug(f"Segment {segment_id+1}: retrieved {len(edges)} comments")
                    
                    segment_comments = []
                    
                    for edge in edges:
                        node = edge.get("node", {})
                        
                        # Create a structured comment
                        offset = node.get("contentOffsetSeconds", 0)
                        commenter_id = node.get("commenter", {}).get("id", "")
                        message_body = self._extract_message_text(node.get("message", {}))
                        comment_hash = f"{offset}-{commenter_id}-{message_body}"
                        
                        segment_comments.append({
                            "hash": comment_hash,
                            "comment": {
                                "content_offset_seconds": offset,
                                "commenter": {
                                    "display_name": node.get("commenter", {}).get("displayName", "Unknown"),
                                    "id": commenter_id
                                },
                                "message": {
                                    "body": message_body
                                },
                                "timestamp": node.get("createdAt", "")
                            }
                        })
                    
                    return segment_comments
                    
            except Exception as e:
                logger.warning(f"Error processing segment {segment_id+1}: {str(e)}")
                return []
        
        # Create tasks for each segment (with concurrency limit)
        max_concurrent = 5  # Don't overdo it to avoid rate limiting
        
        # Create batches of segments
        for batch_start in range(0, num_segments, max_concurrent):
            batch_end = min(batch_start + max_concurrent, num_segments)
            batch_tasks = []
            
            for i in range(batch_start, batch_end):
                offset_seconds = i * segment_size
                task = asyncio.create_task(process_segment(i, offset_seconds))
                batch_tasks.append(task)
                
            # Wait for all tasks in this batch to complete
            batch_results = await asyncio.gather(*batch_tasks)
            
            # Process the results from this batch
            for i, segment_comments in enumerate(batch_results):
                for comment_data in segment_comments:
                    # Skip duplicates
                    if comment_data["hash"] in processed_comments:
                        continue
                        
                    processed_comments.add(comment_data["hash"])
                    all_comments.append(comment_data["comment"])
                
                # Update progress after each batch
                if progress_callback:
                    progress = min(0.95, (batch_start + i + 1) / num_segments)
                    progress_callback(progress)
            
            # Add a small delay between batches to avoid rate limiting
            await asyncio.sleep(1)
        
        # Sort by timestamp and return
        all_comments.sort(key=lambda c: c["content_offset_seconds"])
        return all_comments

    async def _download_chat_by_sampling(self, video_id, total_duration_seconds, progress_callback=None):
        """Download chat by sampling points throughout the video with parallel requests"""
        logger.info("Using sampling-based chat download method...")
        
        all_comments = []
        processed_offsets = set()
        
        # Sample points - use more points for longer videos
        samples = 20
        if total_duration_seconds > 3600:  # 1 hour
            samples = 40
        if total_duration_seconds > 10800:  # 3 hours
            samples = 60
        
        # Calculate sample points throughout the video
        sample_points = []
        for i in range(samples):
            offset = int(i * total_duration_seconds / samples)
            sample_points.append(offset)
        
        # Add some extra points at the start
        for offset in [0, 30, 60, 120, 300, 600]:
            if offset < total_duration_seconds and offset not in sample_points:
                sample_points.append(offset)
        
        # Sort sample points
        sample_points.sort()
        
        logger.info(f"Using {len(sample_points)} sample points across the video")
        
        # GQL headers
        headers = {
            "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
            "Content-Type": "application/json"
        }
        
        # Get aiohttp session
        session = await self.get_session()
        
        # Process sample points with concurrency
        async def process_sample_point(sample_idx, offset):
            if offset in processed_offsets:
                return []
                
            processed_offsets.add(offset)
            
            gql_query = {
                "operationName": "VideoCommentsByOffsetOrCursor",
                "variables": {
                    "videoID": video_id,
                    "contentOffsetSeconds": offset
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "b70a3591ff0f4e0313d126c6a1502d79a1c02baebb288227c582044aa76adf6a"
                    }
                }
            }
            
            logger.debug(f"Sampling point {sample_idx+1}/{len(sample_points)} at {offset}s")
            
            try:
                async with session.post(self.gql_url, json=gql_query, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"Failed at sample {sample_idx+1}: {response.status}")
                        return []
                        
                    data = await response.json()
                    
                    if "errors" in data:
                        logger.warning(f"GQL errors at sample {sample_idx+1}: {data['errors']}")
                        return []
                        
                    video_comments = data.get("data", {}).get("video", {}).get("comments", {})
                    edges = video_comments.get("edges", [])
                    
                    logger.debug(f"Sample {sample_idx+1}: retrieved {len(edges)} comments at {offset}s")
                    
                    # Process comments from this sample
                    sample_comments = []
                    for edge in edges:
                        node = edge.get("node", {})
                        
                        sample_comments.append({
                            "content_offset_seconds": node.get("contentOffsetSeconds", 0),
                            "commenter": {
                                "display_name": node.get("commenter", {}).get("displayName", "Unknown"),
                                "id": node.get("commenter", {}).get("id", "")
                            },
                            "message": {
                                "body": self._extract_message_text(node.get("message", {}))
                            },
                            "timestamp": node.get("createdAt", "")
                        })
                        
                    return sample_comments
                    
            except Exception as e:
                logger.warning(f"Error at sample point {offset}s: {str(e)}")
                return []
        
        # Process sample points in batches with concurrency
        max_concurrent = 5
        
        for batch_start in range(0, len(sample_points), max_concurrent):
            batch_end = min(batch_start + max_concurrent, len(sample_points))
            batch_tasks = []
            
            for i in range(batch_start, batch_end):
                task = asyncio.create_task(process_sample_point(i, sample_points[i]))
                batch_tasks.append(task)
                
            # Wait for all tasks in this batch to complete
            batch_results = await asyncio.gather(*batch_tasks)
            
            # Process the results from this batch
            for i, sample_comments in enumerate(batch_results):
                for comment in sample_comments:
                    # Check for duplicates
                    is_duplicate = False
                    for existing in all_comments:
                        if (existing["content_offset_seconds"] == comment["content_offset_seconds"] and
                            existing["commenter"]["id"] == comment["commenter"]["id"] and
                            existing["message"]["body"] == comment["message"]["body"]):
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        all_comments.append(comment)
                
                # Update progress after each batch
                if progress_callback:
                    progress = min(0.95, (batch_start + i + 1) / len(sample_points))
                    progress_callback(progress)
            
            # Add a small delay between batches to avoid rate limiting
            await asyncio.sleep(1)
        
        # Sort by timestamp
        all_comments.sort(key=lambda c: c["content_offset_seconds"])
        
        return all_comments

    def _extract_message_text(self, message):
        """Extract text content from message object"""
        # Check for direct body field
        if "body" in message and message["body"]:
            return message["body"]
        
        # Try to get text from fragments
        fragments = message.get("fragments", [])
        if fragments:
            text = ""
            for fragment in fragments:
                text += fragment.get("text", "")
            return text
        
        return ""

    def _extract_message_body(self, message):
        """Extract message body from message data"""
        if "body" in message:
            return message["body"]
        
        # If body is not directly available, try to concatenate fragments
        fragments = message.get("fragments", [])
        if fragments:
            return "".join(frag.get("text", "") for frag in fragments)
            
        return ""
    
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
    
    # Synchronous compatibility methods for backward compatibility
    def authenticate_sync(self) -> bool:
        """Synchronous version of authenticate for backward compatibility."""
        return asyncio.run(self.authenticate())
    
    def get_video_info_sync(self, video_id: str) -> Optional[Dict]:
        """Synchronous version of get_video_info for backward compatibility."""
        return asyncio.run(self.get_video_info(video_id))
    
    def download_chat_sync(self, video_id: str, output_path: str, progress_callback=None) -> bool:
        """Synchronous version of download_chat for backward compatibility."""
        return asyncio.run(self.download_chat(video_id, output_path, progress_callback))

# For backward compatibility, keep this function
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
        match = re.search(r'twitch\.tv/videos/(\d+)', url)
        if match:
            logger.info(f"Extracted video ID {match.group(1)} from URL: {url}")
            return match.group(1)
    
    logger.warning(f"Could not extract video ID from URL: {url}")
    return None


