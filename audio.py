import speech_recognition as sr
import logging
import os
import tempfile
import groq

# Configure logging
logger = logging.getLogger(__name__)

def transcribe_audio(audio_file_path):
    """
    Transcribe audio file to text using speech recognition
    
    Args:
        audio_file_path (str): Path to the audio file
        
    Returns:
        str: Transcribed text
    """
    try:
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Load the audio file
        with sr.AudioFile(audio_file_path) as source:
            # Adjust for ambient noise and record
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)
            
            # Use Google's speech recognition
            text = recognizer.recognize_google(audio_data)
            logger.debug(f"Transcription completed: {text[:30]}...")
            return text
            
    except sr.UnknownValueError:
        logger.error("Google Speech Recognition could not understand audio")
        return "Could not understand audio. Please try again."
    
    except sr.RequestError as e:
        logger.error(f"Google Speech Recognition service error: {str(e)}")
        return f"Speech recognition service error: {str(e)}"
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
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

def transcribe_youtube_audio(audio_file_path):
    """
    Transcribe YouTube audio file using Groq API
    
    Args:
        audio_file_path (str): Path to the downloaded audio file
        
    Returns:
        str: Transcribed text
    """
    try:
        logger.info(f"Transcribing YouTube audio from: {audio_file_path}")
        
        # First check if the file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found at: {audio_file_path}")
            return "Audio file not found. Download may have failed."
        
        # Use the SpeechRecognition library with the local audio file
        return transcribe_audio(audio_file_path)
        
    except Exception as e:
        logger.error(f"Error transcribing YouTube audio: {str(e)}")
        return f"Error processing YouTube audio: {str(e)}"
