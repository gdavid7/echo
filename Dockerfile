# Use a more recent stable base image
FROM python:3.9-slim-bullseye

# Set environment variables to prevent Python from writing .pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install build tools needed for C extensions
RUN apt-get update && apt-get install -y build-essential python3-dev

# Argument to specify the service directory (e.g., voice_service, summary_service)
ARG SERVICE_DIR

# Upgrade pip and install python build dependencies first
COPY ${SERVICE_DIR}/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code for the specific service
COPY ${SERVICE_DIR}/ .

# Define the command to run the application
CMD ["python", "app.py"] 
