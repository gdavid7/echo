from flask import Flask, request, jsonify
import os
import openai
import httpx
import uuid

app = Flask(__name__)

# Initialize the OpenAI client with a custom httpx client
try:
    http_client = httpx.Client(proxies={})
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        http_client=http_client
    )
except Exception as e:
    print(f"Error initializing OpenAI client in transcription service: {e}")
    client = None

# Create a temporary folder for audio uploads
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Receives an audio file, transcribes it, and returns the text."""
    if not client:
        return jsonify({"error": "OpenAI client not initialized in transcription service."}), 500

    if 'audio_data' not in request.files:
        return jsonify({"error": "No audio file part in the request"}), 400

    audio_file = request.files['audio_data']

    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    temp_filepath = ""
    try:
        # The browser's MediaRecorder typically sends webm or ogg
        temp_filename = f"{uuid.uuid4()}-{audio_file.filename}"
        temp_filepath = os.path.join(UPLOAD_FOLDER, temp_filename)
        audio_file.save(temp_filepath)
        print(f"Audio file saved to {temp_filepath}")

        # Transcribe using OpenAI Whisper API
        with open(temp_filepath, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )

        print(f"Transcription successful: '{transcript.text}'")
        return jsonify({"transcript": transcript.text})

    except Exception as e:
        print(f"An error occurred during transcription: {e}")
        return jsonify({"error": "An error occurred during transcription"}), 500

    finally:
        # Ensure the temporary file is always cleaned up
        if temp_filepath and os.path.exists(temp_filepath):
            os.remove(temp_filepath)
            print(f"Cleaned up temporary file: {temp_filepath}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
