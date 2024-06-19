import io
import os
import asyncio
import sounddevice as sd
import numpy as np
import wave
import streamlit as st
from deepgram import Deepgram
from groq import Groq
from dotenv import load_dotenv
import pyttsx3

# Load API keys from .env file
load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DEEPGRAM_API_KEY or not GROQ_API_KEY:
    raise ValueError("API keys for Deepgram and Groq must be set in the .env file")

# Initialize Deepgram and Groq clients
dg_client = Deepgram(DEEPGRAM_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# Audio recording parameters
DURATION = 5  # seconds
SAMPLERATE = 16000

async def recognize_audio_deepgram(audio_data):
    with io.BytesIO() as wav_file:
        wav_writer = wave.open(wav_file, 'wb')
        wav_writer.setnchannels(1)
        wav_writer.setsampwidth(2)
        wav_writer.setframerate(SAMPLERATE)
        wav_writer.writeframes(audio_data.tobytes())
        wav_writer.close()
        wav_file.seek(0)
        source = {'buffer': wav_file.read(), 'mimetype': 'audio/wav'}
        response = await dg_client.transcription.prerecorded(source, {'punctuate': True, 'language': 'en-US'})
        return response['results']['channels'][0]['alternatives'][0]['transcript']

def record_audio(duration, samplerate):
    st.write("Recording🔉...")
    
    # Find the default input device and use its index for recording
    default_input_device = sd.default.device[0]
    
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16, device=default_input_device)
    
    sd.wait()  # Wait until recording is finished
    st.write("Recording finished🔴.")
    
    return audio_data

def generate_response(prompt):
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.29,
        max_tokens=100,
        top_p=1,
        stream=False,
        stop=None,
    )
    return response.choices[0].message.content.strip()

def play_response(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

async def main():
    stop_keywords = {"thank you", "goodbye", "exit"}

    while True:
        audio_data = record_audio(DURATION, SAMPLERATE)
        user_input = await recognize_audio_deepgram(audio_data)
        st.write(f"User: {user_input}")

        if any(keyword in user_input.lower() for keyword in stop_keywords):
            st.write("Conversation ended.")
            play_response("Goodbye! Have a great day!")
            break

        response = generate_response(user_input)
        st.write(f"Bot: {response}")
        play_response(response)

# Streamlit UI
def run_streamlit_app():
    st.title("Voice Chatbot🔊")

    if st.button("Start Conversation"):
        asyncio.run(main())

if __name__ == "__main__":
    run_streamlit_app()
