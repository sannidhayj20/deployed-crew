import os
import io
import json
import time
import requests
import streamlit as st
from streamlit_webrtc import webrtc_streamer

import numpy as np
import soundfile as sf
import google.generativeai as genai
from building_a_multi_agent_finance_assistant_with_voice_interaction.crew import BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew

# —————————————————————————
# Streamlit UI Setup
# —————————————————————————
st.set_page_config(page_title="🎹 Global Finance Assistant", page_icon="🎹", layout="wide")
st.title("🎹 Morning Market Brief Assistant")
st.markdown("Speak or type your financial query — get a spoken response.")

# —————————————————————————
# Sidebar Controls
# —————————————————————————
st.sidebar.header("🔧 Settings")
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
gemini_api_key = st.sidebar.text_input("🔮 Gemini API Key", type="password")
assemblyai_api_key = st.sidebar.text_input("🗣️ AssemblyAI API Key", type="password")
record_query = st.sidebar.checkbox("🎤 Record voice input instead of typing?")
voice_enabled = st.sidebar.checkbox("🔊 Enable voice output", value=True)

if openai_api_key:
    os.environ["OPENAI_API_KEY"] = openai_api_key

# —————————————————————————
# AssemblyAI Transcription Helpers
# —————————————————————————

def upload_audio(audio_bytes, api_key):
    headers = {
        "authorization": st.secrets("ASSEMBLY_AI_API"),
        "transfer-encoding": "chunked"
    }
    response = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=audio_bytes)
    response.raise_for_status()
    return response.json()["upload_url"]

def request_transcription(upload_url, api_key):
    json_data = {
        "audio_url": upload_url,
        "language_code": "en_us"
    }
    headers = {
        "authorization": api_key,
        "content-type": "application/json"
    }
    response = requests.post("https://api.assemblyai.com/v2/transcript", headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()["id"]

def get_transcription_result(transcript_id, api_key):
    headers = {
        "authorization": api_key,
    }
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        response = requests.get(polling_endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "completed":
            return data["text"]
        elif data["status"] == "error":
            raise RuntimeError(f"Transcription failed: {data['error']}")
        else:
            time.sleep(2)

def transcribe_audio_bytes(audio_bytes, api_key):
    upload_url = upload_audio(audio_bytes, api_key)
    transcript_id = request_transcription(upload_url, api_key)
    transcript_text = get_transcription_result(transcript_id, api_key)
    return transcript_text

# —————————————————————————
# Gemini Validator
# —————————————————————————
def is_query_valid(query: str, gemini_key: str) -> dict:
    genai.configure(api_key=gemini_key)
    model_gen = genai.GenerativeModel("gemini-1.5-flash")

    full_prompt = f"""
    You are a compliance officer and finance gatekeeper.
    Your task is to determine whether the user's query is finance-related and ethically acceptable.
    Respond ONLY with a JSON object in the following format:
    {{
    "is_finance": true,
    "is_ethical": true,
    "reason": "..."
    }}

    User Query: {query}
    """

    try:
        response = model_gen.generate_content(full_prompt)
        raw_text = response.text.strip()

        json_start = raw_text.find("{")
        json_end = raw_text.rfind("}") + 1
        json_str = raw_text[json_start:json_end]
        return json.loads(json_str)
    except Exception as e:
        return {
            "is_finance": False,
            "is_ethical": False,
            "reason": f"Error validating query: {e}"
        }

# —————————————————————————
# WebRTC callback and global audio buffer
# —————————————————————————
audio_buffer = None

def audio_frame_callback(frame):
    global audio_buffer
    # Convert audio frame to WAV bytes
    audio_bytes = frame.to_ndarray(format="wav")
    audio_buffer = audio_bytes.tobytes()
    return frame

# —————————————————————————
# Main UI and Logic
# —————————————————————————

user_query = ""

if record_query:
    st.markdown("### 🎤 Live Voice Input (Streamlit WebRTC)")
    webrtc_ctx = webrtc_streamer(
        key="audio-recorder",
        audio_receiver_size=1024,
        in_audio_track=True,
        media_stream_constraints={"audio": True, "video": False},
        audio_frame_callback=audio_frame_callback,
        async_processing=False,
    )

    if st.button("🛑 Stop and Transcribe"):
        if audio_buffer:
            if not assemblyai_api_key:
                st.error("Please enter your AssemblyAI API key in the sidebar.")
            else:
                with st.spinner("Transcribing audio with AssemblyAI..."):
                    try:
                        user_query = transcribe_audio_bytes(audio_buffer, assemblyai_api_key)
                        st.markdown(f"📝 Transcribed Query: `{user_query}`")
                    except Exception as e:
                        st.error(f"Transcription failed: {e}")
        else:
            st.warning("No audio recorded yet. Please speak into your microphone.")
else:
    user_query = st.text_area(
        "💬 Enter your financial query:",
        placeholder="e.g., What’s our risk exposure in Asia tech stocks today?",
        height=150,
    )

if st.button("🚀 Get Market Brief"):
    st.text(f"DEBUG: Received input: '{user_query}'")
    if not user_query.strip():
        st.error("🚩 No valid query detected.")
        st.markdown("Please try again. Make sure you're speaking clearly and the mic is working.")
        st.stop()

    st.info("🔍 Validating query...")
    validation_result = is_query_valid(user_query, gemini_api_key)

    if not validation_result['is_finance']:
        st.error("🛛 Not a financial query.")
        st.markdown(f"💡 Suggestion: {validation_result['reason']}")
        st.stop()

    if not validation_result['is_ethical']:
        st.error("⚠️ Potentially unethical content detected.")
        st.markdown(f"📌 Reason: {validation_result['reason']}")
        st.stop()

    st.info("🧠 Processing query with crew...")
    crew = BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew()
    result = crew.crew().kickoff(inputs={'query': user_query})

    st.markdown("### 📊 Result:")
    st.markdown(result)

    if voice_enabled:
        st.markdown("### 🎧 Audio Playback")
        try:
            from gtts import gTTS
            import io

            response_text = str(result)
            if not response_text:
                raise ValueError("Empty response text for TTS.")

            tts = gTTS(text=response_text, lang="en")
            audio_output = io.BytesIO()
            tts.write_to_fp(audio_output)
            audio_output.seek(0)

            st.audio(audio_output, format="audio/mp3")
        except Exception as e:
            st.warning("🔇 Voice synthesis failed.")
            st.text(f"Error: {e}")
