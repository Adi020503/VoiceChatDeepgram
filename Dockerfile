FROM python:3.8-slim  # Choose a slim Python base image

# Install system dependencies (might differ based on OS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2  # Replace with appropriate package for your OS

# Install app dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your app code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["python", "main.py"]
