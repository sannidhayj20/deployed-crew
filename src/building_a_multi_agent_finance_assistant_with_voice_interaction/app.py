import sys
import os
import io
import json
import time
import streamlit as st
from io import BytesIO
import requests
from gtts import gTTS
import assemblyai as aai

from crew import BuildingAMultiAgentFinanceAssistantWithVoiceInteractionCrew

# --------------------
# Page config
# --------------------
st.set_page_config(page_title="💵 Global Finance Assistant", page_icon="💵", layout="wide")
st.title("💵 Morning Market Brief Assistant")
st.markdown("Speak or type your financial query — get a spoken response.")

# --------------------
# Load secrets
# --------------------
aai.api_key = st.secrets["ASSEMBLYAI_API_KEY"]
openai_api_key = st.secrets["OPENAI_API_KEY"]
gemini_api_key = st.secrets["GEMINI_API_KEY"]

os.environ["OPENAI_API_KEY"] = openai_api_key

# --------------------
# Sidebar settings
# --------------------
st.sidebar.header("🔧 Settings")
record_query = st.sidebar.checkbox("🎤 Record voice input instead of typing?")
voice_enabled = st.sidebar.checkbox("🔊 Enable voice output", value=True)

# --------------------
# AssemblyAI Transcription
# --------------------
def transcribe_audio_bytes(audio_bytes):
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_bytes)
        return transcript.text
    except Exception as e:
        raise RuntimeError(f"AssemblyAI transcription error: {e}")

# --------------------
# Gemini Query Validator
# --------------------
def is_query_valid(query, gemini_key):
    import google.generativeai as genai
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
                user_query = transcribe_audio_bytes(audio_bytes)
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
if not user_query and "transcribed_query" in st.session_state:
    user_query = st.session_state.transcribed_query

if st.button("🚀 Get Market Brief"):
    st.markdown("⚠️ Responses Do take about 5 minutes to generate")

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
    st.markdown(str(result))

    if voice_enabled:
        st.markdown("### 🔊 Voice Output")
        try:
            tts = gTTS(text=str(result), lang="en")
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            audio_io.seek(0)
            st.audio(audio_io, format="audio/mp3")
        except Exception as e:
            st.warning("🔇 Failed to synthesize voice.")
            st.text(f"Error: {e}")
