import sounddevice as sd
import numpy as np
import wave
import streamlit as st
from deepgram import Deepgram
from groq import Groq
from dotenv import load_dotenv
from gtts import gTTS
import asyncio
import os

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
DURATION = 5 # seconds
SAMPLERATE = 16000
FILENAME = "output.wav"
RESPONSE_AUDIO = "response.mp3"

async def recognize_audio_deepgram(filename):
    with open(filename, 'rb') as audio:
        source = {'buffer': audio.read(), 'mimetype': 'audio/wav'}
        response = await dg_client.transcription.prerecorded(source, {'punctuate': True, 'language': 'en-US'})
        return response['results']['channels'][0]['alternatives'][0]['transcript']

def record_audio(filename, duration, samplerate):
    try:
        st.write("Recording🔉...")
        device_info = sd.query_devices(kind='input')
        default_samplerate = int(device_info['default_samplerate'])

        audio_data = sd.rec(int(duration * default_samplerate), samplerate=default_samplerate, channels=1, dtype=np.int16)
        sd.wait()  # Wait until recording is finished
        wavefile = wave.open(filename, 'wb')
        wavefile.setnchannels(1)
        wavefile.setsampwidth(2)
        wavefile.setframerate(default_samplerate)
        wavefile.writeframes(audio_data.tobytes())
        wavefile.close()
        st.write("Recording finished🔴.")
    except Exception as e:
        st.write(f"Error recording audio: {e}")

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
    tts = gTTS(text=text, lang='en')
    tts.save(RESPONSE_AUDIO)
    audio_file = open(RESPONSE_AUDIO, 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3')

async def main():
    stop_keywords = {"thank you", "goodbye", "exit"}

    while True:
        record_audio(FILENAME, DURATION, SAMPLERATE)
        user_input = await recognize_audio_deepgram(FILENAME)
        st.write(f"User: {user_input}")

        if any(keyword in user_input.lower() for keyword in stop_keywords):
            st.write("Conversation ended.")
            play_response("Goodbye! Have a great day!")
            break

        response = generate_response(user_input)
        st.write(f"Bot: {response}")
        play_response(response)
        os.remove(FILENAME)  # Clean up the audio file

# Streamlit UI
def run_streamlit_app():
    st.title("Voice Chatbot🔊")

    if st.button("Start Conversation"):
        asyncio.run(main())

if __name__ == "__main__":
    run_streamlit_app()
