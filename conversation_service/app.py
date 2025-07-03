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
    # This will catch errors during initialization
    print(f"Error initializing OpenAI client: {e}")
    client = None

@app.route('/conversation', methods=['POST'])
def handle_conversation():
    """
    Takes a conversation history and uses an LLM to generate the next assistant question.
    """
    data = request.get_json()
    conversation_log = data.get('conversation_log', [])

    if not conversation_log:
        return jsonify({"error": "No conversation log provided"}), 400

    if not client:
        return jsonify({"error": "OpenAI client not initialized."}), 500

    print("Conversation service received request, calling OpenAI...")

    try:
        # We add a new system message to guide the model's response for THIS turn.
        messages_for_api = conversation_log + [
            {"role": "system", "content": "Ask the next single, clarifying question. If you have enough information to form a diagnosis, end the conversation by saying 'END_CONVERSATION'."}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_api,
            max_tokens=100,
            temperature=0.7,
        )
        
        assistant_reply = response.choices[0].message.content

        end_of_conversation = "END_CONVERSATION" in assistant_reply
        if end_of_conversation:
            # Clean up the marker from the final message
            assistant_reply = assistant_reply.replace("END_CONVERSATION", "").strip()
            print("AI decided to end the conversation.")
        
        print(f"AI response: {assistant_reply}")

        return jsonify({
            "reply": assistant_reply,
            "end_of_conversation": end_of_conversation
        })
        
    except openai.APIError as e:
        print(f"OpenAI API error: {e}")
        return jsonify({"error": "There was an issue with the AI service."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
