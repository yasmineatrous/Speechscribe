from __future__ import unicode_literals
import yt_dlp as youtube_dl
import os
import time
import shutil
import logging
import sys
from dotenv import load_dotenv


load_dotenv()  

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create console handler and set level to debug
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to ch
ch.setFormatter(formatter)

# Add ch to logger
logger.addHandler(ch)

# Constants
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB (increased from 100 MB)
FILE_TOO_LARGE_MESSAGE = "The audio file is too large (over 500 MB). Try a shorter video."
MAX_RETRIES = 4  # Increased from 3
RETRY_DELAY = 2

# Create downloads directory if it doesn't exist
os.makedirs('./downloads/audio', exist_ok=True)

class MyLogger(object):
    def __init__(self, external_logger=None):
        self.external_logger = external_logger or (lambda x: None)

    def debug(self, msg):
        logger.debug(msg)
        self.external_logger(msg)

    def warning(self, msg):
        logger.warning(msg)
        self.external_logger(msg)

    def error(self, msg):
        logger.error(msg)
        self.external_logger(msg)

def progress_hook(d):
    if d["status"] == "finished":
        logger.info("Download completed, now converting...")

def get_ydl_opts(external_logger=None):
    """
    Get options for youtube-dl
    """
    return {
        # Prioritize audio-only formats with lower quality for faster downloads
        "format": "worstaudio/worst[filesize<50M]/bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",  # Reduced quality from 192kbps to 128kbps
            }
        ],
        "logger": MyLogger(external_logger),
        "outtmpl": "./downloads/audio/%(title)s.%(ext)s",  # Set output filename
        "progress_hooks": [progress_hook],
        "noplaylist": True,  # Only download the video, not the entire playlist
        "quiet": False,
        "no_warnings": False,
        # Adding some timeouts to prevent hanging on large videos
        "socket_timeout": 30,  # 30 seconds
    }

def download_video_audio(url, external_logger=None):
    """
    Download audio from a YouTube video URL
    
    Args:
        url (str): YouTube URL
        external_logger (function, optional): External logging function
        
    Returns:
        str: Path to downloaded audio file, or None if download failed
    """
    logger.info(f"Starting download of YouTube audio from: {url}")
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            # Get youtube-dl options
            ydl_opts = get_ydl_opts(external_logger)
            
            # Download video and extract audio
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Extracting information from URL: {url}")
                
                # First extract info without downloading to check size
                info = ydl.extract_info(url, download=False)
                
                # Check if file is too large
                filesize = info.get("filesize", 0)
                if filesize > MAX_FILE_SIZE:
                    logger.error(FILE_TOO_LARGE_MESSAGE)
                    return None
                
                # Prepare filename
                filename = ydl.prepare_filename(info)
                
                # Download the file
                logger.info("Starting the actual download...")
                ydl.download([url])
                
                # Get the mp3 filename after conversion
                mp3_filename = os.path.splitext(filename)[0] + '.mp3'
                logger.info(f"Download complete. MP3 file: {mp3_filename}")
                
                return mp3_filename
                
        except Exception as e:
            retries += 1
            logger.error(f"Error during download (Attempt {retries}/{MAX_RETRIES}): {str(e)}")
            
            if retries >= MAX_RETRIES:
                logger.error(f"Maximum retries ({MAX_RETRIES}) reached. Giving up.")
                return None
                
            time.sleep(RETRY_DELAY)
    
    return None

def delete_download(path):
    """
    Delete a downloaded file or directory
    
    Args:
        path (str): Path to file or directory to delete
    """
    try:
        if os.path.isfile(path):
            os.remove(path)
            logger.info(f"File {path} has been deleted")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            logger.info(f"Directory {path} and its contents have been deleted")
        else:
            logger.warning(f"Path {path} is neither a file nor a directory")
    except Exception as e:
        logger.error(f"Error deleting {path}: {str(e)}")