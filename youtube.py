import re
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(youtube_url):
    """
    Extract the video ID from a YouTube URL
    
    Args:
        youtube_url (str): The YouTube video URL
        
    Returns:
        str: The YouTube video ID
    """
    # Common patterns for YouTube URLs
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)',   # Standard watch URL or youtu.be
        r'(?:youtube\.com\/embed\/)([\w-]+)',                 # Embed URL
        r'(?:youtube\.com\/v\/)([\w-]+)',                     # Legacy embed
        r'(?:youtube\.com\/shorts\/)([\w-]+)'                 # YouTube shorts
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
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
    video_id = extract_video_id(youtube_url)
    
    if not video_id:
        return "Error: Could not extract video ID from the provided URL."
    
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine all text parts into a single transcript
        transcript = " ".join([part['text'] for part in transcript_list])
        
        return transcript
    
    except Exception as e:
        return f"Error getting transcript: {str(e)}"