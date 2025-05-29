import sys
import pysqlite3
sys.modules["sqlite3"] = pysqlite3

import os
import io
import json
import time
import streamlit as st
import requests
from io import BytesIO
import google.generativeai as genai
from crew import BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew
from elevenlabs.client import ElevenLabs
from gtts import gTTS

# --------------------
# Page config
# --------------------
st.set_page_config(page_title="💵 Global Finance Assistant", page_icon="💵", layout="wide")
st.title("💵 Morning Market Brief Assistant")
st.markdown("Speak or type your financial query — get a spoken response.")

# --------------------
# Load secrets
# --------------------
openai_api_key = st.secrets["OPENAI_API_KEY"]
gemini_api_key = st.secrets["GEMINI_API_KEY"]
elevenlabs_api_key = st.secrets["ELEVEN_API_KEY"]

os.environ["OPENAI_API_KEY"] = openai_api_key

# --------------------
# Sidebar settings
# --------------------
st.sidebar.header("🔧 Settings")
record_query = st.sidebar.checkbox("🎤 Record voice input instead of typing?")
voice_enabled = st.sidebar.checkbox("🔊 Enable voice output", value=True)

# --------------------
# ElevenLabs Transcription
# --------------------
elevenlabs = ElevenLabs(api_key=elevenlabs_api_key)

def transcribe_audio_bytes_elevenlabs(audio_bytes):
    try:
        transcription = elevenlabs.speech_to_text.convert(
            file=BytesIO(audio_bytes),
            model_id="scribe_v1",
            tag_audio_events=True,
            language_code="eng",
            diarize=True,
        )
        return transcription.text
    except Exception as e:
        raise RuntimeError(f"ElevenLabs transcription error: {e}")

# --------------------
# Gemini Query Validator
# --------------------
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

# --------------------
# Main Input Section
# --------------------
user_query = ""

if record_query:
    from audiorecorder import audiorecorder

    st.markdown("### 🎤 Record your voice query")
    audio = audiorecorder("Click to record", "Click to stop recording")

    if len(audio) > 0:
        audio_bytes = audio.export().read()
        st.audio(audio_bytes, format="audio/wav")

        if st.button("📝 Transcribe Audio"):
            try:
                user_query = transcribe_audio_bytes_elevenlabs(audio_bytes)
                if user_query:
                    st.session_state.transcribed_query = user_query
                    st.markdown(f"📝 **Transcribed Query**: `{user_query}`")
                else:
                    st.error("Transcription returned empty text.")
            except Exception as e:
                st.error(f"Transcription failed: {e}")
else:
    user_query = st.text_input("Enter your financial query")

# --------------------
# Process Query
# --------------------
if st.button("🚀 Get Market Brief"):
    st.markdown("⚠️ Responses Do take about 5 minutes to generate")
    if not user_query.strip():
        st.error("Please enter or record a valid query.")
        st.stop()

    st.info("🔍 Validating query...")
    validation = is_query_valid(user_query, st.secrets["GEMINI_API_KEY"])

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
    st.markdown(str(result))  # Safely display result

    if voice_enabled:
        st.markdown("### 🔊 Voice Output")
        try:
            tts = gTTS(text=str(result), lang="en")  # Ensure result is string
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            st.audio(audio_io, format="audio/mp3")
        except Exception as e:
            st.warning("🔇 Failed to synthesize voice.")
            st.text(f"Error: {e}")
