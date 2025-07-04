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
        transcript = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_log if 'role' in msg and 'content' in msg])
        
        summary_prompt = (
            "You are a clinical assistant AI. Your task is to create a highly detailed and structured clinical summary of a phone conversation transcript. The patient called ahead of an appointment to provide details on their condition. Your summary must be comprehensive, especially if pain or significant symptoms are mentioned.\n\n"
            "Based on the transcript, extract and format the key information under the following Markdown headings. Be thorough and capture all relevant details.\n\n"
            "**Patient Status:**\n"
            "- [Note whether the patient is new or existing.]\n\n"
            "**Chief Complaint:**\n"
            "- [State the primary reason for the patient's upcoming visit in one sentence.]\n\n"
            "**Detailed Symptom Analysis:**\n"
            "- **Onset & Duration:** [When did the symptoms start and how long have they been present?]\n"
            "- **Nature of Pain/Sensation:** [Provide a detailed description of the sensation. Use the patient's own words where possible (e.g., 'sharp', 'throbbing', 'dull ache', 'sensitive to air').]\n"
            "- **Location:** [Specify the exact location of the issue as described by the patient.]\n"
            "- **Triggers & Relievers:** [What actions or conditions make the symptoms worse or better?]\n"
            "- **Severity:** [Include the patient's self-reported severity rating and any other descriptions of its impact.]\n"
            "- **History of Issue:** [Did the patient mention if this has happened before?]\n\n"
            "**Potential Clinical Considerations:**\n"
            "- [Based on the reported symptoms, list potential dental issues to investigate. Examples: 'Dental Caries (Cavity)', 'Pulpitis', 'Cracked Tooth Syndrome', 'Gingivitis', 'Periapical Abscess'. Frame these as possibilities.]\n\n"
            "**Urgency Assessment (1-5):** [Provide a numerical score for clinical urgency (1=Routine, 5=Emergency) and a brief justification.]\n\n"
            "**Clinical Narrative:**\n"
            "- [If the patient reported significant pain, trauma, or swelling, provide a detailed narrative summary of the situation here. Synthesize the information from the other sections into a cohesive paragraph. Otherwise, state 'No significant issues reported requiring a detailed narrative.']\n\n"
            "Fill out each category as completely as possible. If the patient did not provide information for a specific category, explicitly state 'Not mentioned by patient'."
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": transcript}
            ],
            max_tokens=800,
            temperature=0.5,
        )

        summary_text = response.choices[0].message.content
        print("--- Generated Clinical Summary ---")
        print(summary_text)
        print("------------------------------------")

        return jsonify({"summary_text": summary_text})

    except openai.APIError as e:
        print(f"OpenAI API error: {e}")
        return jsonify({"error": "There was an issue with the AI summary service."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
