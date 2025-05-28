import os
import io
import json
import time
import requests
import streamlit as st
import numpy as np
import av
from pydub import AudioSegment
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import google.generativeai as genai
from crew import BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew

# -----------------------------
# Page Setup
# -----------------------------
st.set_page_config(page_title="🎹 Global Finance Assistant", page_icon="🎹", layout="wide")
st.title("🎹 Morning Market Brief Assistant")
st.markdown("Speak or type your financial query — get a spoken response.")

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("🔧 Settings")
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
gemini_api_key = st.sidebar.text_input("🔮 Gemini API Key", type="password")
assemblyai_api_key = st.sidebar.text_input("🔣 AssemblyAI API Key", type="password")
record_query = st.sidebar.checkbox("🎤 Record voice input instead of typing?")
voice_enabled = st.sidebar.checkbox("🔊 Enable voice output", value=True)

if openai_api_key:
    os.environ["OPENAI_API_KEY"] = openai_api_key

# -----------------------------
# Audio Processing Class
# -----------------------------
class AudioProcessor:
    def __init__(self):
        self.audio = AudioSegment.empty()

    def recv(self, frame: av.AudioFrame):
        pcm = frame.to_ndarray()
        audio_segment = AudioSegment(
            pcm.tobytes(),
            frame_rate=frame.sample_rate,
            sample_width=2,
            channels=len(pcm.shape),
        )
        self.audio += audio_segment
        return frame

processor = AudioProcessor()

# -----------------------------
# AssemblyAI Helpers
# -----------------------------
def upload_audio(audio_bytes, api_key):
    headers = {
        "authorization": api_key,
        "transfer-encoding": "chunked"
    }
    response = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=audio_bytes)
    response.raise_for_status()
    return response.json()["upload_url"]

def transcribe_audio(audio_segment, api_key):
    with io.BytesIO() as f:
        audio_segment.export(f, format="wav")
        f.seek(0)
        upload_url = upload_audio(f, api_key)

    json_data = {"audio_url": upload_url, "language_code": "en_us"}
    headers = {"authorization": api_key, "content-type": "application/json"}
    resp = requests.post("https://api.assemblyai.com/v2/transcript", json=json_data, headers=headers)
    transcript_id = resp.json()['id']

    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        polling_resp = requests.get(polling_endpoint, headers=headers)
        data = polling_resp.json()
        if data['status'] == "completed":
            return data['text']
        elif data['status'] == "error":
            raise RuntimeError(f"Transcription failed: {data['error']}")
        time.sleep(2)

# -----------------------------
# Gemini Query Validator
# -----------------------------
def is_query_valid(query: str, gemini_key: str) -> dict:
    genai.configure(api_key=gemini_key)
    model_gen = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    You are a compliance officer and finance gatekeeper.
    Determine if this query is finance-related and ethically acceptable.
    Respond ONLY with JSON:
    {{"is_finance": true, "is_ethical": true, "reason": "..."}}

    User Query: {query}
    """

    try:
        response = model_gen.generate_content(prompt)
        raw_text = response.text.strip()
        return json.loads(raw_text[raw_text.find("{"):raw_text.rfind("}")+1])
    except Exception as e:
        return {"is_finance": False, "is_ethical": False, "reason": str(e)}

# -----------------------------
# Voice or Text Input
# -----------------------------
user_query = ""

if record_query:
    st.markdown("### 🎤 Live Voice Input")
    webrtc_streamer(
        key="audio-recorder",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=1024,
        audio_frame_callback=processor.recv,
        media_stream_constraints={"audio": True, "video": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )

    if st.button("🔁 Transcribe Voice"):
        if not assemblyai_api_key:
            st.error("Please enter your AssemblyAI API key.")
        else:
            with st.spinner("Transcribing..."):
                try:
                    user_query = transcribe_audio(processor.audio, assemblyai_api_key)
                    st.success("Transcription complete")
                    st.markdown(f"**You said:** `{user_query}`")
                except Exception as e:
                    st.error(f"Error: {e}")
else:
    user_query = st.text_area(
        "💬 Enter your financial query:",
        placeholder="e.g., What’s our exposure in Asia tech stocks?",
        height=150,
    )

# -----------------------------
# Run CrewAI Agent if Query Valid
# -----------------------------
if st.button("🚀 Get Market Brief"):
    if not user_query.strip():
        st.error("Please enter or record a query.")
        st.stop()

    st.info("Validating query...")
    result = is_query_valid(user_query, gemini_api_key)

    if not result['is_finance']:
        st.error("📢 Not a financial query.")
        st.markdown(f"Reason: {result['reason']}")
        st.stop()
    if not result['is_ethical']:
        st.error("⚠️ Query deemed unethical.")
        st.markdown(f"Reason: {result['reason']}")
        st.stop()

    st.info("🧠 Running analysis with CrewAI...")
    crew = BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew()
    result = crew.crew().kickoff(inputs={'query': user_query})

    st.markdown("### 📊 Result:")
    st.markdown(result)

    if voice_enabled:
        st.markdown("### 🎧 Audio Response")
        try:
            from gtts import gTTS
            tts = gTTS(text=result, lang="en")
            audio_output = io.BytesIO()
            tts.write_to_fp(audio_output)
            audio_output.seek(0)
            st.audio(audio_output, format="audio/mp3")
        except Exception as e:
            st.warning(f"Voice synthesis failed: {e}")
