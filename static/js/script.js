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
    const youtubeUrlInput = document.getElementById('youtube-url');
    const transcribeYoutubeBtn = document.getElementById('transcribe-youtube');
    const manualTranscriptInput = document.getElementById('manual-transcript');
    const useManualTranscriptBtn = document.getElementById('use-manual-transcript');
    // Audio file upload elements
    const audioFileInput = document.getElementById('audio-file-input');
    const uploadAudioBtn = document.getElementById('upload-audio-btn');
    const audioUploadProgress = document.getElementById('audio-upload-progress');
    
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
            recordingIndicator.classList.remove('d-none');
            recordingIndicator.classList.add('recording');
            startRecordingBtn.classList.add('d-none');
            stopRecordingBtn.classList.remove('d-none');
        };
        
        recognition.onend = function() {
            isRecording = false;
            recordingStatus.textContent = 'Not recording';
            recordingIndicator.classList.add('d-none');
            recordingIndicator.classList.remove('recording');
            startRecordingBtn.classList.remove('d-none');
            stopRecordingBtn.classList.add('d-none');
        };
        
        recognition.onresult = function(event) {
            interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + ' ';
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }
            
            updateTranscriptDisplay();
            
            // Save transcript periodically
            if (finalTranscript.trim() !== '') {
                saveTranscriptToServer(finalTranscript);
            }
        };
        
        recognition.onerror = function(event) {
            let errorMsg = '';
            
            switch(event.error) {
                case 'no-speech':
                    errorMsg = 'No speech detected. Please try again.';
                    break;
                case 'audio-capture':
                    errorMsg = 'No microphone detected. Please check your microphone settings.';
                    break;
                case 'not-allowed':
                    errorMsg = 'Microphone access denied. Please allow microphone access.';
                    break;
                default:
                    errorMsg = `Error: ${event.error}`;
            }
            
            showError(errorMsg);
            
            // Stop recording on error
            if (isRecording) {
                recognition.stop();
            }
        };
    }
    
    // Function to start recording
    function startRecording() {
        finalTranscript = '';
        interimTranscript = '';
        transcriptElement.textContent = '';
        structuredNotesElement.innerHTML = '';
        
        try {
            recognition.start();
        } catch (e) {
            console.error('Recognition error:', e);
            showError(`Error starting recognition: ${e.message}`);
        }
    }
    
    // Function to stop recording
    function stopRecording() {
        if (isRecording) {
            recognition.stop();
        }
    }
    
    // Update transcript display
    function updateTranscriptDisplay() {
        transcriptElement.textContent = finalTranscript + interimTranscript;
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
    
    // Function to render Markdown content safely
    function renderMarkdown(markdownText) {
        // Convert markdown to HTML using marked.js
        const rawHtml = marked.parse(markdownText);
        
        // Sanitize the HTML using DOMPurify
        const sanitizedHtml = DOMPurify.sanitize(rawHtml, {
            ADD_ATTR: ['target'],
            ALLOWED_TAGS: [
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'p', 'a', 'ul', 'ol', 
                'nl', 'li', 'b', 'i', 'strong', 'em', 'strike', 'code', 'hr', 'br', 'div', 
                'table', 'thead', 'caption', 'tbody', 'tr', 'th', 'td', 'pre', 'span'
            ],
        });
        
        return sanitizedHtml;
    }
    
    // YouTube transcript function
    function getYoutubeTranscript() {
        const youtubeUrl = youtubeUrlInput.value.trim();
        
        if (!youtubeUrl) {
            showError('Please enter a valid YouTube URL');
            return;
        }
        
        // Validate URL format
        if (!youtubeUrl.startsWith('https://www.youtube.com/') && 
            !youtubeUrl.startsWith('https://youtu.be/') &&
            !youtubeUrl.startsWith('https://youtube.com/')) {
            showError('Please enter a valid YouTube URL starting with https://www.youtube.com/ or https://youtu.be/');
            return;
        }
        
        // Disable buttons and show loading
        transcribeYoutubeBtn.disabled = true;
        finalTranscript = '';
        
        // Show detailed loading message with spinner
        transcriptElement.innerHTML = `
            <div class="text-center my-5">
                <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h5 class="mt-3">Extracting transcript from YouTube...</h5>
                <p class="text-muted">This may take several moments for longer videos.</p>
                <div class="progress mt-3" style="height: 10px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
                </div>
            </div>
        `;
        
        // Set a timeout to update the message for longer videos
        const longVideoTimeout = setTimeout(() => {
            transcriptElement.innerHTML = `
                <div class="text-center my-5">
                    <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h5 class="mt-3">Still working...</h5>
                    <p class="text-muted">Downloading and processing video audio.</p>
                    <p class="text-muted">For videos longer than 10 minutes, this may take a minute or two.</p>
                    <div class="progress mt-3" style="height: 10px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
                    </div>
                </div>
            `;
        }, 5000);
        
        // Call API to get YouTube transcript
        fetch('/transcribe-youtube', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ youtube_url: youtubeUrl }),
        })
        .then(response => {
            clearTimeout(longVideoTimeout);
            return response.json();
        })
        .then(data => {
            transcribeYoutubeBtn.disabled = false;
            
            if (data.error) {
                showError(data.error);
                transcriptElement.textContent = 'Error loading transcript. Please try again.';
            } else {
                finalTranscript = data.transcript;
                
                // Show success notification
                const successAlert = document.createElement('div');
                successAlert.className = "alert alert-success mb-3";
                successAlert.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i> Transcript successfully extracted!';
                
                // Insert success notification
                transcriptElement.innerHTML = '';
                transcriptElement.parentNode.insertBefore(successAlert, transcriptElement);
                
                // Set transcript text
                transcriptElement.textContent = finalTranscript;
                generateNotesBtn.disabled = false;
                
                // Remove notification after 3 seconds
                setTimeout(() => {
                    successAlert.remove();
                }, 3000);
            }
        })
        .catch(error => {
            clearTimeout(longVideoTimeout);
            transcribeYoutubeBtn.disabled = false;
            console.error('Error getting YouTube transcript:', error);
            showError(`Error getting YouTube transcript: ${error.message}`);
            transcriptElement.textContent = 'Error loading transcript. Please try again.';
        });
    }
    
    // Generate notes from transcript
    function generateNotes() {
        if (finalTranscript.trim() === '') {
            showError('Please record some speech or get a YouTube transcript before generating notes.');
            return;
        }
        
        // Show loading state
        notesLoading.classList.remove('d-none');
        generateNotesBtn.disabled = true;
        structuredNotesElement.innerHTML = '<em>Generating...</em>';
        
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
            generateNotesBtn.disabled = false;
            notesLoading.classList.add('d-none');
            
            if (data.error) {
                showError(data.error);
                structuredNotesElement.innerHTML = '<em>Error generating notes. Please try again.</em>';
            } else {
                // Render markdown content
                structuredNotesElement.innerHTML = renderMarkdown(data.notes);
                downloadPDFBtn.disabled = false;
                
                // Show success notification
                const successAlert = document.createElement('div');
                successAlert.className = "alert alert-success mb-3";
                successAlert.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i> Notes successfully generated!';
                
                // Insert before the notes
                structuredNotesElement.parentNode.insertBefore(successAlert, structuredNotesElement);
                
                // Remove after 3 seconds
                setTimeout(() => {
                    successAlert.remove();
                }, 3000);
            }
        })
        .catch(error => {
            generateNotesBtn.disabled = false;
            notesLoading.classList.add('d-none');
            console.error('Error generating notes:', error);
            showError(`Error generating notes: ${error.message}`);
            structuredNotesElement.innerHTML = '<em>Error generating notes. Please try again.</em>';
        });
    }
    
    // Function to clear transcript
    function clearTranscript() {
        finalTranscript = '';
        interimTranscript = '';
        transcriptElement.textContent = '';
        structuredNotesElement.innerHTML = '';
        generateNotesBtn.disabled = true;
        downloadPDFBtn.disabled = true;
    }
    
    // Download PDF function
    function downloadPDF() {
        const notes = structuredNotesElement.innerHTML;
        
        if (!notes) {
            showError('Please generate notes before downloading PDF.');
            return;
        }
        
        // Create a form and submit it to trigger PDF download
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/download-pdf';
        
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'notes_html';
        input.value = notes;
        
        form.appendChild(input);
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    }
    
    // Function to use manual transcript
    function useManualTranscript() {
        const transcript = manualTranscriptInput.value.trim();
        
        if (!transcript) {
            showError('Please enter a transcript before proceeding.');
            return;
        }
        
        finalTranscript = transcript;
        transcriptElement.textContent = finalTranscript;
        generateNotesBtn.disabled = false;
        saveTranscriptToServer(finalTranscript);
    }

    // Function to upload and process audio file
    function uploadAndProcessAudio() {
        const fileInput = audioFileInput;
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showError('Please select an audio file to upload.');
            return;
        }
        
        const file = fileInput.files[0];
        
        // Check file type
        const allowedTypes = ['.mp3', '.wav', '.m4a', '.ogg', '.flac'];
        const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            showError(`Unsupported file format. Allowed formats: ${allowedTypes.join(', ')}`);
            return;
        }
        
        // Check file size (limit to 100MB)
        const maxSize = 100 * 1024 * 1024; // 100MB in bytes
        if (file.size > maxSize) {
            showError(`File is too large. Maximum file size is 100MB.`);
            return;
        }
        
        // Show progress and disable button
        audioUploadProgress.classList.remove('d-none');
        uploadAudioBtn.disabled = true;
        
        // Clear previous transcript
        finalTranscript = '';
        
        // Show detailed loading indicator in the transcript area
        transcriptElement.innerHTML = `
            <div class="text-center my-5">
                <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h5 class="mt-3">Processing audio file...</h5>
                <p class="text-muted">Converting and transcribing the audio. This may take a moment.</p>
                <div class="progress mt-3" style="height: 10px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" style="width: 100%"></div>
                </div>
            </div>
        `;
        
        structuredNotesElement.innerHTML = '';
        
        // Create form data
        const formData = new FormData();
        formData.append('audio_file', file);
        
        // Send audio file to server for transcription
        fetch('/transcribe-audio-file', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            audioUploadProgress.classList.add('d-none');
            uploadAudioBtn.disabled = false;
            
            if (data.error) {
                showError(data.error);
                transcriptElement.textContent = 'Error processing audio file. Please try again.';
            } else {
                finalTranscript = data.transcript;
                
                // Show success notification
                const successAlert = document.createElement('div');
                successAlert.className = "alert alert-success mb-3";
                successAlert.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i> Audio successfully transcribed!';
                
                // Insert before transcript
                transcriptElement.innerHTML = '';
                transcriptElement.parentNode.insertBefore(successAlert, transcriptElement);
                
                // Set transcript and enable generate button
                transcriptElement.textContent = finalTranscript;
                generateNotesBtn.disabled = false;
                
                // Remove notification after 3 seconds
                setTimeout(() => {
                    successAlert.remove();
                }, 3000);
            }
        })
        .catch(error => {
            audioUploadProgress.classList.add('d-none');
            uploadAudioBtn.disabled = false;
            console.error('Error processing audio file:', error);
            showError(`Error processing audio file: ${error.message}`);
            transcriptElement.textContent = 'Error processing audio file. Please try again.';
        });
    }
    
    // Event listeners
    startRecordingBtn.addEventListener('click', startRecording);
    stopRecordingBtn.addEventListener('click', stopRecording);
    clearTranscriptBtn.addEventListener('click', clearTranscript);
    generateNotesBtn.addEventListener('click', generateNotes);
    downloadPDFBtn.addEventListener('click', downloadPDF);
    transcribeYoutubeBtn.addEventListener('click', getYoutubeTranscript);
    useManualTranscriptBtn.addEventListener('click', useManualTranscript);
    uploadAudioBtn.addEventListener('click', uploadAndProcessAudio);
    
    // Handle keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Start recording with Ctrl+Shift+R
        if (e.ctrlKey && e.shiftKey && e.key === 'R') {
            e.preventDefault();
            if (!isRecording && !startRecordingBtn.disabled) {
                startRecording();
            }
        }
        
        // Stop recording with Ctrl+Shift+S
        if (e.ctrlKey && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            if (isRecording) {
                stopRecording();
            }
        }
    });
    
    // Handle page unload to stop recording
    window.addEventListener('beforeunload', () => {
        if (isRecording) {
            recognition.stop();
        }
    });
});
