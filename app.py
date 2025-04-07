import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, session
from call_llm import generate_structured_notes
from audio import transcribe_audio
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

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
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Add title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12
        )
        elements.append(Paragraph("Structured Notes", title_style))
        elements.append(Spacer(1, 12))
        
        # Add content
        content_style = ParagraphStyle(
            'Content',
            parent=styles['Normal'],
            fontSize=10,
            leading=14
        )
        
        # Split by lines to maintain formatting
        lines = notes.split('\n')
        for line in lines:
            if line.strip():
                elements.append(Paragraph(line, content_style))
                elements.append(Spacer(1, 6))
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
