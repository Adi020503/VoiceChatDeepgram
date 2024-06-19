# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    cmake \
    rsync \
    libgl1-mesa-glx \
    wget \
    libasound2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
