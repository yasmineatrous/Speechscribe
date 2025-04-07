import os
import groq
import logging

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
        I need you to organize the following transcript into well-structured notes.
        
        Rules:
        1. Identify key topics and create clear headings
        2. Use bullet points for important details
        3. Group related information together
        4. Highlight important concepts, definitions, or actionable items
        5. Maintain a logical flow and hierarchy
        6. Correct any grammar or clarity issues, but preserve all information
        7. Remove filler words and redundancies
        
        Here is the transcript:
        {transcript}
        
        Format the notes with:
        - Clear section headings (using markdown # or ## style)
        - Bullet points for key details
        - Numbered lists for sequential steps or prioritized items
        - Bold text for emphasis on important terms
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
