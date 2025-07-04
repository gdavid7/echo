# Product Document: Echo - AI Dental Intake Assistant

## 1. Vision & Overview

Echo is an AI-powered, phone-based dental intake assistant designed to streamline the pre-appointment process for dental offices. It provides a convenient and efficient way for patients to provide detailed information about their symptoms and concerns before their visit, ensuring the clinical team is fully prepared.

The system is built on a robust microservice architecture using Python, Twilio for telephony, and OpenAI's cutting-edge models for real-time conversation, transcription, and clinical analysis.

## 2. Core Features

-   **Toll-Free Phone Number:** Patients call a dedicated number to interact with the AI assistant.
-   **AI-Powered Conversational Agent:** A natural-language, voice-based assistant (named Echo) guides patients through a diagnostic conversation. The conversation is dynamically adapted based on the patient's reported symptoms.
-   **Automated Clinical Summary:** After the call, the system automatically generates a detailed, structured clinical summary formatted for a dentist's review.
-   **Clinical Intelligence:** The summary includes not just transcribed symptoms, but also AI-generated insights such as potential dental conditions to investigate and a clinical urgency score.

## 3. System Architecture

The application has been refined into a highly efficient two-service architecture, orchestrated by Docker Compose.

```
+----------------+      +------------------+      +-------------------+
|                |      |                  |      |                   |
| Twilio         |----->|  voice_service   |----->|   OpenAI Realtime |
| (Phone Number) |      | (Python/aiohttp) |      |   (Conversation)  |
|                |      |                  |      |                   |
+----------------+      +------------------+      +-------------------+
                             |
                             | (on call end)
                             |
                             v
                     +------------------+      +-------------------+
                     |                  |      |                   |
                     |  summary_service |----->|     OpenAI gpt-4o   |
                     |  (Python/Flask)  |      |     (Summary)     |
                     |                  |      |                   |
                     +------------------+      +-------------------+
```

-   **`voice_service`**
    -   **Description:** The primary service that handles all real-time call logic. It serves as the webhook endpoint for Twilio, manages the bidirectional media stream, and orchestrates the real-time conversation with the OpenAI Realtime API. At the end of a call, it triggers the `summary_service`.
    -   **Technology:** Python, aiohttp, websockets, Twilio Python SDK.
-   **`summary_service`**
    -   **Description:** A worker service that receives the full conversation log from the `voice_service`. It uses a specially crafted prompt with the `gpt-4o` model to generate a structured, clinically relevant summary.
    -   **Technology:** Python, Flask, OpenAI Python SDK.

## 4. User & System Flow

1.  **Patient Calls:** The patient dials the Twilio phone number associated with the dental practice.
2.  **AI Greeting:** The `voice_service` answers the call and plays a brief greeting message.
3.  **Connect to AI:** The call is connected to the OpenAI Realtime API via a WebSocket media stream.
4.  **Diagnostic Conversation:** The AI assistant, "Echo," engages the patient in a conversation, asking for their name, the reason for their visit, and detailed follow-up questions about their symptoms, history, and discomfort.
5.  **Call Ends:** The patient hangs up.
6.  **Summary Trigger:** The `voice_service` sends the complete, structured conversation log to the `summary_service`.
7.  **Summary Generation:** The `summary_service` sends the log to the `gpt-4o` API with a detailed prompt, requesting a clinical summary.
8.  **Summary Logged:** The final, structured summary is printed to the `summary_service` logs for review.

## 5. Potential Future Enhancements

-   **PDF Report Generation:** The `summary_service` could format the summary into a professional, branded PDF.
-   **Automated Delivery:** The generated PDF summary could be automatically emailed to the office manager or sent via a secure link to the dentist's phone.
-   **Patient Record Integration:** The summary could be automatically pushed into the dental office's Patient Management System (e.g., Dentrix, Eaglesoft) via an API integration.
-   **Caller ID Lookup:** The system could use the incoming phone number to identify the patient and greet them by name for a more personalized experience.
