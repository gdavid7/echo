# Voice-First Dental Intake Assistant Prototype

This project is a Python-based prototype of a voice-first dental intake assistant, architected as a set of communicating microservices. It demonstrates a complete, end-to-end flow from voice input (simulated via file upload) to a final PDF summary for a dentist, using a stateless and containerized approach.

The application simulates a "dental nurse" assistant that engages in a dynamic conversation to gather patient information and then generates a one-time-use clinical report.

## Architecture

This project is composed of four distinct microservices that communicate over HTTP:

-   **API Gateway (`api_gateway`)**: The single entry point for all client requests. It handles file uploads, orchestrates the workflow by calling the other services in sequence, and serves the final PDF report to the user.
-   **Transcription Service (`transcription_service`)**: Responsible for handling the speech-to-text conversion of the audio input.
-   **Conversation Service (`conversation_service`)**: Manages the dynamic, branching conversation with a simulated LLM to gather patient details.
- **Summary Service (`summary_service`)**: Takes the final conversation log, generates a structured text summary, and renders it into a PDF report using WeasyPrint.

This microservice architecture ensures a clean separation of concerns, allows for independent scaling of services, and promotes resilience.

## Tech Stack

-   **Backend**: Python, Flask, Gunicorn
-   **Service Communication**: HTTP (via Requests)
-   **PDF Generation**: WeasyPrint
-   **Containerization**: Docker, Docker Compose
-   **Frontend**: HTML, CSS

## Project Structure

```
.
├── api_gateway/
│   ├── app.py
│   ├── static/
│   └── templates/
├── conversation_service/
│   └── app.py
├── summary_service/
│   └── app.py
├── transcription_service/
│   └── app.py
├── reports/                # Shared volume for generated PDFs (auto-managed)
├── Dockerfile              # Universal Dockerfile for all services
├── docker-compose.yml      # Defines and orchestrates the services
├── requirements.txt        # Python dependencies for all services
└── README.md
```

## Setup and Installation

### Prerequisites

-   **Docker**: You must have Docker and Docker Compose installed on your system.
    -   [Install Docker Engine](https://docs.docker.com/engine/install/)
    -   [Install Docker Compose](https://docs.docker.com/compose/install/)

### Running the Application

1.  **Clone the repository (or ensure all files are in the same directory):**
    ```bash
    # git clone <repository-url>
    # cd <repository-directory>
    ```

2.  **Build and run the services using Docker Compose:**
    From the root of the project directory, run the following command:
    ```bash
    docker-compose up --build
    ```
    This command will build the Docker image for the services and start them. You will see logs from all four services in your terminal.

3.  **Access the web interface:**
    Open your web browser and navigate to `http://127.0.0.1:5000`.

## How to Use

1.  You will see a simple page with a file upload form.
2.  Click the "Upload Audio File" area and select any audio file from your computer. (Since the transcription is mocked, the content of the file does not matter).
3.  Click the "Generate Report" button.
4.  A loading spinner will appear while the API Gateway orchestrates the calls to the backend services.
5.  After a few seconds, your browser will automatically download the generated PDF report.
6.  Check the terminal where Docker Compose is running to see log messages from each service, including the final cleanup of temporary files.

## Stopping the Application

To stop all running services, press `Ctrl+C` in the terminal where `docker-compose` is running. To remove the containers, you can run:
```bash
docker-compose down
```
