from flask import Flask, request, jsonify, send_file
import os
import openai
import httpx
from io import BytesIO

app = Flask(__name__)

# Initialize the OpenAI client with a custom httpx client to avoid proxy issues
try:
    http_client = httpx.Client(proxies={})
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        http_client=http_client
    )
except Exception as e:
    print(f"Error initializing OpenAI client in TTS service: {e}")
    client = None

@app.route('/generate-speech', methods=['POST'])
def generate_speech():
    """Receives text and returns speech audio from OpenAI."""
    if not client:
        return jsonify({"error": "OpenAI client not initialized in TTS service."}), 500

    data = request.get_json()
    text_to_speak = data.get('text')
    if not text_to_speak:
        return jsonify({"error": "No text provided"}), 400

    try:
        print(f"TTS service received request for text: '{text_to_speak[:30]}...'")
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy", # A friendly, neutral voice
            input=text_to_speak
        )

        # Use an in-memory buffer to stream the audio back without saving to disk
        audio_buffer = BytesIO(response.content)
        audio_buffer.seek(0)

        print("TTS generation complete, sending audio data.")
        return send_file(
            audio_buffer,
            mimetype="audio/mpeg",
            as_attachment=False
        )

    except Exception as e:
        print(f"An unexpected error occurred in TTS service: {e}")
        return jsonify({"error": "An unexpected error occurred during speech generation."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True) 
