# Use an official Python runtime as a parent image
FROM python:3.10

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
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Download and install the correct PyAudio .whl file
RUN wget https://download.lfd.uci.edu/pythonlibs/p5fg5vbh/PyAudio-0.2.11-cp310-cp310-win_amd64.whl \
    && pip install PyAudio-0.2.11-cp310-cp310-win_amd64.whl \
    && rm PyAudio-0.2.11-cp310-cp310-win_amd64.whl

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run the Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8000", "--server.address=0.0.0.0"]
