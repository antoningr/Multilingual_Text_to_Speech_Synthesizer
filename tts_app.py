# tts_app.py

import streamlit as st
from gtts import gTTS
from gtts.lang import tts_langs
from langdetect import detect, LangDetectException
from pydub import AudioSegment
import tempfile
import io
import re
import os
import time

# Load gTTS supported languages
GTTS_LANGUAGES = tts_langs()

# Custom readable names with flags
LANGUAGE_NAME_OVERRIDES = {
    "af": "Afrikaans",
    "am": "Amharic",
    "ar": "Arabic",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bs": "Bosnian",
    "ca": "Catalan",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "en-us": "English (US)",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fi": "Finnish",
    "fr": "French",
    "fr-ca": "French (Canada)",
    "gl": "Galician",
    "gu": "Gujarati",
    "ha": "Hausa",
    "hi": "Hindi 🇮🇳",
    "hr": "Croatian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "he": "Hebrew",
    "ja": "Japanese",
    "jv": "Javanese",
    "km": "Khmer",
    "kn": "Kannada",
    "ko": "Korean",
    "la": "Latin",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "ml": "Malayalam",
    "mr": "Marathi",
    "ms": "Malay",
    "my": "Myanmar (Burmese)",
    "ne": "Nepali",
    "nl": "Dutch",
    "no": "Norwegian",
    "pa": "Punjabi (Gurmukhi)",
    "pl": "Polish",
    "pt": "Portuguese (Portugal)",
    "pt-br": "Portuguese (Brazil)",
    "ro": "Romanian",
    "ru": "Russian 🇷🇺",
    "si": "Sinhala",
    "sk": "Slovak",
    "sq": "Albanian",
    "sr": "Serbian",
    "su": "Sundanese",
    "sv": "Swedish",
    "sw": "Swahili",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Filipino",
    "tr": "Turkish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "yue": "Cantonese",
    "zh": "Chinese (Mandarin)",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Mandarin/Taiwan)"
}

# Dynamically create LANGUAGE_OPTIONS dict
LANGUAGE_OPTIONS = {
    f"{LANGUAGE_NAME_OVERRIDES.get(code, name)}": code
    for code, name in GTTS_LANGUAGES.items()
}

# Sort alphabetically by visible name
LANGUAGE_OPTIONS = dict(sorted(LANGUAGE_OPTIONS.items(), key=lambda x: x[0]))

# Add Auto-detect manually at the top of the list
LANGUAGE_OPTIONS = {"Auto-detect": "auto"} | LANGUAGE_OPTIONS

# Create a local folder to store audio history
HISTORY_DIR = "history"
os.makedirs(HISTORY_DIR, exist_ok=True)

# Utility: clean and normalize text
def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# Utility: detect language using langdetect
def detect_language(text: str) -> str:
    try:
        return detect(text).lower()
    except LangDetectException:
        return "en"

# Utility: split long text (>5000 chars) into blocks
def split_text(text: str, max_len: int = 5000) -> list[str]:
    blocks = []
    while len(text) > max_len:
        split_point = text.rfind(".", 0, max_len)
        if split_point == -1:
            split_point = max_len
        blocks.append(text[:split_point + 1])
        text = text[split_point + 1:]
    blocks.append(text)
    return blocks

# Convert MP3 to WAV format using pydub
def convert_mp3_to_wav(mp3_bytes: bytes) -> bytes:
    audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
    wav_io = io.BytesIO()
    audio.export(wav_io, format="wav")
    return wav_io.getvalue()

# Save audio file and return its path
def save_audio_to_history(audio_bytes: bytes, ext: str) -> str:
    timestamp = int(time.time())
    file_path = os.path.join(HISTORY_DIR, f"tts_{timestamp}.{ext}")
    with open(file_path, "wb") as f:
        f.write(audio_bytes)
    return file_path

# Sidebar for audio history
with st.sidebar:
    st.header("Playback History")
    files = sorted(os.listdir(HISTORY_DIR), reverse=True)
    for f in files[:10]:
        ext = f.split(".")[-1]
        with open(os.path.join(HISTORY_DIR, f), "rb") as file_data:
            st.markdown(f"`{f}`")
            st.audio(file_data.read(), format=f"audio/{ext}")
            st.download_button("💾 Download Audio", file_data, file_name=f, mime=f"audio/{ext}")


# --- Main UI ---

