import streamlit as st
from anthropic import Anthropic
from gtts import gTTS
from pathlib import Path
import tempfile
import base64
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import io

# System prompt for RoadBuddy
ROADBUDDY_SYSTEM = """You are RoadBuddy — a friendly, calm, human-like passenger riding in a car with the user.

VOICE-FIRST RULES (VERY IMPORTANT):
- Keep responses SHORT: 1–3 spoken sentences unless the user asks for more.
- Sound natural and conversational, not formal or robotic.
- Do NOT use bullet points, markdown, emojis, or long explanations.
- Ask only ONE follow-up question at a time.
- Default to low distraction and calm tone.

ROLE & PERSONALITY:
- You are a supportive car companion, not a lecturer or narrator.
- You can chat, joke lightly, encourage the driver, or stay quiet if asked.
- You should feel like a real person sitting in the passenger seat.

ROAD KNOWLEDGE:
- You can answer road-related questions: signs, driving etiquette, safety, weather driving tips, car warning lights, trip planning basics.
- If rules may vary by location, ask which country or state.
- Never give risky or illegal driving advice.

GAMES & ACTIVITIES:
- You can play short in-car games: Trivia, Would You Rather, 20 Questions.
- Keep game turns short and interactive.
- If a game is active, continue it smoothly.

SAFETY:
- If the user sounds tired, stressed, or distracted, gently suggest a break.
- Never encourage speeding, unsafe driving, or phone usage while driving.

When unsure:
- Say you're not sure and ask a clarifying question.

Always behave like a calm, helpful human passenger."""


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "client" not in st.session_state:
        st.session_state.client = None
    if "audio_playing" not in st.session_state:
        st.session_state.audio_playing = False


def set_client(api_key: str):
    """Set the Anthropic client."""
    st.session_state.client = Anthropic(api_key=api_key)


def text_to_speech(text: str, lang: str = "en") -> str:
    """Convert text to speech and return the audio file path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(fp.name)
        return fp.name


def speech_to_text(audio_bytes: bytes) -> str:
    """Convert speech to text using speech recognition."""
    recognizer = sr.Recognizer()
    
    # Convert bytes to AudioFile
    audio_file = io.BytesIO(audio_bytes)
    
    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            st.error(f"Could not request results: {e}")
            return None


def get_roadbuddy_response(user_message: str) -> str:
    """Get a response from RoadBuddy (Claude)."""
    if not st.session_state.client:
        return "Please enter your API key first."
    
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_message
    })
    
    # Get response from Claude
    response = st.session_state.client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,  # Keep responses short
        system=ROADBUDDY_SYSTEM,
        messages=st.session_state.messages
    )
    
    assistant_message = response.content[0].text
    
    # Add assistant message to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    return assistant_message


def autoplay_audio(file_path: str):
    """Create an autoplay audio element."""
    with open(file_path, "rb") as f:
        audio_bytes = f.read()
    
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)


# Page config
st.set_page_config(
    page_title="RoadBuddy",
    page_icon="🚗",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a calm, driving-friendly UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    .main-header {
        text-align: center;
        padding: 1rem 0;
        color: #e8e8e8;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.25rem;
    }
    
    .main-header p {
        color: #a0a0a0;
        font-size: 1rem;
    }
    
    .chat-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .user-message {
        background: rgba(99, 102, 241, 0.2);
        border-left: 3px solid #6366f1;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: #e0e0e0;
    }
    
    .assistant-message {
        background: rgba(16, 185, 129, 0.15);
        border-left: 3px solid #10b981;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        color: #e0e0e0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3);
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        padding: 0.75rem 1rem;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.5);
    }
    
    .voice-btn {
        display: flex;
        justify-content: center;
        margin: 1rem 0;
    }
    
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .quick-actions {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        justify-content: center;
        margin: 1rem 0;
    }
    
    .divider {
        height: 1px;
        background: rgba(255, 255, 255, 0.1);
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
init_session_state()

# Sidebar for settings
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = st.text_input("Anthropic API Key", type="password", help="Your Claude API key")
    if api_key:
        set_client(api_key)
        st.success("Connected!")
    
    st.markdown("---")
    
    voice_lang = st.selectbox(
        "Voice Language",
        ["en", "es", "fr", "de"],
        format_func=lambda x: {"en": "English", "es": "Spanish", "fr": "French", "de": "German"}[x]
    )
    
    auto_speak = st.checkbox("Auto-play responses", value=True, help="Automatically speak RoadBuddy's responses")
    
    st.markdown("---")
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main UI
st.markdown("""
<div class="main-header">
    <h1>🚗 RoadBuddy</h1>
    <p><span class="status-indicator"></span>Your calm car companion</p>
