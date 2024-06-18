import os
import asyncio
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

RESPONSE_AUDIO = "response.mp3"

async def recognize_audio_deepgram(audio_data):
    response = await dg_client.transcription.prerecorded(
        {'buffer': audio_data, 'mimetype': 'audio/wav'}, {'punctuate': True, 'language': 'en-US'}
    )
    return response['results']['channels'][0]['alternatives'][0]['transcript']

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
    audio_file = open(RESPONSE_AUDIO, 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3')
    os.remove(RESPONSE_AUDIO)  # Clean up the response audio file

async def main(audio_data):
    transcript = await recognize_audio_deepgram(audio_data)
    st.write(f"User: {transcript}")

    response = generate_response(transcript)
    st.write(f"Bot: {response}")
    play_response(response)

# Streamlit UI
def run_streamlit_app():
    st.title("Voice Chatbot🔊")

    st.write("Click the button below and allow access to your microphone to start recording.")

    audio_recorder_html = """
    <script>
    const recordButton = document.getElementById("recordButton");
    const stopButton = document.getElementById("stopButton");
    const audioElement = document.getElementById("audioElement");

    let mediaRecorder;
    let audioChunks = [];

    recordButton.addEventListener("click", async () => {
        audioChunks = [];
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();

        mediaRecorder.addEventListener("dataavailable", event => {
            audioChunks.push(event.data);
        });

        mediaRecorder.addEventListener("stop", async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const arrayBuffer = await audioBlob.arrayBuffer();
            const uint8Array = new Uint8Array(arrayBuffer);

            const response = await fetch("/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    audio_data: Array.from(uint8Array)
                })
            });

            const result = await response.json();
            const audioResponseBlob = new Blob([new Uint8Array(result.audio)], { type: 'audio/mp3' });
            const audioUrl = URL.createObjectURL(audioResponseBlob);
            audioElement.src = audioUrl;
            audioElement.play();
        });

        recordButton.style.display = "none";
        stopButton.style.display = "block";
    });

    stopButton.addEventListener("click", () => {
        mediaRecorder.stop();
        stopButton.style.display = "none";
        recordButton.style.display = "block";
    });
    </script>
    <button id="recordButton">Start Recording</button>
    <button id="stopButton" style="display:none;">Stop Recording</button>
    <audio id="audioElement" controls></audio>
    """

    st.markdown(audio_recorder_html, unsafe_allow_html=True)

if __name__ == "__main__":
    run_streamlit_app()
