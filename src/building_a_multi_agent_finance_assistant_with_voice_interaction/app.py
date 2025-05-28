import sys
import pysqlite3
sys.modules["sqlite3"] = pysqlite3

import os
import io
import json
import time
import tempfile
import streamlit as st
import google.generativeai as genai
from crew import BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew
from elevenlabs import Recording, transcribe
from gtts import gTTS

# Page config
st.set_page_config(page_title="🎹 Global Finance Assistant", page_icon="🎹", layout="wide")
st.title("🎹 Morning Market Brief Assistant")
st.markdown("Speak or type your financial query — get a spoken response.")

# Sidebar
st.sidebar.header("🔧 Settings")
openai_api_key = st.sidebar.text_input("🔑 OpenAI API Key", type="password")
gemini_api_key = st.sidebar.text_input("🔮 Gemini API Key", type="password")
record_query = st.sidebar.checkbox("🎤 Record voice input instead of typing?")
voice_enabled = st.sidebar.checkbox("🔊 Enable voice output", value=True)

if openai_api_key:
    os.environ["OPENAI_API_KEY"] = openai_api_key


os.environ["ELEVEN_API_KEY"] = st.secrets("ELEVEN_API_KEY")

# ————————————————————————————
# Gemini Validator
# ————————————————————————————

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

# ————————————————————————————
# ElevenLabs Recording & Transcription
# ————————————————————————————

def record_with_elevenlabs():
    st.markdown("### 🎤 Record live query (via ElevenLabs)")
    if st.button("⏺️ Start Recording"):
        with st.spinner("Recording for 10 seconds..."):
            audio_bytes = Recording.start(duration=10)
            return audio_bytes


def transcribe_with_elevenlabs(audio_bytes):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file.flush()
            transcript = transcribe(tmp_file.name)
            return transcript.text
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return ""

# ————————————————————————————
# Main Input Section
# ————————————————————————————

user_query = ""

if record_query:
    audio = record_with_elevenlabs()

    if audio:
        st.audio(audio, format="audio/mp3")
        if st.button("📝 Transcribe Audio"):
            with st.spinner("Transcribing..."):
                user_query = transcribe_with_elevenlabs(audio)
                st.markdown(f"📝 **Transcribed Query**: `{user_query}`")
else:
    user_query = st.text_input("Enter your financial query")

# ————————————————————————————
# Process Input and Run Crew
# ————————————————————————————

if st.button("🚀 Get Market Brief"):
    if not user_query.strip():
        st.error("Please enter or record a valid query.")
        st.stop()

    st.info("🔍 Validating query...")
    validation = is_query_valid(user_query, gemini_api_key)

    if not validation["is_finance"]:
        st.error("🚩 Not a finance-related query.")
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
            tts = gTTS(text=result, lang="en")
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            st.audio(audio_io, format="audio/mp3")
        except Exception as e:
            st.warning("🔇 Failed to synthesize voice.")
            st.text(f"Error: {e}")
