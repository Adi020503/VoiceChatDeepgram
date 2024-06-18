import os
import asyncio
import sounddevice as sd
import numpy as np
import wave
import pygame
import streamlit as st
from deepgram import Deepgram
from groq import Groq
from dotenv import load_dotenv
from gtts import gTTS

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
DURATION = 3  # seconds
SAMPLERATE = 16000
FILENAME = "output.wav"
RESPONSE_AUDIO = "response.mp3"

async def recognize_audio_deepgram(filename):
    with open(filename, 'rb') as audio:
        source = {'buffer': audio.read(), 'mimetype': 'audio/wav'}
        response = await dg_client.transcription.prerecorded(source, {'punctuate': True, 'language': 'en-US'})
        return response['results']['channels'][0]['alternatives'][0]['transcript']

def record_audio(filename, duration, samplerate):
    st.write("Recording🔉...")
    try:
        audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
        sd.wait()  # Wait until recording is finished
    except sd.PortAudioError as e:
        st.write(f"Error recording audio: {e}")
        return

    wavefile = wave.open(filename, 'wb')
    wavefile.setnchannels(1)
    wavefile.setsampwidth(2)
    wavefile.setframerate(samplerate)
    wavefile.writeframes(audio_data.tobytes())
    wavefile.close()
    st.write("Recording finished🔴.")

def generate_response(prompt):
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.29,
        max_tokens=80,
        top_p=1,
        stream=False,
        stop=None,
    )
    return response.choices[0].message.content.strip()

def play_response(text):
    tts = gTTS(text=text, lang='en')
    tts.save(RESPONSE_AUDIO)
    pygame.mixer.init()
    pygame.mixer.music.load(RESPONSE_AUDIO)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.quit()
    os.remove(RESPONSE_AUDIO)  # Clean up the response audio file

async def main():
    stop_keywords = {"thank you", "goodbye", "exit"}

    while True:
        record_audio(FILENAME, DURATION, SAMPLERATE)
        if not os.path.exists(FILENAME):
            st.write("Audio recording failed. Please try again.")
            break

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