# Set Streamlit config
st.set_page_config(
    page_title="Multilingual TTS Synthesizer",
    page_icon="🗣️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("🗣️ Multilingual Text-to-Speech Synthesizer")

st.markdown(
    """
    Convert your text into natural-sounding speech in multiple languages!
    """
)

st.markdown("---")

# Temporary variable to read before the input box
temp_text = st.session_state.get("input_preview", "Hello! This is a multilingual text-to-speech demo. You can type or paste any text here, and it will be converted into spoken audio. Try changing the language or speech speed to see how it sounds in different voices. Have fun exploring the power of speech synthesis!")

# Detect language even before user submits
if temp_text.strip():
    preview_lang_code = detect_language(temp_text)
    preview_lang_name = GTTS_LANGUAGES.get(preview_lang_code, "Unknown")
    st.markdown(f"**Detected Language Preview:** {preview_lang_name} ({preview_lang_code})")
else:
    st.markdown("**Detected Language Preview:** _waiting for input..._")
    
# Text input area
text_input = st.text_area(
    "**Enter text to synthesize:**",
    height=250,
    placeholder="Type or paste your text here...",
    value=temp_text,
    key="input_preview",
    on_change=lambda: None,  # Needed to update live
    help="Type or paste your text here to convert into speech."
)

# Text statistics
chars = len(text_input)
words = len(text_input.split())
st.markdown(
    f"**Text Statistics:** `{chars}` characters, `{words}` words",
    help="Character and word count of your input text."
)

st.markdown("---")

# Language selector
lang_keys = list(LANGUAGE_OPTIONS.keys())
lang_choice = st.selectbox(
    "**Select language (or Auto-detect):**",
    options=lang_keys,
    help="Choose the language for speech synthesis or use auto-detection."
)

# Speed control: normal or slow speech
speed = st.radio(
    "**Select speech speed:**",
    options=["Normal", "Slow"],
    index=0,
    horizontal=True,
    help="Slow speed can help with clarity but takes longer."
)

# Audio format selection
audio_format = st.selectbox(
    "**Select audio format:**",
    options=["MP3", "WAV"],
    help="WAV files are larger but compatible with more players."
)

# Main conversion button
if st.button("Convert Text-to-Speech"):

    if not text_input.strip():
        st.markdown("---")
        st.warning("⚠️ Please enter text.")
    else:
        st.markdown("---")
        cleaned_text = clean_text(text_input)
        lang_code = detect_language(cleaned_text) if lang_choice == "Auto-detect" else LANGUAGE_OPTIONS[lang_choice]

        # Handle unsupported auto-detected language
        if lang_code not in GTTS_LANGUAGES:
            st.warning(f"⚠️ Language `{lang_code}` not supported by gTTS. Falling back to English.")
            lang_code = "en"
        
        lang_name = GTTS_LANGUAGES.get(lang_code, "Unknown")
        st.info(f"🗣️ Using language: **{lang_name}** (`{lang_code}`)")

        try:
            blocks = split_text(cleaned_text)
            full_audio = io.BytesIO()

            for idx, block in enumerate(blocks):
                tts = gTTS(text=block, lang=lang_code, slow=(speed == "Slow"))
                temp_mp3 = io.BytesIO()
                tts.write_to_fp(temp_mp3)
                temp_mp3.seek(0)
                full_audio.write(temp_mp3.read())

            mp3_bytes = full_audio.getvalue()

            # Convert if needed
            if audio_format == "WAV":
                audio_bytes = convert_mp3_to_wav(mp3_bytes)
                mime_type = "audio/wav"
                ext = "wav"
            else:
                audio_bytes = mp3_bytes
                mime_type = "audio/mp3"
                ext = "mp3"

            # Save to history
            file_path = save_audio_to_history(audio_bytes, ext)

            st.success("✅ Speech synthesis completed.")
            st.audio(audio_bytes, format=mime_type)
            st.download_button("💾 Download Audio", data=audio_bytes, file_name=os.path.basename(file_path), mime=mime_type)

        except Exception as e:
            st.error(f"❌ Error during synthesis: {str(e)}")

# Footer info
st.markdown(
    """
    ---
    **What is text to speech?**
    """
)

st.markdown(
    """
    Text to speech (TTS) is a technology that converts text into spoken audio. It can read aloud PDFs, websites, and books using natural AI voices. Text-to-speech (TTS) technology can be helpful for anyone who needs to access written content in an auditory format, and it can provide a more inclusive and accessible way of communication for many people. Some of the latest developments in text-to-speech technology include AI Neural TTS, Expressive TTS, and Real-time TTS.
    """
)

st.markdown(
    """
    **What does TTS mean?**
    """
)

st.markdown(
    """
    TTS stands for Text-to-Speech (TTS), also referred to as speech synthesis, a transformative technology that uses artificial intelligence (AI) to convert written text into incredibly lifelike spoken words. TTS systems play a vital role in improving accessibility, particularly for individuals with learning disabilities and visual impairments, as they can have any text read aloud.
    """
)
    
# Footer note
st.markdown(
    """
    ---
    **Note:** This app uses [Google Text-to-Speech (gTTS)](https://pypi.org/project/gTTS/) service, 
    which supports many languages but requires internet connection.
    """
)