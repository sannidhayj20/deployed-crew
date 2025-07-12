import sys
import pysqlite3
sys.modules["sqlite3"] = pysqlite3
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
aai.api_key = st.secrets["ASSEMBLY_AI_API"]
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
# Gemini Query Validator with Suggestions
# --------------------
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()  # Loads variables from .env into os.environ
client = OpenAI()  # Uses OPENAI_API_KEY from the environment

def is_query_valid(query):
    system_prompt = """
You are a compliance officer for a financial assistant.

Evaluate the following query and respond ONLY with JSON like:
{
  "is_finance": true,
  "is_ethical": true,
  "confidence": 42,
  "reason": "Explain the confidence level briefly.",
  "suggestions": [
    "Improved version of the query suggestion 1",
    "Improved version of the query suggestion 2"
  ]
}
"""
    user_prompt = f"Query: {query}"

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500,
        )

        text_response = response.choices[0].message.content.strip()
        json_part = text_response[text_response.find("{"):text_response.rfind("}") + 1]
        return json.loads(json_part)

    except Exception as e:
        return {
            "is_finance": False,
            "is_ethical": False,
            "confidence": 0,
            "reason": f"Validation failed: {e}",
            "suggestions": []
        }

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
    st.markdown("🧑‍🏭 Responses may take 1 to 5 minutes for common tasks")

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

    if validation.get("confidence", 0) < 50:
        reason = validation.get("reason", "Low confidence in this query.")
        confidence = validation.get("confidence", 0)
        suggestions = validation.get("suggestions", [])

        st.error("🤔 Gemini has low confidence in this query.")
        st.markdown(f"📉 Confidence Score: **{confidence}%**")
        st.markdown(f"📌 Reason: {reason}")

        voice_message = f"The system has low confidence in your query. Confidence is {confidence} percent. Reason: {reason}."

        if suggestions:
            st.markdown("### 💡 Suggestions to improve your query:")
            for s in suggestions:
                st.markdown(f"- {s}")
            suggestion_text = "Here are some suggestions: " + "; ".join(suggestions)
            voice_message += " " + suggestion_text
        else:
            voice_message += " Try making your query more specific, financial in nature, and clearly ethical."

        # 🔊 Play voice response
        if voice_enabled:
            try:
                tts = gTTS(text=voice_message, lang="en")
                audio_io = io.BytesIO()
                tts.write_to_fp(audio_io)
                audio_io.seek(0)
                st.markdown("### 🔊 Voice Explanation")
                st.audio(audio_io, format="audio/mp3")
            except Exception as e:
                st.warning("🔇 Failed to synthesize voice.")
                st.text(f"Error: {e}")

        st.stop()

    # --------------------
    # Run Multi-Agent Crew
    # --------------------
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
