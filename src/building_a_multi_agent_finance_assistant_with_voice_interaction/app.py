# app.py
import os
import io
import whisper
import streamlit as st
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import soundfile as sf
import resampy
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
record_query = st.sidebar.checkbox("🎤 Record voice input instead of typing?")
voice_enabled = st.sidebar.checkbox("🔊 Enable voice output", value=True)

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# —————————————————————————
# Audio Handling Functions
# —————————————————————————
def record_audio_blob(duration=5):
    fs = 16000
    st.info("🎹 Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    audio_buffer = io.BytesIO()
    wav.write(audio_buffer, fs, recording)
    audio_buffer.seek(0)
    st.success("✅ Audio recorded in memory")
    return audio_buffer

def audio_blob_to_text(audio_blob):
    model = whisper.load_model("small")
    try:
        audio_data, sample_rate = sf.read(audio_blob, dtype='float32')
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        if sample_rate != 16000:
            audio_data = resampy.resample(audio_data, sample_rate, 16000)
        result = model.transcribe(audio_data, language="en", fp16=False)
        text = result.get('text', '').strip()
        if not text:
            raise ValueError("Empty transcription result.")
        return text
    except Exception as e:
        st.error("❌ Transcription failed. Try speaking clearly or closer to mic.")
        st.text(f"Error: {e}")
        return ""

# —————————————————————————
# Gemini Validator
# —————————————————————————
import json

def is_query_valid(query: str, gemini_key: str) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)

    model = genai.GenerativeModel("gemini-1.5-flash")

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
        response = model.generate_content(full_prompt)
        raw_text = response.text.strip()

        # Extract valid JSON portion
        json_start = raw_text.find("{")
        json_end = raw_text.rfind("}") + 1
        json_str = raw_text[json_start:json_end]

        # Convert using json.loads() instead of eval()
        result = json.loads(json_str)
        return result

    except Exception as e:
        return {
            "is_finance": False,
            "is_ethical": False,
            "reason": f"Error validating query: {e}"
        }

# —————————————————————————
# Main App Logic
# —————————————————————————
user_query = ""

if record_query:
    if st.sidebar.button("🎤 Start Recording"):
        with st.spinner("Recording..."):
            audio_blob = record_audio_blob(duration=5)
            user_query = audio_blob_to_text(audio_blob)
            st.markdown(f"📝 Transcribed Query: `{user_query}`")
            st.text(f"DEBUG: Raw transcription: '{user_query}'")
else:
    user_query = st.text_area(
        "💬 Enter your financial query:",
        placeholder="e.g., What’s our risk exposure in Asia tech stocks today?",
        height=150
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

            # Extract text output string safely
            response_text = str(result)

            if not response_text:
                raise ValueError("Empty response text for TTS.")

            # Generate audio with gTTS
            tts = gTTS(text=response_text, lang='en')
            audio_output = io.BytesIO()
            tts.write_to_fp(audio_output)
            audio_output.seek(0)

            # Play back the audio in Streamlit
            st.audio(audio_output, format="audio/mp3")

        except Exception as e:
            st.warning("🔇 Voice synthesis failed.")
            st.text(f"Error: {e}")
