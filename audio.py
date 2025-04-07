import speech_recognition as sr
import logging
import os
import tempfile
import groq
from pydub import AudioSegment
import uuid
import time

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
                        model="distil-whisper-large-v3-en",
                        prompt="",
                        response_format="text",
                        language="en",
                        temperature=0.0
                    )
                    
                    # Get the transcription text
                    transcript = transcription.text
                    
                    if transcript and len(transcript.strip()) > 0:
                        logger.info(f"Groq transcription completed: {transcript[:50]}...")
                        return transcript
                    else:
                        logger.error("Groq returned empty transcript")
                        return "Error: No speech could be recognized in the audio"
                        
                except Exception as groq_error:
                    logger.error(f"Groq API error: {str(groq_error)}")
                    return f"Error: Could not transcribe with Groq API. {str(groq_error)}"
                    
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

def process_uploaded_audio(uploaded_file):
    """
    Process and transcribe an uploaded audio file (MP3, WAV, etc.)
    
    Args:
        uploaded_file: The uploaded file object from Flask request.files
        
    Returns:
        str: Transcribed text from the audio file
    """
    try:
        logger.info(f"Processing uploaded audio file: {uploaded_file.filename}")
        
        # Create a unique filename to avoid conflicts
        file_id = str(uuid.uuid4())
        original_filename = uploaded_file.filename
        file_extension = os.path.splitext(original_filename)[1].lower()
        
        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded file
        temp_input_path = os.path.join(temp_dir, f"{file_id}{file_extension}")
        uploaded_file.save(temp_input_path)
        
        # Convert to WAV if not already WAV (SpeechRecognition requires WAV)
        wav_path = os.path.join(temp_dir, f"{file_id}.wav")
        
        if file_extension.lower() != '.wav':
            logger.info(f"Converting {file_extension} file to WAV format")
            try:
                # Load the audio file with pydub
                if file_extension.lower() == '.mp3':
                    audio = AudioSegment.from_mp3(temp_input_path)
                elif file_extension.lower() == '.m4a':
                    audio = AudioSegment.from_file(temp_input_path, format="m4a")
                elif file_extension.lower() == '.ogg':
                    audio = AudioSegment.from_ogg(temp_input_path)
                else:
                    # Try generic loading for other formats
                    audio = AudioSegment.from_file(temp_input_path)
                
                # Convert to WAV format at 16kHz (good for speech recognition)
                audio = audio.set_frame_rate(16000)
                audio.export(wav_path, format="wav")
                
                logger.info(f"Audio conversion successful: {wav_path}")
            except Exception as e:
                logger.error(f"Error converting audio file: {str(e)}")
                # Clean up the original temp file
                if os.path.exists(temp_input_path):
                    os.remove(temp_input_path)
                return f"Error: Could not convert audio file. {str(e)}"
        else:
            # If already WAV, just use the original file
            wav_path = temp_input_path
        
        # Transcribe the WAV file
        transcript = transcribe_audio(wav_path)
        
        # Clean up temporary files
        try:
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
            if wav_path != temp_input_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception as e:
            logger.warning(f"Error removing temporary files: {str(e)}")
        
        return transcript
        
    except Exception as e:
        logger.error(f"Error processing uploaded audio: {str(e)}")
        return f"Error processing audio file: {str(e)}"

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
                        model="distil-whisper-large-v3-en",
                        prompt="",
                        response_format="text",
                        language="en",
                        temperature=0.0
                    )
                    
                    # Get the transcription text
                    transcript = transcription.text
                    
                    if transcript and len(transcript.strip()) > 0:
                        logger.info(f"Groq transcription of YouTube audio completed: {len(transcript)} characters")
                        logger.debug(f"Transcript preview: {transcript[:100]}...")
                        return transcript
                    else:
                        logger.error("Groq returned empty transcript for YouTube audio")
                        return "Error: No speech could be recognized in the YouTube audio"
                        
                except Exception as groq_error:
                    logger.error(f"Groq API error for YouTube audio: {str(groq_error)}")
                    return f"Error: Could not transcribe YouTube audio with Groq API. {str(groq_error)}"
        
        except Exception as file_error:
            logger.error(f"Error opening or processing YouTube audio file: {str(file_error)}")
            return f"Error: Could not process YouTube audio file. {str(file_error)}"
            
    except Exception as e:
        logger.error(f"Error transcribing YouTube audio: {str(e)}")
        return f"Error processing YouTube audio: {str(e)}"
