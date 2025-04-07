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
    Transcribe YouTube audio file
    
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
            return "Error: Audio file not found. Download may have failed."
        
        # Get file size
        file_size = os.path.getsize(audio_file_path)
        logger.info(f"Audio file size: {file_size} bytes")
        
        if file_size == 0:
            logger.error("Audio file is empty (0 bytes)")
            return "Error: Downloaded audio file is empty."
        
        # Initialize the speech recognizer
        try:
            recognizer = sr.Recognizer()
            
            # Load the audio file
            logger.info("Loading audio file into speech recognizer")
            
            # For longer files, we'll split the audio into chunks
            with sr.AudioFile(audio_file_path) as source:
                # Adjust recognition parameters for better results
                recognizer.energy_threshold = 300  # Increased from default for better noise handling
                recognizer.dynamic_energy_threshold = True  # Adapts to ambient noise
                recognizer.pause_threshold = 0.8  # Shorter pause detection for more accurate transcription
                
                # For longer files, we'll process in chunks
                if file_size > 10 * 1024 * 1024:  # If more than 10MB
                    logger.info("Large audio file detected, processing in chunks")
                    
                    # Get audio duration from the file
                    audio_duration = source.DURATION
                    
                    # If audio_duration is not available, estimate it based on file size
                    if not audio_duration:
                        # Rough estimate: 1MB ≈ 1 minute of audio at typical bit rates
                        audio_duration = (file_size / (1024 * 1024)) * 60
                    
                    logger.info(f"Estimated audio duration: {audio_duration} seconds")
                    
                    # Process in chunks of 30 seconds with 2-second overlap
                    chunk_duration = 30  # seconds
                    overlap = 2  # seconds
                    
                    # Calculate the number of chunks
                    num_chunks = int(audio_duration / (chunk_duration - overlap)) + 1
                    
                    # Initialize transcript list
                    transcript_chunks = []
                    
                    # Process each chunk
                    for i in range(num_chunks):
                        start_time = max(0, i * (chunk_duration - overlap))
                        end_time = min(audio_duration, start_time + chunk_duration)
                        
                        if end_time <= start_time:
                            break
                        
                        logger.info(f"Processing chunk {i+1}/{num_chunks} ({start_time}-{end_time}s)")
                        
                        # Adjust the recognizer to the current position
                        source.rewind()  # Rewind to beginning
                        source.stream.read(int(start_time * source.SAMPLE_RATE * source.SAMPLE_WIDTH))  # Skip to start_time
                        
                        # Record chunk
                        chunk_audio = recognizer.record(source, duration=end_time-start_time)
                        
                        try:
                            # Try with multiple language options for better results
                            languages = ['en-US', 'en-GB', 'en-AU']  # Different English variants
                            success = False
                            
                            for language in languages:
                                try:
                                    # Use Google's speech recognition service with specific language
                                    logger.info(f"Trying language: {language} for chunk {i+1}")
                                    chunk_text = recognizer.recognize_google(chunk_audio, language=language)
                                    transcript_chunks.append(chunk_text)
                                    success = True
                                    break  # Stop trying languages if one works
                                except sr.UnknownValueError:
                                    continue  # Try the next language
                                except sr.RequestError:
                                    break  # Network error, don't try more languages
                            
                            if not success:
                                logger.warning(f"Could not understand audio in chunk {i+1} with any language")
                                # Add a placeholder for empty chunks to maintain timing
                                transcript_chunks.append("")
                                
                        except sr.RequestError as e:
                            logger.error(f"Google Speech Recognition service error in chunk {i+1}: {str(e)}")
                            # Continue with next chunk on error
                    
                    # Combine all chunks
                    transcript = " ".join(transcript_chunks)
                else:
                    # For smaller files, process the entire file at once
                    logger.info("Processing audio file in one go")
                    audio_data = recognizer.record(source)
                    
                    # Try with multiple language options for better results
                    languages = ['en-US', 'en-GB', 'en-AU']  # Different English variants
                    transcript = None
                    
                    for language in languages:
                        try:
                            # Use Google's speech recognition service with specific language
                            logger.info(f"Trying language: {language} for full audio")
                            transcript = recognizer.recognize_google(audio_data, language=language)
                            if transcript and transcript.strip():
                                break  # Stop trying languages if one works
                        except sr.UnknownValueError:
                            continue  # Try the next language
                        except sr.RequestError as e:
                            logger.error(f"Google Speech Recognition service error: {str(e)}")
                            raise e  # Re-raise to be caught by outer exception handler
                    
                    # If all languages failed, set empty transcript to trigger error below
                    if not transcript:
                        transcript = ""
                
                # Check if we got a valid transcript
                if not transcript or transcript.strip() == "":
                    logger.warning("Speech recognition returned empty result")
                    return "Error: No speech could be recognized in the audio."
                
                logger.info(f"Transcription successful, got {len(transcript)} characters")
                return transcript
        
        except sr.UnknownValueError:
            logger.error("Google Speech Recognition could not understand audio")
            return "Error: Could not understand audio. The speech might be unclear or in an unsupported language."
            
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition service error: {str(e)}")
            return f"Error: Could not request results from speech recognition service. {str(e)}"
        
    except Exception as e:
        logger.error(f"Error transcribing YouTube audio: {str(e)}")
        return f"Error processing YouTube audio: {str(e)}"
