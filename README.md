# AI Dental Intake Assistant

This project is a prototype of a voice-first dental intake assistant. It provides a web-based interface where a patient can have a spoken conversation with an AI assistant to describe their symptoms and medical history.

The application is built with a Python and Flask backend, organized into a microservice architecture, and fully containerized with Docker.

## Features

- **Voice-First Interface**: A real-time, voice-driven interface for patient intake.
- **Speech-to-Text**: Utilizes OpenAI's Whisper model for real-time transcription.
- **AI-Powered Conversation**: Employs OpenAI's GPT-4o for dynamic, natural conversation flow.
- **Text-to-Speech**: Uses OpenAI's TTS model to give the assistant a voice.
- **Automated Summary**: Generates a clinical summary of the conversation for the dentist.
- **Microservice Architecture**: Built with five distinct services for scalability and maintainability.

## System Architecture

The application is composed of five microservices:
1.  **API Gateway**: The main entry point that serves the frontend and orchestrates backend requests.
2.  **Transcription Service**: Converts the user's speech to text.
3.  **Conversation Service**: Generates the AI's conversational responses.
4.  **Text-to-Speech (TTS) Service**: Converts the AI's text responses into speech.
5.  **Summary Service**: Creates a clinical summary at the end of the conversation.

For a more detailed breakdown, please see `PRODUCT_DOCUMENT.md`.

## Setup and Usage

### Prerequisites

*   Docker and Docker Compose
*   A valid OpenAI API key
*   A working microphone
*   A modern web browser (e.g., Chrome, Firefox)

### Running the Application

1.  **Create `.env` file**: In the root of the project, create a file named `.env`.
2.  **Set API Key**: Add your OpenAI API key to the `.env` file like this:
    ```
    OPENAI_API_KEY=sk-YourActualKeyHere...
    ```
3.  **Build and Run**: Open a terminal and run the following command:
    ```bash
    docker compose up --build
    ```
4.  **Access the Assistant**: Open your browser and go to `http://localhost:5000`. Grant microphone permissions when prompted. Click the microphone button to start and stop recording your voice.
