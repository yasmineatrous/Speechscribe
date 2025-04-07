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
