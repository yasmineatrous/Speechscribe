// Main JavaScript for the Speech to Structured Notes application

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const startRecordingBtn = document.getElementById('startRecording');
    const stopRecordingBtn = document.getElementById('stopRecording');
    const clearTranscriptBtn = document.getElementById('clearTranscript');
    const generateNotesBtn = document.getElementById('generateNotes');
    const downloadPDFBtn = document.getElementById('downloadPDF');
    const transcriptElement = document.getElementById('transcript');
    const structuredNotesElement = document.getElementById('structured-notes');
    const recordingStatus = document.getElementById('status-text');
    const recordingIndicator = document.getElementById('recording-indicator');
    const notesLoading = document.getElementById('notes-loading');
    
    // Global variables
    let recognition = null;
    let finalTranscript = '';
    let interimTranscript = '';
    let isRecording = false;
    
    // Error handling function
    function showError(message) {
        const errorMessage = document.getElementById('error-message');
        errorMessage.textContent = message;
        
        // Show the modal
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
    }
    
    // Check if the browser supports speech recognition
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        startRecordingBtn.disabled = true;
        showError('Your browser does not support speech recognition. Please use Chrome or Edge.');
    } else {
        // Initialize speech recognition
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        // Speech recognition events
        recognition.onstart = function() {
            isRecording = true;
            recordingStatus.textContent = 'Recording...';
            recordingIndicator.textContent = '🔴';
            recordingIndicator.classList.add('active');
            startRecordingBtn.disabled = true;
            stopRecordingBtn.disabled = false;
            generateNotesBtn.disabled = true;
        };
        
        recognition.onend = function() {
            isRecording = false;
            recordingStatus.textContent = 'Not Recording';
            recordingIndicator.textContent = '⚪';
            recordingIndicator.classList.remove('active');
            startRecordingBtn.disabled = false;
            stopRecordingBtn.disabled = true;
            generateNotesBtn.disabled = finalTranscript.trim() === '';
            
            // Save the transcript to the server
            if (finalTranscript.trim() !== '') {
                saveTranscriptToServer(finalTranscript);
            }
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error', event.error);
            showError(`Speech recognition error: ${event.error}`);
            stopRecording();
        };
        
        recognition.onresult = function(event) {
            interimTranscript = '';
            
            // Process the results
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                
                if (event.results[i].isFinal) {
                    finalTranscript += ' ' + transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // Update the display
            updateTranscriptDisplay();
        };
    }
    
    // Start recording function
    function startRecording() {
        try {
            finalTranscript = '';
            interimTranscript = '';
            transcriptElement.textContent = 'Listening...';
            recognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            showError(`Error starting speech recognition: ${error.message}`);
        }
    }
    
    // Stop recording function
    function stopRecording() {
        if (isRecording) {
            recognition.stop();
        }
    }
    
    // Update the transcript display
    function updateTranscriptDisplay() {
        transcriptElement.innerHTML = '';
        
        // Add final transcript words
        if (finalTranscript) {
            const finalWords = finalTranscript.trim().split(' ');
            finalWords.forEach(word => {
                const wordSpan = document.createElement('span');
                wordSpan.className = 'word final-word';
                wordSpan.textContent = word + ' ';
                transcriptElement.appendChild(wordSpan);
            });
        }
        
        // Add interim transcript words
        if (interimTranscript) {
            const interimWords = interimTranscript.trim().split(' ');
            interimWords.forEach(word => {
                const wordSpan = document.createElement('span');
                wordSpan.className = 'word interim-word';
                wordSpan.textContent = word + ' ';
                transcriptElement.appendChild(wordSpan);
            });
        }
        
        // If empty, show placeholder
        if (!finalTranscript && !interimTranscript) {
            transcriptElement.textContent = 'Your speech will appear here...';
        }
        
        // Enable/disable generate notes button
        generateNotesBtn.disabled = finalTranscript.trim() === '';
    }
    
    // Save transcript to server
    function saveTranscriptToServer(transcript) {
        fetch('/save-transcript', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ transcript: transcript.trim() }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            }
        })
        .catch(error => {
            console.error('Error saving transcript:', error);
            showError(`Error saving transcript: ${error.message}`);
        });
    }
    
    // Generate notes from transcript
    function generateNotes() {
        if (finalTranscript.trim() === '') {
            showError('Please record some speech before generating notes.');
            return;
        }
        
        // Show loading state
        notesLoading.classList.remove('d-none');
        generateNotesBtn.disabled = true;
        structuredNotesElement.textContent = 'Generating...';
        
        // Call API to generate notes
        fetch('/generate-notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ transcript: finalTranscript.trim() }),
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading state
            notesLoading.classList.add('d-none');
            generateNotesBtn.disabled = false;
            
            if (data.error) {
                showError(data.error);
                structuredNotesElement.textContent = 'Error generating notes. Please try again.';
            } else {
                structuredNotesElement.textContent = data.notes;
                downloadPDFBtn.disabled = false;
            }
        })
        .catch(error => {
            // Hide loading state
            notesLoading.classList.add('d-none');
            generateNotesBtn.disabled = false;
            
            console.error('Error generating notes:', error);
            showError(`Error generating notes: ${error.message}`);
            structuredNotesElement.textContent = 'Error generating notes. Please try again.';
        });
    }
    
    // Clear transcript function
    function clearTranscript() {
        finalTranscript = '';
        interimTranscript = '';
        updateTranscriptDisplay();
        generateNotesBtn.disabled = true;
        downloadPDFBtn.disabled = true;
        structuredNotesElement.textContent = 'Generated notes will appear here...';
    }
    
    // Download PDF function
    function downloadPDF() {
        window.open('/download-pdf', '_blank');
    }
    
    // Event listeners
    startRecordingBtn.addEventListener('click', startRecording);
    stopRecordingBtn.addEventListener('click', stopRecording);
    clearTranscriptBtn.addEventListener('click', clearTranscript);
    generateNotesBtn.addEventListener('click', generateNotes);
    downloadPDFBtn.addEventListener('click', downloadPDF);
    
    // Handle page unload to stop recording
    window.addEventListener('beforeunload', () => {
        if (isRecording) {
            recognition.stop();
        }
    });
});
