import os
import asyncio
from gtts import gTTS
import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase, WebRtcMode
from deepgram import Deepgram
from groq import Groq
from dotenv import load_dotenv
import numpy as np
import wave

# Load API keys from .env file
load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DEEPGRAM_API_KEY or not GROQ_API_KEY:
    raise ValueError("API keys for Deepgram and Groq must be set in the .env file")

# Initialize Deepgram and Groq clients
dg_client = Deepgram(DEEPGRAM_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

RESPONSE_AUDIO = "response.mp3"

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recording = np.array([], dtype=np.int16)

    def recv(self, frame):
        audio_frame = frame.to_ndarray()
        self.recording = np.concatenate((self.recording, audio_frame))
        return frame

    async def process_and_generate_response(self):
        # Save recording to a temporary WAV file
        filename = "temp_audio.wav"
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(self.recording.tobytes())

        transcript = await recognize_audio_deepgram(filename)
        response = generate_response(transcript)
        play_response(response)

        os.remove(filename)  # Clean up the audio file

async def recognize_audio_deepgram(filename):
    with open(filename, 'rb') as audio:
        source = {'buffer': audio.read(), 'mimetype': 'audio/wav'}
        response = await dg_client.transcription.prerecorded(source, {'punctuate': True, 'language': 'en-US'})
        return response['results']['channels'][0]['alternatives'][0]['transcript']

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
    os.remove(RESPONSE_AUDIO)  # Clean up the response audio file

# Streamlit UI
def run_streamlit_app():
    st.title("Voice Chatbot🔊")

    audio_processor = AudioProcessor()
    webrtc_ctx = webrtc_streamer(key="example", mode=WebRtcMode.SENDRECV, audio_processor_factory=lambda: audio_processor, media_stream_constraints={"audio": True})

    if st.button("Process and Get Response"):
        asyncio.run(audio_processor.process_and_generate_response())

if __name__ == "__main__":
    run_streamlit_app()
