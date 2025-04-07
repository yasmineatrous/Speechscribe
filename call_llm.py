import os
import groq
import logging
import trafilatura
import requests
from download import download_video_audio, delete_download
from audio import transcribe_youtube_audio

# Configure logging
logger = logging.getLogger(__name__)

def generate_structured_notes(transcript):
    """
    Generate structured notes from a transcript using Groq API
    
    Args:
        transcript (str): The speech transcript
        
    Returns:
        str: Structured notes
    """
    try:
        # Get Groq API key from environment
        api_key = os.environ.get("GROQ_API_KEY")
        
        if not api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            return "Error: GROQ API key not configured. Please set the GROQ_API_KEY environment variable."
        
        # Initialize Groq client
        client = groq.Client(api_key=api_key)
        
        # Prepare the prompt
        prompt = f"""
        I need you to organize the following transcript into professionally structured notes.
        
        Rules:
        1. Identify key topics and create a clear hierarchical structure with main headings and subheadings
        2. Use bullet points for important details and key points
        3. Use numbered lists for sequential steps, prioritized items, or chronological information
        4. Group related information together logically
        5. Highlight important concepts, definitions, actionable items, and key terms
        6. Maintain a professional flow and clear hierarchy that would be suitable for business or academic settings
        7. Correct any grammar or clarity issues, but preserve all meaningful information
        8. Remove filler words, redundancies, and informal speech patterns
        9. Create a concise and comprehensive summary at the beginning if the content is substantial
        10. Include a logical conclusion or next steps section when appropriate
        
        Here is the transcript:
        {transcript}
        
        Format the notes with:
        - Professional document structure with a clear hierarchy
        - Main section headings (using markdown # style)
        - Subsection headings (using markdown ## and ### style)
        - Bullet points (using - ) for key details and facts
        - Numbered lists for sequential steps or prioritized items
        - **Bold text** for emphasis on important terms and concepts
        - *Italic text* for definitions or specialized terminology
        - > Blockquotes for direct quotations or important statements
        - Paragraphs separated by blank lines for improved readability
        
        The result should be highly readable, professional-looking notes that effectively organize the information.
        """
        
        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-70b-8192",  # Using Llama 3 70B model for its strong capabilities
            temperature=0.1,  # Low temperature for more focused and consistent results
            max_tokens=4096,  # Allowing for ample space for structured notes
            top_p=0.9,  # Slightly reduced from default for more focused responses
        )
        
        # Extract and return the structured notes
        structured_notes = chat_completion.choices[0].message.content
        return structured_notes
    
    except Exception as e:
        logger.error(f"Error calling Groq API: {str(e)}")
        return f"Error generating structured notes: {str(e)}"

def extract_youtube_transcript(youtube_url):
    """
    Extract a transcript from a YouTube video URL using Groq AI
    
    Args:
        youtube_url (str): The YouTube video URL
        
    Returns:
        str: The extracted transcript
    """
    try:
        # Get Groq API key from environment
        api_key = os.environ.get("GROQ_API_KEY")
        
        if not api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            return "Error: GROQ API key not configured. Please set the GROQ_API_KEY environment variable."
        
        # Initialize Groq client
        client = groq.Client(api_key=api_key)
        
        # First, get the general video content using trafilatura
        try:
            downloaded = trafilatura.fetch_url(youtube_url)
            video_content = trafilatura.extract(downloaded)
        except Exception as e:
            logger.error(f"Error fetching YouTube page: {str(e)}")
            video_content = "Could not fetch video content for context."
        
        # Prepare the prompt for transcript extraction
        prompt = f"""
        I need you to extract the transcript or summarize the content from a YouTube video.
        
        The video URL is: {youtube_url}
        
        Here's some context about the video that might help:
        {video_content}
        
        Please provide a detailed transcript of the video's content following these rules:
        1. Focus on the spoken words, presentations, and important dialogue
        2. Organize it as a continuous transcript
        3. Include all significant information and key points
        4. Preserve the natural flow of the speech or presentation
        5. Format it as plain text in paragraph form
        6. Exclude timestamps, video descriptions, and metadata
        7. If you cannot access the exact transcript, provide a comprehensive summarization based on the context

        If you absolutely cannot access the video content, please acknowledge this limitation.
        """
        
        # Call Groq API for transcript extraction
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-70b-8192",
            temperature=0.2,
            max_tokens=4096,
        )
        
        # Extract and return the transcript
        transcript = chat_completion.choices[0].message.content
        
        # Check if the result indicates failure
        if "cannot access" in transcript.lower() and "video" in transcript.lower():
            return f"Error: Could not extract transcript from YouTube video. The video might be unavailable or have no captions."
        
        return transcript
    
    except Exception as e:
        logger.error(f"Error extracting YouTube transcript with Groq: {str(e)}")
        return f"Error extracting YouTube transcript: {str(e)}"

def download_and_transcribe_youtube(youtube_url):
    """
    Download audio from YouTube video and transcribe it
    
    Args:
        youtube_url (str): The YouTube video URL
        
    Returns:
        str: The extracted transcript
    """
    try:
        logger.info(f"Starting YouTube download and transcription process for: {youtube_url}")
        
        # Download the audio from YouTube
        audio_file_path = download_video_audio(youtube_url)
        
        # Check if download was successful
        if not audio_file_path or audio_file_path is None:
            logger.error("Failed to download audio from YouTube")
            return "Error: Failed to download audio from YouTube. The video might be unavailable or too large."
        
        logger.info(f"Successfully downloaded audio to: {audio_file_path}")
        
        # Transcribe the downloaded audio
        transcript = transcribe_youtube_audio(audio_file_path)
        
        # Clean up - delete the downloaded file
        delete_download(audio_file_path)
        logger.info("Deleted downloaded audio file after transcription")
        
        return transcript
        
    except Exception as e:
        logger.error(f"Error in download and transcribe process: {str(e)}")
        return f"Error processing YouTube video: {str(e)}"
