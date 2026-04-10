# Use a slim Python image for efficiency on your local machine
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install necessary libraries for the "Cage"
# We add 'requests' here so the agent can fetch live data
RUN pip install --no-cache-dir requests

# Copy the current directory contents into the container
COPY . /app

# Ensure the container stays open or runs the script passed by the dispatcher
CMD ["python"]