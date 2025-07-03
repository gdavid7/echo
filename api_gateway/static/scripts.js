document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const recordButton = document.getElementById('record-button');
    const summaryButton = document.getElementById('summary-button');
    const statusMessage = document.getElementById('status-message');
    const loader = document.getElementById('loader');

    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    function appendMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);
        const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
        messageElement.innerHTML = formattedText;
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    async function toggleRecording() {
        if (isRecording) {
            mediaRecorder.stop();
            isRecording = false;
        } else {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                isRecording = true;
                audioChunks = [];
                recordButton.classList.add('recording');
                statusMessage.textContent = 'Recording... Click to stop.';

                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener('stop', sendAudio);
            } catch (err) {
                console.error('Error accessing microphone:', err);
                statusMessage.textContent = 'Could not access microphone.';
            }
        }
    }

    async function sendAudio() {
        recordButton.classList.remove('recording');
        statusMessage.textContent = 'Processing...';
        loader.style.display = 'block';

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('audio_data', audioBlob, 'recording.webm');

        try {
            const response = await fetch('/voice-chat', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);

            // Update transcript
            const userTranscript = response.headers.get('X-User-Transcript');
            const aiTranscript = response.headers.get('X-AI-Transcript');
            appendMessage(userTranscript, 'user');
            appendMessage(aiTranscript, 'assistant');

            // Play audio response
            const audioResponseBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioResponseBlob);
            const audio = new Audio(audioUrl);
            audio.play();

            if (response.headers.get('X-Conversation-Over') === 'True') {
                summaryButton.style.display = 'block';
                recordButton.style.display = 'none';
                statusMessage.textContent = 'Conversation complete.';
            } else {
                 statusMessage.textContent = 'Click the button to reply.';
            }

        } catch (error) {
            console.error('Error sending audio:', error);
            statusMessage.textContent = 'Error processing audio. Please try again.';
            appendMessage('Sorry, something went wrong. Please try again.', 'assistant');
        } finally {
            loader.style.display = 'none';
        }
    }
    
    async function getSummary() {
        loader.style.display = 'block';
        summaryButton.style.display = 'none';
        try {
            const response = await fetch('/get-summary', { method: 'POST' });
            if (!response.ok) throw new Error('Failed to get summary.');
            const data = await response.json();
            appendMessage(data.summary_text, 'summary');
        } catch (error) {
            console.error('Error:', error);
            appendMessage('Could not generate the summary.', 'assistant');
        } finally {
            loader.style.display = 'none';
            statusMessage.textContent = 'Report generated.';
        }
    }

    recordButton.addEventListener('click', toggleRecording);
    summaryButton.addEventListener('click', getSummary);
    
    // Initial message
    appendMessage("Hello! I'm a dental assistant AI. What seems to be the problem today?", 'assistant');
}); 
