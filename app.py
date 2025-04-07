import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, session
from call_llm import generate_structured_notes, extract_youtube_transcript, download_and_transcribe_youtube
from audio import transcribe_audio, process_uploaded_audio
from youtube import get_youtube_transcript
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Logger setup
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    """Process audio data for transcription"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save the audio file temporarily
        audio_path = 'temp_audio.wav'
        audio_file.save(audio_path)
        
        # Transcribe the audio
        transcript = transcribe_audio(audio_path)
        
        # Remove the temporary file
        os.remove(audio_path)
        
        # Store transcript in session for later use
        session['transcript'] = transcript
        
        return jsonify({'transcript': transcript})
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate-notes', methods=['POST'])
def generate_notes():
    """Generate structured notes from transcript using Groq API"""
    try:
        data = request.json
        transcript = data.get('transcript', session.get('transcript', ''))
        
        if not transcript:
            return jsonify({'error': 'No transcript provided'}), 400
        
        # Generate structured notes using Groq API
        structured_notes = generate_structured_notes(transcript)
        
        # Store the structured notes in session
        session['structured_notes'] = structured_notes
        
        return jsonify({'notes': structured_notes})
    
    except Exception as e:
        logger.error(f"Error generating notes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download-pdf', methods=['GET'])
def download_pdf():
    """Generate and download PDF of structured notes"""
    try:
        notes = session.get('structured_notes', '')
        
        if not notes:
            return jsonify({'error': 'No notes available to download'}), 400
        
        # Create a PDF in memory
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Create custom styles
        styles = getSampleStyleSheet()
        
        # Custom styles for different markdown elements
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=16,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Center alignment
        )
        
        h1_style = ParagraphStyle(
            'Heading1',
            parent=styles['Heading1'],
            fontSize=16,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor('#3498db'),
            borderWidth=0,
            borderColor=colors.HexColor('#3498db'),
            borderPadding=5,
            borderRadius=None,
            allowWidows=0
        )
        
        h2_style = ParagraphStyle(
            'Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor('#2980b9'),
            allowWidows=0
        )
        
        h3_style = ParagraphStyle(
            'Heading3',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor('#0d6efd'),
            allowWidows=0
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceBefore=6,
            spaceAfter=6,
            allowWidows=0
        )
        
        bullet_style = ParagraphStyle(
            'Bullet',
            parent=normal_style,
            leftIndent=20,
            firstLineIndent=-15,
            spaceBefore=4,
            spaceAfter=4
        )
        
        blockquote_style = ParagraphStyle(
            'Blockquote',
            parent=normal_style,
            leftIndent=30,
            rightIndent=30,
            fontStyle='italic',
            textColor=colors.HexColor('#6c757d'),
            spaceBefore=8,
            spaceAfter=8,
            borderWidth=1,
            borderColor=colors.HexColor('#dee2e6'),
            borderPadding=8,
            borderRadius=6
        )
        
        elements = []
        
        # Add title
        elements.append(Paragraph("Structured Notes", title_style))
        elements.append(Spacer(1, 20))
        
        # Process the markdown content
        lines = notes.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Process headings
            if line.startswith('# '):
                elements.append(Paragraph(line[2:], h1_style))
            elif line.startswith('## '):
                elements.append(Paragraph(line[3:], h2_style))
            elif line.startswith('### '):
                elements.append(Paragraph(line[4:], h3_style))
            
            # Process blockquotes
            elif line.startswith('> '):
                blockquote_text = line[2:]
                elements.append(Paragraph(blockquote_text, blockquote_style))
            
            # Process bullet points
            elif line.startswith('- ') or line.startswith('* '):
                bullet_text = f"• {line[2:]}"
                elements.append(Paragraph(bullet_text, bullet_style))
            
            # Process numbered lists
            elif line.strip() and line[0].isdigit() and '. ' in line:
                num, text = line.split('. ', 1)
                num_text = f"{num}. {text}"
                elements.append(Paragraph(num_text, bullet_style))
            
            # Process regular paragraphs
            else:
                # Handle bold text with ** or __
                processed_line = line
                processed_line = processed_line.replace('**', '<b>', 1)
                if '**' in processed_line:
                    processed_line = processed_line.replace('**', '</b>', 1)
                
                processed_line = processed_line.replace('__', '<b>', 1)
                if '__' in processed_line:
                    processed_line = processed_line.replace('__', '</b>', 1)
                
                # Handle italic text with * or _
                processed_line = processed_line.replace('*', '<i>', 1)
                if '*' in processed_line:
                    processed_line = processed_line.replace('*', '</i>', 1)
                
                processed_line = processed_line.replace('_', '<i>', 1)
                if '_' in processed_line:
                    processed_line = processed_line.replace('_', '</i>', 1)
                
                elements.append(Paragraph(processed_line, normal_style))
            
            i += 1
        
        # Build the PDF
        doc.build(elements)
        
        # Prepare the PDF for download
        buffer.seek(0)
        
        return send_file(
            buffer,
            download_name='structured_notes.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )
    
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save-transcript', methods=['POST'])
def save_transcript():
    """Save the transcript from the client side to the session"""
    try:
        data = request.json
        transcript = data.get('transcript', '')
        
        if not transcript:
            return jsonify({'error': 'No transcript provided'}), 400
        
        # Save to session
        session['transcript'] = transcript
        
        return jsonify({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Error saving transcript: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe-audio-file', methods=['POST'])
def transcribe_audio_file():
    """Process and transcribe an uploaded audio file (MP3, WAV, etc.)"""
    try:
        # Log request data for debugging
        logger.info(f"Request files: {list(request.files.keys())}")
        logger.info(f"Request Content-Type: {request.content_type}")
        
        # Check if file was uploaded
        if 'audio_file' not in request.files:
            logger.error("No 'audio_file' in request.files")
            return jsonify({'error': 'No audio file provided. Make sure the file is named "audio_file" in the request.'}), 400
        
        audio_file = request.files['audio_file']
        logger.info(f"Received file: {audio_file.filename}, size: {audio_file.content_length if hasattr(audio_file, 'content_length') else 'unknown'}")
        
        # Check if file was selected
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.flac'}
        file_ext = os.path.splitext(audio_file.filename)[1].lower()
        logger.info(f"File extension: {file_ext}")
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'error': f'Unsupported file format. Allowed formats: {", ".join(allowed_extensions)}'
            }), 400
        
        # Make sure uploads directory exists
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Process and transcribe the audio file
        logger.info("Starting audio transcription process...")
        
        try:
            transcript = process_uploaded_audio(audio_file)
            logger.info(f"Transcription complete: {transcript[:50]}...")
            
            # Check if there was an error
            if transcript.startswith('Error'):
                logger.error(f"Error transcribing audio file: {transcript}")
                return jsonify({'error': transcript}), 400
                
            if transcript.startswith('⚠️'):
                # This is a special case for when online recognition fails but we still want to return a user-friendly message
                logger.warning("Using fallback message because online services were unavailable")
                return jsonify({'error': transcript}), 503  # Service Unavailable
                
            # Store transcript in session for later use
            session['transcript'] = transcript
            
            return jsonify({'transcript': transcript})
            
        except Exception as process_error:
            logger.error(f"Error in process_uploaded_audio: {str(process_error)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Provide a user-friendly message
            error_message = "Sorry, we couldn't process your audio file. This could be due to network restrictions or an unsupported audio format. Please try using YouTube transcription instead."
            return jsonify({'error': error_message}), 500
    
    except Exception as e:
        logger.error(f"Error processing audio file: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())  # Log full traceback
        return jsonify({'error': f"Failed to process audio file: {str(e)}"}), 500

@app.route('/transcribe-youtube', methods=['POST'])
def transcribe_youtube():
    """Get and process transcript from YouTube video"""
    try:
        data = request.json
        youtube_url = data.get('youtube_url', '')
        
        if not youtube_url:
            return jsonify({'error': 'No YouTube URL provided'}), 400
        
        # Validate the URL format
        if not youtube_url.startswith(('https://www.youtube.com/', 'https://youtu.be/', 'https://youtube.com/')):
            return jsonify({'error': 'Invalid YouTube URL. Please provide a valid YouTube URL starting with https://www.youtube.com/ or https://youtu.be/'}), 400
            
        # Step 1: First check if we can get a quick response from YouTube API
        try:
            logger.info(f"Attempting to fetch transcript via YouTube API for: {youtube_url}")
            transcript = get_youtube_transcript(youtube_url)
            
            # If YouTube API worked, use it right away (fastest method)
            if not transcript.startswith('Error'):
                logger.info("YouTube API successfully retrieved transcript")
                session['transcript'] = transcript
                return jsonify({'transcript': transcript})
                
            logger.info(f"YouTube API failed: {transcript}")
        except Exception as youtube_api_error:
            logger.info(f"YouTube API error: {str(youtube_api_error)}")
        
        # Step 2: Try direct download and transcription
        logger.info(f"Starting download and transcription process for: {youtube_url}")
        
        # Send an initial response to let the user know processing has started
        # Using an intermediate status helps with longer videos
        processing_message = "Processing your YouTube video. For longer videos (>10 min), this may take a few moments..."
        
        # Return the actual transcript
        transcript = download_and_transcribe_youtube(youtube_url)
        
        # If download and transcribe fails, use Groq API as final fallback
        if transcript.startswith('Error'):
            logger.info(f"Download method failed: {transcript}")
            logger.info(f"Using Groq API as final fallback for: {youtube_url}")
            
            try:
                transcript = extract_youtube_transcript(youtube_url)
            except Exception as groq_error:
                logger.error(f"Groq API fallback error: {str(groq_error)}")
                return jsonify({'error': f"Failed to transcribe video. {str(groq_error)}"}), 500
        
        # Check if we still have an error after all attempts
        if transcript.startswith('Error'):
            logger.error(f"All transcription methods failed for: {youtube_url}")
            return jsonify({'error': transcript}), 400
        
        # Store transcript in session for later use
        session['transcript'] = transcript
        
        # Return the successful transcript
        return jsonify({'transcript': transcript})
    
    except Exception as e:
        logger.error(f"Error getting YouTube transcript: {str(e)}")
        return jsonify({'error': f"Failed to process YouTube video: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
