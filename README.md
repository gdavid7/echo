# Echo - AI Voice Agent

This project is a voice-based AI assistant that communicates over a phone call. Users can call a Twilio phone number, have a conversation with an AI, and then receive a text message with a summary of the conversation.

The application is built with Python and Flask, containerized with Docker, and designed to be deployed in a cloud environment.

## Features

- **Real-time Voice Conversation**: Engage in a spoken conversation with an AI over a standard phone call.
- **Twilio Integration**: Uses Twilio for managing the phone call and streaming audio.
- **AI-Powered Conversation**: Employs OpenAI's models for transcription, conversational intelligence, and text-to-speech.
- **Automated Summarization**: The `summary_service` generates a concise summary of the conversation, which is sent via SMS.

## System Architecture

The application is composed of two main services:

1.  **Voice Service**: A Flask application that handles the Twilio Voice webhook. It establishes a WebSocket connection to receive and send real-time audio streams, orchestrates the interaction with OpenAI's services (transcription, chat, TTS), and manages the call flow.
2.  **Summary Service**: A simple service that accepts the conversation transcript and uses OpenAI to generate a summary.

## Setup and Usage

### Prerequisites

*   Docker and Docker Compose
*   A valid OpenAI API Key
*   A Twilio account with a phone number
    *   Twilio Account SID
    *   Twilio Auth Token
*   `ngrok` to expose your local server to the internet for Twilio webhooks.

### Running the Application

1.  **Set up Environment Variables**:
    Create a `.env` file in the project root. You will need to add your credentials from OpenAI and Twilio.

    ```
    OPENAI_API_KEY=sk-YourActualKeyHere...

    # Your Twilio Account SID and Auth Token
    TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    TWILIO_AUTH_TOKEN=your_auth_token_here

    # The Twilio phone number you purchased
    TWILIO_NUMBER=+15551234567

    # Your personal phone number to receive the summary SMS
    USER_NUMBER=+15557654321

    # This will be your ngrok forwarding URL
    SERVER_URL=
    ```

2.  **Start `ngrok`**:
    In a separate terminal, start `ngrok` to forward traffic to the `voice_service` port (8080).

    ```bash
    ngrok http 8080
    ```

3.  **Update `.env` with ngrok URL**:
    Copy the HTTPS forwarding URL from the `ngrok` output (it will look like `https://<random-string>.ngrok-free.app`) and paste it into the `SERVER_URL` variable in your `.env` file.

    ```
    SERVER_URL=https://<random-string>.ngrok-free.app
    ```

4.  **Configure Twilio Webhook**:
    Go to your Twilio phone number's configuration page in the Twilio console. Under "Voice & Fax", set the "A CALL COMES IN" webhook to your ngrok forwarding URL, appending the `/call` endpoint. For example: `https://<random-string>.ngrok-free.app/call`

5.  **Build and Run with Docker**:
    Open a terminal in the project root and run:

    ```bash
    docker compose up --build
    ```

6.  **Make a Call**:
    Call your Twilio phone number. The application will answer, and you can begin speaking with the AI assistant. After you hang up, you will receive an SMS with the conversation summary.
