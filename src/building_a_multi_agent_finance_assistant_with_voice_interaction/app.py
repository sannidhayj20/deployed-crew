import sys
import pysqlite3
sys.modules["sqlite3"] = pysqlite3
import os
import io
import json
import time
import requests
import streamlit as st
import google.generativeai as genai
from crew import BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew

# Page config
st.set_page_config(page_title="🎹 Global Finance Assistant", page_icon="🎹", layout="wide")
st.title("🎹 Morning Market Brief Assistant")
st.markdown("Speak or type your financial query — get a spoken response.")

# Sidebar
st.sidebar.header("🔧 Settings")
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
gemini_api_key = st.sidebar.text_input("🔮 Gemini API Key", type="password")
assemblyai_api_key = st.sidebar.text_input("🗣️ AssemblyAI API Key", type="password")
record_query = st.sidebar.checkbox("🎤 Record voice input instead of typing?")
voice_enabled = st.sidebar.checkbox("🔊 Enable voice output", value=True)

if openai_api_key:
    os.environ["OPENAI_API_KEY"] = openai_api_key

# —————————————————————————
# AssemblyAI Helpers
# —————————————————————————
def upload_audio(audio_bytes, api_key):
    headers = {
        "authorization": api_key,
        "transfer-encoding": "chunked"
    }
    response = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=audio_bytes)
    response.raise_for_status()
    return response.json()["upload_url"]

def request_transcription(upload_url, api_key):
    headers = {"authorization": api_key, "content-type": "application/json"}
    data = {"audio_url": upload_url, "language_code": "en_us"}
    response = requests.post("https://api.assemblyai.com/v2/transcript", headers=headers, json=data)
    response.raise_for_status()
    return response.json()["id"]

def get_transcription_result(transcript_id, api_key):
    headers = {"authorization": api_key}
    polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        response = requests.get(polling_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "completed":
            return data["text"]
        elif data["status"] == "error":
            raise RuntimeError(f"Transcription error: {data['error']}")
        time.sleep(2)

def transcribe_audio_bytes(audio_bytes, api_key):
    upload_url = upload_audio(audio_bytes, api_key)
    transcript_id = request_transcription(upload_url, api_key)
    return get_transcription_result(transcript_id, api_key)

# —————————————————————————
# Gemini Validator
# —————————————————————————
def is_query_valid(query, gemini_key):
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are a compliance officer. Validate this query. Output ONLY JSON like:
    {{
      "is_finance": true,
      "is_ethical": true,
      "reason": "..." 
    }}

    Query: {query}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        json_part = text[text.find("{"):text.rfind("}") + 1]
        return json.loads(json_part)
    except Exception as e:
        return {"is_finance": False, "is_ethical": False, "reason": f"Validation failed: {e}"}

# —————————————————————————
# Main Input Section
# —————————————————————————
user_query = ""

from audiorecorder import audiorecorder
from pydub import AudioSegment

st.markdown("### 🎤 Record your voice query")

audio = audiorecorder("Click to record", "Click to stop recording")

if len(audio) > 0:
    st.audio(audio.export().read(), format="audio/wav")

    audio.export("audio.wav", format="wav")
    st.success("✅ Audio recorded and saved.")

    if st.button("📝 Transcribe Audio"):
        if not assemblyai_api_key:
            st.error("AssemblyAI API key is missing.")
        else:
            with st.spinner("Transcribing audio..."):
                try:
                    with open("audio.wav", "rb") as f:
                        audio_bytes = f.read()
                    user_query = transcribe_audio_bytes(audio_bytes, assemblyai_api_key)
                    st.markdown(f"📝 **Transcribed Query**: `{user_query}`")
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
# —————————————————————————
# Process Input and Run Crew
# —————————————————————————
if st.button("🚀 Get Market Brief"):
    if not user_query.strip():
        st.error("Please enter or record a valid query.")
        st.stop()

    st.info("🔍 Validating query...")
    validation = is_query_valid(user_query, gemini_api_key)

    if not validation["is_finance"]:
        st.error("🛑 Not a finance-related query.")
        st.markdown(f"🔎 Reason: {validation['reason']}")
        st.stop()

    if not validation["is_ethical"]:
        st.error("⚠️ Query flagged as potentially unethical.")
        st.markdown(f"📌 Reason: {validation['reason']}")
        st.stop()

    st.info("🤖 Running multi-agent finance assistant...")
    crew = BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew()
    result = crew.crew().kickoff(inputs={"query": user_query})

    st.markdown("## 📊 Market Brief Result")
    st.markdown(result)

    if voice_enabled:
        st.markdown("### 🔊 Voice Output")
        try:
            from gtts import gTTS
            tts = gTTS(text=result, lang="en")
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            st.audio(audio_io, format="audio/mp3")
        except Exception as e:
            st.warning("🔇 Failed to synthesize voice.")
            st.text(f"Error: {e}")
