import re
import logging
from youtube_transcript_api import YouTubeTranscriptApi

# Configure logging
logger = logging.getLogger(__name__)

def extract_video_id(youtube_url):
    """
    Extract the video ID from a YouTube URL
    
    Args:
        youtube_url (str): The YouTube video URL
        
    Returns:
        str: The YouTube video ID
    """
    if not youtube_url:
        return None
        
    # For URLs like youtube.com/watch?v=VIDEO_ID&feature=...
    # This pattern catches the v parameter in any position
    watch_pattern = re.compile(r'(?:youtube\.com\/watch\?(?:[^&]*&)*v=|youtube\.com\/watch\?v=)([\w-]+)')
    match = watch_pattern.search(youtube_url)
    if match:
        return match.group(1)
    
    # For short URLs like youtu.be/VIDEO_ID
    short_pattern = re.compile(r'(?:youtu\.be\/)([\w-]+)')
    match = short_pattern.search(youtube_url)
    if match:
        return match.group(1)
    
    # For embed URLs like youtube.com/embed/VIDEO_ID
    embed_pattern = re.compile(r'(?:youtube\.com\/embed\/)([\w-]+)')
    match = embed_pattern.search(youtube_url)
    if match:
        return match.group(1)
    
    # For legacy embed URLs like youtube.com/v/VIDEO_ID
    v_pattern = re.compile(r'(?:youtube\.com\/v\/)([\w-]+)')
    match = v_pattern.search(youtube_url)
    if match:
        return match.group(1)
    
    # For YouTube shorts like youtube.com/shorts/VIDEO_ID
    shorts_pattern = re.compile(r'(?:youtube\.com\/shorts\/)([\w-]+)')
    match = shorts_pattern.search(youtube_url)
    if match:
        return match.group(1)
    
    # For urls that have the video_id as a query parameter other than 'v'
    query_pattern = re.compile(r'(?:youtube\.com\/(?:.*?)(?:\?|&)(?:v|video_id)=)([\w-]+)')
    match = query_pattern.search(youtube_url)
    if match:
        return match.group(1)
    
    return None

def get_youtube_transcript(youtube_url):
    """
    Get the transcript from a YouTube video
    
    Args:
        youtube_url (str): The YouTube video URL
        
    Returns:
        str: The full transcript
    """
    logger.info(f"Getting transcript for YouTube URL: {youtube_url}")
    
    video_id = extract_video_id(youtube_url)
    logger.info(f"Extracted video ID: {video_id}")
    
    if not video_id:
        logger.error("Failed to extract video ID from the URL")
        return "Error: Could not extract video ID from the provided URL."
    
    try:
        logger.info(f"Requesting transcript for video ID: {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        if not transcript_list:
            logger.warning("Received empty transcript list from YouTube API")
            return "Error: No transcript available for this video. The creator may not have enabled captions."
        
        # Combine all text parts into a single transcript
        transcript = " ".join([part['text'] for part in transcript_list])
        
        # Log transcript length for debugging
        transcript_length = len(transcript)
        logger.info(f"Successfully retrieved transcript with {transcript_length} characters")
        
        if transcript_length == 0:
            logger.warning("Transcript is empty")
            return "Error: Transcript is empty. The video may not have proper captions."
        
        return transcript
    
    except Exception as e:
        logger.error(f"Error getting transcript from YouTube API: {str(e)}")
        
        # More specific error messages based on known exceptions
        if "No transcript" in str(e):
            return "Error: No transcript available for this video. The creator may not have enabled captions."
        elif "Video unavailable" in str(e):
            return "Error: The video is unavailable or private."
        elif "not supported" in str(e):
            return "Error: This video's subtitles format is not supported."
        
        return f"Error getting transcript: {str(e)}"