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
    
    // File upload functionality
    const audioFileInput = document.getElementById('audio-file');
    const transcribeAudioFileBtn = document.getElementById('transcribe-audio-file');
    const uploadProgress = document.getElementById('upload-progress');
    
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
        if (startRecordingBtn) {
            startRecordingBtn.disabled = true;
        }
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
            recordingIndicator.style.color = 'red';
            
            // Toggle buttons
            if (startRecordingBtn) startRecordingBtn.disabled = true;
            if (stopRecordingBtn) stopRecordingBtn.disabled = false;
            if (clearTranscriptBtn) clearTranscriptBtn.disabled = true;
        };
        
        recognition.onend = function() {
            isRecording = false;
            recordingStatus.textContent = 'Ready';
            recordingIndicator.textContent = '⚪';
            recordingIndicator.style.color = '';
            
            // Toggle buttons
            if (startRecordingBtn) startRecordingBtn.disabled = false;
            if (stopRecordingBtn) stopRecordingBtn.disabled = true;
            if (clearTranscriptBtn) clearTranscriptBtn.disabled = false;
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
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error', event.error);
            
            if (event.error === 'no-speech') {
                recordingStatus.textContent = 'No speech detected';
            } else {
                showError(`Speech recognition error: ${event.error}`);
            }
            
            // Stop recording on error
            if (recognition) {
                recognition.stop();
            }
        };
    }
    
    // Start recording function
    function startRecording() {
        finalTranscript = '';
        interimTranscript = '';
        updateTranscriptDisplay();
        
        if (recognition) {
            try {
                recognition.start();
            } catch (e) {
                console.error('Error starting recognition:', e);
                showError(`Could not start recording: ${e.message}`);
            }
        }
    }
    
    // Stop recording function
    function stopRecording() {
        if (recognition) {
            recognition.stop();
            
            // If we have a final transcript, enable the generate notes button
            if (finalTranscript.trim()) {
                if (generateNotesBtn) {
                    generateNotesBtn.disabled = false;
                }
            }
        }
    }
    
    // Update transcript display
    function updateTranscriptDisplay() {
        transcriptElement.innerHTML = finalTranscript + '<span style="color: #aaa">' + interimTranscript + '</span>';
        
        // Save transcript to server
        if (finalTranscript.trim()) {
            saveTranscriptToServer(finalTranscript.trim());
        }
    }
    
    // Save transcript to server
    function saveTranscriptToServer(transcript) {
        fetch('/save-transcript', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ transcript: transcript }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error saving transcript:', data.error);
            }
        })
        .catch(error => {
            console.error('Error saving transcript:', error);
        });
    }
    
    // Render markdown
    function renderMarkdown(markdownText) {
        // Use the marked library to convert markdown to HTML
        const rawHTML = marked.parse(markdownText);
        
        // Sanitize the HTML to prevent XSS
        const sanitizedHTML = DOMPurify.sanitize(rawHTML);
        
        return sanitizedHTML;
    }
    
    // Get YouTube transcript
    function getYoutubeTranscript() {
        const youtubeUrl = youtubeUrlInput.value.trim();
        
        if (!youtubeUrl) {
            showError('Please enter a YouTube URL.');
            return;
        }
        
        // Show loading state
        transcribeYoutubeBtn.disabled = true;
        transcribeYoutubeBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Processing...';
        
        // Show intermediate message in transcript area
        transcriptElement.innerHTML = '<div class="text-center my-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">Fetching transcript from YouTube...<br>This may take a moment for longer videos.</p></div>';
        
        // Call the API
        fetch('/transcribe-youtube', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ youtube_url: youtubeUrl }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
                transcriptElement.textContent = 'Error fetching transcript. Please try again.';
            } else {
                // Update the transcript
                finalTranscript = data.transcript;
                updateTranscriptDisplay();
                
                // Enable generate notes button
                if (generateNotesBtn) {
                    generateNotesBtn.disabled = false;
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError(`Error fetching YouTube transcript: ${error.message}`);
            transcriptElement.textContent = 'Error fetching transcript. Please try again.';
        })
        .finally(() => {
            // Reset button state
            transcribeYoutubeBtn.disabled = false;
            transcribeYoutubeBtn.innerHTML = '<i class="fas fa-download me-1"></i> Get YouTube Transcript';
        });
    }
    
    // Generate notes function
    function generateNotes() {
        // Make sure we have a transcript
        if (!finalTranscript.trim()) {
            showError('Please record or enter a transcript first.');
            return;
        }
        
        // Show loading indicator
        notesLoading.classList.remove('d-none');
        generateNotesBtn.disabled = true;
        
        // Call the API to generate structured notes
        fetch('/generate-notes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ transcript: finalTranscript }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                // Update the notes display with markdown rendering
                structuredNotesElement.innerHTML = renderMarkdown(data.notes);
                
                // Enable PDF download
                if (downloadPDFBtn) {
                    downloadPDFBtn.disabled = false;
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError(`Error generating notes: ${error.message}`);
        })
        .finally(() => {
            // Hide loading indicator
            notesLoading.classList.add('d-none');
            generateNotesBtn.disabled = false;
        });
    }
    
    // Clear transcript function
    function clearTranscript() {
        finalTranscript = '';
        interimTranscript = '';
        updateTranscriptDisplay();
        
        // Disable generate notes button
        if (generateNotesBtn) {
            generateNotesBtn.disabled = true;
        }
        
        // Show placeholder text
        transcriptElement.textContent = 'Your transcript will appear here...';
    }
    
    // Download PDF function
    function downloadPDF() {
        const notes = structuredNotesElement.textContent || structuredNotesElement.innerText;
        
        if (!notes) {
            showError('Please generate notes before downloading PDF.');
            return;
        }
        
        // Show loading indicator
        const downloadingAlert = document.createElement('div');
        downloadingAlert.className = "alert alert-info mb-3";
        downloadingAlert.innerHTML = '<i class="bi bi-cloud-download me-2"></i> Preparing your PDF file...';
        structuredNotesElement.parentNode.insertBefore(downloadingAlert, structuredNotesElement);
        
        // Use fetch API to get the PDF blob
        fetch('/download-pdf', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
        .then(blob => {
            // Create a URL for the blob
            const url = window.URL.createObjectURL(blob);
            
            // Create a link element
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'structured_notes.pdf';
            
            // Append to the body and trigger download
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            downloadingAlert.remove();
            
            // Show success notification
            const successAlert = document.createElement('div');
            successAlert.className = "alert alert-success mb-3";
            successAlert.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i> PDF downloaded successfully!';
            structuredNotesElement.parentNode.insertBefore(successAlert, structuredNotesElement);
            
            // Remove after 3 seconds
            setTimeout(() => {
                successAlert.remove();
            }, 3000);
        })
        .catch(error => {
            downloadingAlert.remove();
            console.error('Error downloading PDF:', error);
            showError(`Error downloading PDF: ${error.message}`);
        });
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
        
        // Save to server
        saveTranscriptToServer(finalTranscript);
        
        // Enable generate notes button
        generateNotesBtn.disabled = false;
    }
    
    // Attach event listeners if elements exist
    if (startRecordingBtn) startRecordingBtn.addEventListener('click', startRecording);
    if (stopRecordingBtn) stopRecordingBtn.addEventListener('click', stopRecording);
    if (clearTranscriptBtn) clearTranscriptBtn.addEventListener('click', clearTranscript);
    if (generateNotesBtn) generateNotesBtn.addEventListener('click', generateNotes);
    if (downloadPDFBtn) downloadPDFBtn.addEventListener('click', downloadPDF);
    if (transcribeYoutubeBtn) transcribeYoutubeBtn.addEventListener('click', getYoutubeTranscript);
    if (useManualTranscriptBtn) useManualTranscriptBtn.addEventListener('click', useManualTranscript);
    
    // File upload handler
    if (transcribeAudioFileBtn && audioFileInput) {
        transcribeAudioFileBtn.addEventListener('click', function() {
            // Check if a file is selected
            if (!audioFileInput.files.length) {
                showError('Please select an audio file first.');
                return;
            }
            
            const file = audioFileInput.files[0];
            
            // Validate file type
            const allowedTypes = ['.mp3', '.wav', '.m4a', '.ogg', '.flac'];
            const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
            if (!allowedTypes.includes(fileExtension)) {
                showError(`Invalid file type. Allowed types: ${allowedTypes.join(', ')}`);
                return;
            }
            
            // Show loading state
            transcribeAudioFileBtn.disabled = true;
            transcribeAudioFileBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Processing...';
            
            // Show progress if element exists
            if (uploadProgress) {
                uploadProgress.classList.remove('d-none');
                const progressBar = uploadProgress.querySelector('.progress-bar');
                if (progressBar) {
                    progressBar.style.width = '0%';
                }
            }
            
            // Create form data
            const formData = new FormData();
            formData.append('audio_file', file);
            
            // Send to server
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable && uploadProgress) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    const progressBar = uploadProgress.querySelector('.progress-bar');
                    if (progressBar) {
                        progressBar.style.width = percentComplete + '%';
                        progressBar.textContent = percentComplete + '%';
                    }
                }
            });
            
            xhr.addEventListener('load', function() {
                if (xhr.status === 200) {
                    // Parse the response
                    const response = JSON.parse(xhr.responseText);
                    
                    // Set the transcript
                    if (response.transcript) {
                        finalTranscript = response.transcript;
                        if (transcriptElement) {
                            transcriptElement.textContent = finalTranscript;
                        }
                        
                        // Enable generate notes button
                        if (generateNotesBtn) {
                            generateNotesBtn.disabled = false;
                        }
                        
                        // Reset form
                        audioFileInput.value = '';
                    }
                } else {
                    // Handle error
                    try {
                        const response = JSON.parse(xhr.responseText);
                        showError(`Error: ${response.error || 'Failed to transcribe audio file'}`);
                    } catch (e) {
                        showError('Error: Failed to transcribe audio file. Server returned an invalid response.');
                    }
                }
                
                // Reset UI state
                if (uploadProgress) {
                    uploadProgress.classList.add('d-none');
                }
                transcribeAudioFileBtn.disabled = false;
                transcribeAudioFileBtn.innerHTML = '<i class="fas fa-upload me-1"></i> Upload & Transcribe';
            });
            
            xhr.addEventListener('error', function() {
                showError('Error: Network error while uploading file. Please try again.');
                
                // Reset UI state
                if (uploadProgress) {
                    uploadProgress.classList.add('d-none');
                }
                transcribeAudioFileBtn.disabled = false;
                transcribeAudioFileBtn.innerHTML = '<i class="fas fa-upload me-1"></i> Upload & Transcribe';
            });
            
            // Open and send the request
            xhr.open('POST', '/transcribe-audio-file', true);
            xhr.send(formData);
        });
    }
});