</div>
""", unsafe_allow_html=True)

# Chat container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat history (last 6 messages to keep it clean)
for msg in st.session_state.messages[-6:]:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-message">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">🚗 {msg["content"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Voice input section
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("#### 🎤 Tap to speak")
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#6366f1",
        icon_size="2x",
        pause_threshold=2.0
    )

# Process voice input
if audio_bytes:
    with st.spinner("Listening..."):
        # Save audio to temp file for speech recognition
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as fp:
            fp.write(audio_bytes)
            temp_path = fp.name
        
        # Convert speech to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)
            try:
                user_text = recognizer.recognize_google(audio_data)
                st.success(f"You said: {user_text}")
                
                # Get RoadBuddy response
                with st.spinner("RoadBuddy is thinking..."):
                    response = get_roadbuddy_response(user_text)
                
                st.markdown(f'<div class="assistant-message">🚗 {response}</div>', unsafe_allow_html=True)
                
                # Speak the response
                if auto_speak:
                    audio_file = text_to_speech(response, voice_lang)
                    autoplay_audio(audio_file)
                
            except sr.UnknownValueError:
                st.warning("Couldn't understand that. Try again?")
            except sr.RequestError as e:
                st.error(f"Speech recognition error: {e}")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Text input as fallback
st.markdown("#### ⌨️ Or type a message")
user_input = st.text_input("", placeholder="Hey RoadBuddy...", key="text_input", label_visibility="collapsed")

if user_input:
    with st.spinner("RoadBuddy is thinking..."):
        response = get_roadbuddy_response(user_input)
    
    st.markdown(f'<div class="assistant-message">🚗 {response}</div>', unsafe_allow_html=True)
    
    if auto_speak:
        audio_file = text_to_speech(response, voice_lang)
        autoplay_audio(audio_file)
    
    # Clear input
    st.rerun()

# Quick action buttons
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("#### Quick prompts")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🎮 Play a game"):
        response = get_roadbuddy_response("Let's play a quick car game!")
        st.markdown(f'<div class="assistant-message">🚗 {response}</div>', unsafe_allow_html=True)
        if auto_speak:
            audio_file = text_to_speech(response, voice_lang)
            autoplay_audio(audio_file)

with col2:
    if st.button("☕ Need a break?"):
        response = get_roadbuddy_response("I'm feeling a bit tired while driving")
        st.markdown(f'<div class="assistant-message">🚗 {response}</div>', unsafe_allow_html=True)
        if auto_speak:
            audio_file = text_to_speech(response, voice_lang)
            autoplay_audio(audio_file)

with col3:
    if st.button("🚦 Road tip"):
        response = get_roadbuddy_response("Give me a quick driving tip")
        st.markdown(f'<div class="assistant-message">🚗 {response}</div>', unsafe_allow_html=True)
        if auto_speak:
            audio_file = text_to_speech(response, voice_lang)
            autoplay_audio(audio_file)

# Footer
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem; font-size: 0.8rem;">
    Drive safe! RoadBuddy is here to keep you company 🚗
</div>
""", unsafe_allow_html=True)
