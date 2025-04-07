import speech_recognition as sr
import logging
import os
import tempfile
import groq
from pydub import AudioSegment
import uuid
import time
from flask import session

# Configure logging
logger = logging.getLogger(__name__)

def transcribe_audio(audio_file_path):
    """
    Transcribe audio file to text using Groq's Whisper API
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    try:
        # Check if file exists and has content
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file does not exist: {audio_file_path}")
            return "Error: Audio file not found"
            
        file_size = os.path.getsize(audio_file_path)
        if file_size == 0:
            logger.error(f"Audio file is empty: {audio_file_path}")
            return "Error: Audio file is empty"
            
        logger.info(f"Processing audio file with Groq API: {audio_file_path} (size: {file_size} bytes)")
        
        # Initialize Groq client
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            logger.error("GROQ_API_KEY environment variable not found")
            return "Error: Groq API key not configured"
            
        groq_client = groq.Groq(api_key=groq_api_key)
        
        # Open the audio file and send to Groq's Whisper API
        try:
            with open(audio_file_path, "rb") as audio_file:
                logger.info("Sending audio file to Groq's Whisper API...")
                
                try:
                    transcription = groq_client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3",
                        prompt="",
                        response_format="text",
                        language="en",
                        temperature=0.0
                    )
                    
                    # The API can return either a string directly or an object with a text attribute
                    # Handle both cases gracefully
                    if hasattr(transcription, 'text'):
                        # Case where it's a structured response object
                        transcript = transcription.text
                    else:
                        # Case where it's a string directly
                        transcript = transcription
                    
                    if transcript and len(str(transcript).strip()) > 0:
                        logger.info(f"Groq transcription completed: {str(transcript)[:50]}...")
                        return transcript
                    else:
                        logger.error("Groq returned empty transcript")
                        return "Error: No speech could be recognized in the audio"
                        
                except Exception as groq_error:
                    error_msg = str(groq_error)
                    logger.error(f"Groq API error: {error_msg}")
                    
                    # Provide more specific error messages for common issues
                    if "authentication" in error_msg.lower():
                        return "Error: Authentication failed with the Groq API. Please check your API key."
                    elif "file size" in error_msg.lower() or "too large" in error_msg.lower():
                        return "Error: The audio file is too large for the Groq API. Try a shorter audio clip or use YouTube transcription instead."
                    elif "timeout" in error_msg.lower() or "deadline" in error_msg.lower():
                        return "Error: The Groq API request timed out. This might be due to a large file or network issues. Try again or use YouTube transcription."
                    elif "format" in error_msg.lower():
                        return "Error: The audio file format is not supported by the Groq API. Try converting to MP3 or WAV."
                    else:
                        return f"Error: Could not transcribe with Groq API. {error_msg}"
                    
        except Exception as file_error:
            logger.error(f"Error opening or processing audio file: {str(file_error)}")
            return f"Error: Could not process audio file format. {str(file_error)}"
            
    except Exception as e:
        logger.error(f"Error in transcription process: {str(e)}")
        return f"Error processing audio: {str(e)}"

def save_audio_from_blob(audio_blob):
    """
    Save audio blob to a temporary file
    
    Args:
        audio_blob: Audio data blob
        
    Returns:
        str: Path to the saved audio file
    """
    try:
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, "temp_audio.wav")
        
        # Write blob data to file
        with open(temp_path, 'wb') as f:
            f.write(audio_blob)
            
        return temp_path
    
    except Exception as e:
        logger.error(f"Error saving audio blob: {str(e)}")
        raise e

import subprocess

def extract_audio_from_video(video_path, output_path, max_duration=None):
    """
    Extract audio from a video file using FFmpeg for faster processing
    
    Args:
        video_path (str): Path to the video file
        output_path (str): Path where the extracted audio will be saved
        max_duration (int, optional): Maximum duration in seconds to extract
                                     (for large files, extract only first N minutes)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Extracting audio from video file using FFmpeg: {video_path}")
        
        # Get video duration if we need to check if it's a large file
        video_duration = None
        if max_duration:
            try:
                duration_cmd = [
                    'ffprobe', 
                    '-v', 'error', 
                    '-show_entries', 'format=duration', 
                    '-of', 'default=noprint_wrappers=1:nokey=1', 
                    video_path
                ]
                duration_result = subprocess.run(
                    duration_cmd, 
                    stderr=subprocess.PIPE, 
                    stdout=subprocess.PIPE, 
                    text=True,
                    timeout=30
                )
                if duration_result.returncode == 0:
                    video_duration = float(duration_result.stdout.strip())
                    logger.info(f"Video duration: {video_duration} seconds")
            except Exception as e:
                logger.warning(f"Could not determine video duration: {str(e)}")
        
        # Build the FFmpeg command
        cmd = ['ffmpeg', '-i', video_path]  # Base command with input
        
        # Add time limit if video is very long
        if max_duration and video_duration and video_duration > max_duration:
            logger.info(f"Limiting audio extraction to first {max_duration} seconds of video")
            cmd.extend(['-t', str(max_duration)])  # Limit duration
        
        # Add output options
        cmd.extend([
            '-vn',             # Skip video
            '-acodec', 'libmp3lame',  # Use MP3 codec
            '-ar', '16000',    # Set sample rate to 16kHz
            '-ac', '1',        # Mono channel
            '-q:a', '5',       # Medium quality (faster)
            '-y',              # Overwrite output file
            output_path
        ])
        
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        
        # Run the command with a timeout
        result = subprocess.run(
            cmd, 
            stderr=subprocess.PIPE, 
            stdout=subprocess.PIPE,
            timeout=300  # 5 minute timeout
        )
        
        # Check if the command was successful
        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"FFmpeg audio extraction successful: {output_path}")
            return True
        else:
            logger.error(f"FFmpeg audio extraction failed with code {result.returncode}")
            logger.error(f"FFmpeg output: {result.stderr.decode('utf-8', errors='replace')}")
            
            # Fall back to pydub if FFmpeg fails
            logger.info("Falling back to pydub for audio extraction")
            try:
                # Load the video file with pydub
                video = AudioSegment.from_file(video_path)
                
                # Export as MP3
                video.export(output_path, format="mp3")
                
                # Verify the output file exists and has content
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Pydub fallback audio extraction successful: {output_path}")
                    return True
                else:
                    logger.error(f"Pydub fallback audio extraction failed: Output file is empty or does not exist")
                    return False
            except Exception as pydub_error:
                logger.error(f"Pydub fallback extraction error: {str(pydub_error)}")
                return False
            
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg process timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Error extracting audio from video: {str(e)}")
        return False

