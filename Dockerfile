# Use a more recent stable base image
FROM python:3.9-slim-bullseye

# Set environment variables to prevent Python from writing .pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install build dependencies required for packages like gevent
RUN apt-get update && apt-get install -y build-essential python3-dev

# Set the working directory in the container
WORKDIR /app

# Argument to specify the service directory (e.g., voice_service, summary_service)
ARG SERVICE_DIR

# Upgrade pip and install python build dependencies first
COPY ${SERVICE_DIR}/requirements.txt .
RUN pip install --upgrade pip
# Pin Cython to a version before 3.0 to avoid compilation errors with gevent
RUN pip install wheel "cython<3.0"

# Now install the application dependencies
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

# Copy the application code for the specific service
COPY ${SERVICE_DIR}/ .

# Define the command to run the application with access logging enabled
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"] 
