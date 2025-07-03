import os
import requests
from flask import Flask, request, render_template, session, jsonify, make_response
from secrets import token_hex

app = Flask(__name__)
# A secret key is required for Flask session management
app.secret_key = token_hex(16)

# Get service URLs from environment variables
CONVERSATION_SERVICE_URL = os.environ.get("CONVERSATION_SERVICE_URL")
SUMMARY_SERVICE_URL = os.environ.get("SUMMARY_SERVICE_URL")
TRANSCRIPTION_SERVICE_URL = os.environ.get("TRANSCRIPTION_SERVICE_URL")
TTS_SERVICE_URL = os.environ.get("TTS_SERVICE_URL")

@app.route('/')
def index():
    # Initialize a new chat session
    session['conversation_log'] = [{"role": "system", "content": "You are a friendly and professional dental intake assistant. Start the conversation by asking the patient what brought them in today."}]
    session['conversation_over'] = False
    # Start with a welcome message from the assistant
    session['conversation_log'].append({"role": "assistant", "content": "Hello! I'm a dental assistant AI. What seems to be the problem today?"})
    return render_template('index.html')

@app.route('/voice-chat', methods=['POST'])
def voice_chat():
    """Orchestrates the voice-to-voice conversation flow."""
    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio data found in request"}), 400

    audio_file = request.files['audio_data']

    try:
        # 1. Transcribe the user's audio to text
        print("Forwarding audio to transcription service...")
        files = {'audio_data': (audio_file.filename, audio_file.read(), audio_file.mimetype)}
        transcribe_resp = requests.post(f"{TRANSCRIPTION_SERVICE_URL}/transcribe", files=files)
        transcribe_resp.raise_for_status()
        user_text = transcribe_resp.json().get('transcript')

        if not session.get('conversation_log'):
             # Handle expired session if necessary
            session['conversation_log'] = [{"role": "system", "content": "You are a friendly and professional dental intake assistant."}]
        session['conversation_log'].append({"role": "user", "content": user_text})
        session.modified = True
        print(f"Transcription successful: '{user_text}'")

        # 2. Get the AI's text-based reply
        print("Forwarding transcript to conversation service...")
        convo_resp = requests.post(f"{CONVERSATION_SERVICE_URL}/conversation", json={"conversation_log": session['conversation_log']})
        convo_resp.raise_for_status()
        convo_data = convo_resp.json()
        ai_text_reply = convo_data['reply']
        session['conversation_log'].append({"role": "assistant", "content": ai_text_reply})
        session['conversation_over'] = convo_data.get('end_of_conversation', False)
        session.modified = True
        print(f"AI text reply: '{ai_text_reply}'")

        # 3. Convert the AI's text reply to speech
        print("Forwarding AI text to TTS service...")
        tts_resp = requests.post(f"{TTS_SERVICE_URL}/generate-speech", json={"text": ai_text_reply})
        tts_resp.raise_for_status()

        # 4. Stream the audio back to the client
        # We also send back the transcripts in headers for the frontend to display
        response = make_response(tts_resp.content)
        response.headers['Content-Type'] = 'audio/mpeg'
        response.headers['X-User-Transcript'] = user_text.encode('utf-8')
        response.headers['X-AI-Transcript'] = ai_text_reply.encode('utf-8')
        response.headers['X-Conversation-Over'] = str(session['conversation_over'])
        
        return response

    except requests.exceptions.RequestException as e:
        print(f"A service call failed: {e}")
        return jsonify({"error": "A backend service is unavailable."}), 503
    except Exception as e:
        print(f"An unexpected error occurred in voice chat: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

@app.route('/get-summary', methods=['POST'])
def get_summary():
    """
    Requests a summary from the summary service and returns the text.
    """
    if 'conversation_log' not in session:
        return jsonify({"error": "No conversation to summarize"}), 400

    try:
        response = requests.post(
            f"{SUMMARY_SERVICE_URL}/summarize",
            json={"conversation_log": session.get('conversation_log')}
        )
        response.raise_for_status()
        data = response.json()
        return jsonify({"summary_text": data.get("summary_text")})
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Could not connect to summary service: {e}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        error_msg = f"An unexpected error occurred in the api_gateway: {e}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