def process_uploaded_audio(uploaded_file):
    """
    Process and transcribe an uploaded audio or video file (MP3, WAV, MP4, etc.)
    
    This function automatically detects if the file is a video format and extracts the audio,
    then transcribes the audio using Groq's Whisper API.
    
    Args:
        uploaded_file: The uploaded file object from Flask request.files
        
    Returns:
        str: Transcribed text from the audio portion of the file
    """
    # Create unique filenames first
    file_id = str(uuid.uuid4())
    temp_input_path = None
    wav_path = None
    
    try:
        logger.info(f"Processing uploaded file: {uploaded_file.filename}")
        
        # Get file metadata
        original_filename = uploaded_file.filename
        file_extension = os.path.splitext(original_filename)[1].lower()
        
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Define file paths
        temp_input_path = os.path.join(temp_dir, f"{file_id}{file_extension}")
        
        # Define valid video extensions
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
        is_video = file_extension in video_extensions
        
        # For videos, we'll extract to mp3 for faster processing
        audio_path = os.path.join(temp_dir, f"{file_id}.mp3" if is_video else f"{file_id}.wav")
        wav_path = audio_path  # For compatibility with the rest of the code
        
        # Save the uploaded file directly to disk to avoid memory issues
        logger.info(f"Saving uploaded file to: {temp_input_path}")
        uploaded_file.save(temp_input_path)
        file_size = os.path.getsize(temp_input_path)
        logger.info(f"File saved successfully. Size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("Uploaded file is empty (0 bytes)")
            return "Error: The uploaded file is empty. Please try again with a valid file."
        
        # Process based on file type
        if is_video:
            logger.info(f"Processing video file: {file_extension}")
            
            # For large files, only process first 10 minutes
            file_size_mb = file_size / (1024 * 1024)
            max_duration = None
            
            # If file is over 25MB, limit to 10 minutes
            if file_size_mb > 25:
                max_duration = 600  # 10 minutes in seconds
                logger.info(f"Large video file detected ({file_size_mb:.2f} MB), limiting to first {max_duration/60:.1f} minutes")
            
            if not extract_audio_from_video(temp_input_path, wav_path, max_duration=max_duration):
                return "Error: Could not extract audio from video file."
                
            # If we limited the duration, add a note to that effect
            if max_duration:
                session_note = "Note: Due to the large size of the video, only the first 10 minutes were transcribed. For longer videos, please use the YouTube transcription option instead."
                # Store this note to potentially add it to the transcript
                session['processing_note'] = session_note
        elif file_extension.lower() != '.wav':
            # Convert audio to WAV if needed
            logger.info(f"Converting {file_extension} audio file to WAV format")
            try:
                # Load the audio file with pydub
                logger.debug(f"Loading audio file: {temp_input_path}")
                if file_extension.lower() == '.mp3':
                    audio = AudioSegment.from_mp3(temp_input_path)
                elif file_extension.lower() == '.m4a':
                    audio = AudioSegment.from_file(temp_input_path, format="m4a")
                elif file_extension.lower() == '.ogg':
                    audio = AudioSegment.from_ogg(temp_input_path)
                else:
                    # Try generic loading for other formats
                    audio = AudioSegment.from_file(temp_input_path)
                
                logger.debug("Audio file loaded successfully")
                
                # Convert to WAV format at 16kHz (good for speech recognition)
                logger.debug("Converting audio to 16kHz")
                audio = audio.set_frame_rate(16000)
                
                logger.debug(f"Exporting to WAV: {wav_path}")
                audio.export(wav_path, format="wav")
                
                logger.info(f"Audio conversion successful: {wav_path}")
                
            except Exception as e:
                logger.error(f"Error converting audio file: {str(e)}")
                # Clean up the original temp file
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
                return f"Error: Could not convert audio file. {str(e)}"
        else:
            # If already WAV, just rename the original file
            logger.info("File is already WAV format, using as-is")
            wav_path = temp_input_path
        
        # Add a small delay to ensure file is written to disk completely
        time.sleep(0.5)
        
        # Verify the WAV file exists and has content
        if not os.path.exists(wav_path):
            logger.error(f"WAV file does not exist: {wav_path}")
            return "Error: WAV file was not created successfully."
            
        wav_size = os.path.getsize(wav_path)
        if wav_size == 0:
            logger.error(f"WAV file is empty: {wav_path}")
            return "Error: Converted WAV file is empty."
        
        logger.info(f"WAV file ready for transcription: {wav_path} (size: {wav_size} bytes)")
        
        # Transcribe the WAV file
        transcript = transcribe_audio(wav_path)
        logger.info(f"Transcription received: {len(transcript)} characters")
        
        # Clean up temporary files after successful transcription
        try:
            logger.debug("Cleaning up temporary files")
            if temp_input_path and os.path.exists(temp_input_path) and temp_input_path != wav_path:
                os.remove(temp_input_path)
                logger.debug(f"Removed input file: {temp_input_path}")
                
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)
                logger.debug(f"Removed WAV file: {wav_path}")
        except Exception as e:
            logger.warning(f"Error removing temporary files: {str(e)}")
        
        return transcript
        
    except Exception as e:
        logger.error(f"Error processing uploaded audio: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Clean up temporary files in case of error
        try:
            if temp_input_path and os.path.exists(temp_input_path):
                os.remove(temp_input_path)
            if wav_path and wav_path != temp_input_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {str(cleanup_error)}")
            
        return f"Error processing media file: {str(e)}"

def transcribe_youtube_audio(audio_file_path):
    """
    Transcribe YouTube audio file using Groq's Whisper API
    
    Args:
        audio_file_path (str): Path to the downloaded audio file
        
    Returns:
        str: Transcribed text
    """
    try:
        logger.info(f"Transcribing YouTube audio with Groq API from: {audio_file_path}")
        
        # First check if file exists and has content
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found at: {audio_file_path}")
            return "Error: Audio file not found. Download may have failed."
        
        # Get file size
        file_size = os.path.getsize(audio_file_path)
        logger.info(f"Audio file size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("Audio file is empty (0 bytes)")
            return "Error: Downloaded audio file is empty."
        
        # Initialize Groq client
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            logger.error("GROQ_API_KEY environment variable not found")
            return "Error: Groq API key not configured"
        
        groq_client = groq.Groq(api_key=groq_api_key)
        
        # Open the audio file and send to Groq's Whisper API
        try:
            with open(audio_file_path, "rb") as audio_file:
                logger.info("Sending YouTube audio file to Groq's Whisper API...")
                
                try:
                    # For larger files, let the API handle it
                    transcription = groq_client.audio.transcriptions.create(
                        file=audio_file,
                        model="whisper-large-v3",
                        prompt="",
                        response_format="text",
                        language="en",
                        temperature=0.0
                    )
                    
                    # The API can return either a string directly or an object with a text attribute
                    # Handle both cases gracefully
                    if hasattr(transcription, 'text'):
                        # Case where it's a structured response object
                        transcript = transcription.text
                    else:
                        # Case where it's a string directly
                        transcript = transcription
                    
                    if transcript and len(str(transcript).strip()) > 0:
                        logger.info(f"Groq transcription of YouTube audio completed: {len(str(transcript))} characters")
                        logger.debug(f"Transcript preview: {str(transcript)[:100]}...")
                        return transcript
                    else:
                        logger.error("Groq returned empty transcript for YouTube audio")
                        return "Error: No speech could be recognized in the YouTube audio"
                        
                except Exception as groq_error:
                    error_msg = str(groq_error)
                    logger.error(f"Groq API error for YouTube audio: {error_msg}")
                    
                    # Provide more specific error messages for common issues
                    if "authentication" in error_msg.lower():
                        return "Error: Authentication failed with the Groq API. Please check your API key."
                    elif "file size" in error_msg.lower() or "too large" in error_msg.lower():
                        return "Error: The YouTube audio file is too large for the Groq API. Try a shorter video or use the YouTube transcript API instead."
                    elif "timeout" in error_msg.lower() or "deadline" in error_msg.lower():
                        return "Error: The Groq API request timed out. This might be due to a large file or network issues. Try again with a shorter video."
                    elif "format" in error_msg.lower():
                        return "Error: The YouTube audio file format is not supported by the Groq API."
                    else:
                        return f"Error: Could not transcribe YouTube audio with Groq API. {error_msg}"
        
        except Exception as file_error:
            logger.error(f"Error opening or processing YouTube audio file: {str(file_error)}")
            return f"Error: Could not process YouTube audio file. {str(file_error)}"
            
    except Exception as e:
        logger.error(f"Error transcribing YouTube audio: {str(e)}")
        return f"Error processing YouTube audio: {str(e)}"
