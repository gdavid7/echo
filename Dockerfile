# Use an official Python runtime as a parent image
FROM python:3.9-slim

# This build argument is provided by docker-compose.yml
ARG SERVICE_DIR

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file for the specific service and install dependencies
COPY ${SERVICE_DIR}/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code for the specific service
# This makes the image self-contained and runnable without volumes
COPY ${SERVICE_DIR}/ /app/

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application with access logging enabled
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "app:app"] 
