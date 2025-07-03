from flask import Flask, request, jsonify
import os
import openai
import httpx

app = Flask(__name__)

# Explicitly initialize the OpenAI client with a custom httpx client
try:
    # Create a custom httpx client, explicitly disabling proxies
    http_client = httpx.Client(proxies={})
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        http_client=http_client
    )
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

@app.route('/summarize', methods=['POST'])
def handle_summary():
    """
    Creates a clinical summary from a conversation log using an LLM.
    """
    data = request.get_json()
    conversation_log = data.get('conversation_log')

    if not conversation_log:
        return jsonify({"error": "No conversation log provided"}), 400

    if not client:
        return jsonify({"error": "OpenAI client not initialized."}), 500

    print("Summary service received request, calling OpenAI for summary...")

    try:
        # Convert the conversation log to a simple string format for the prompt
        transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_log if msg['role'] != 'system'])
        
        summary_prompt = (
            "You are a helpful assistant for a dentist. Based on the following conversation "
            "transcript, create a concise clinical summary for the dentist. The summary should include: "
            "Patient-Reported Symptoms, Symptom Timeline, Relevant Medical/Dental History, "
            "and a list of Potential Conditions. Format the output clearly using Markdown-style headings "
            "(e.g., `**Patient-Reported Symptoms:**`)."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": transcript}
            ],
            max_tokens=600,
            temperature=0.5,
        )

        summary_text = response.choices[0].message.content
        print("OpenAI summary generation complete.")

        return jsonify({"summary_text": summary_text})

    except openai.APIError as e:
        print(f"OpenAI API error: {e}")
        return jsonify({"error": "There was an issue with the AI summary service."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
