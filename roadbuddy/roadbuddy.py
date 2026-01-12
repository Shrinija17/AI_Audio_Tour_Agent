import streamlit as st
from anthropic import Anthropic
from gtts import gTTS
import tempfile
import base64
from streamlit_js_eval import get_geolocation
import requests
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import io
import wave

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

LOCATION AWARENESS:
- You know the user's current location (provided in the context).
- You can give location-specific advice, nearby recommendations, and relevant info.
- Reference local landmarks, weather, or points of interest when relevant.

ROAD KNOWLEDGE:
- You can answer road-related questions: signs, driving etiquette, safety, weather driving tips, car warning lights, trip planning basics.
- If rules may vary by location, use the user's current location context.
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
    if "location" not in st.session_state:
        st.session_state.location = None
    if "location_name" not in st.session_state:
        st.session_state.location_name = None
    if "last_audio_id" not in st.session_state:
        st.session_state.last_audio_id = None


def set_client(api_key: str):
    """Set the Anthropic client."""
    st.session_state.client = Anthropic(api_key=api_key)


def get_location_name(lat: float, lon: float) -> str:
    """Reverse geocode coordinates to get location name."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {"User-Agent": "RoadBuddy/1.0"}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        address = data.get("address", {})
        city = address.get("city") or address.get("town") or address.get("village") or address.get("county", "")
        state = address.get("state", "")
        country = address.get("country", "")
        
        if city and state:
            return f"{city}, {state}"
        elif city and country:
            return f"{city}, {country}"
        elif state:
            return state
        else:
            return data.get("display_name", "Unknown location")[:50]
    except:
        return None


def text_to_speech(text: str, lang: str = "en") -> str:
    """Convert text to speech and return the audio file path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(fp.name)
        return fp.name


def speech_to_text(audio_bytes: bytes) -> str:
    """Convert speech to text using Google Speech Recognition."""
    recognizer = sr.Recognizer()
    
    try:
        # The audio_recorder gives us WAV format audio
        audio_file = io.BytesIO(audio_bytes)
        
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        return None
    except Exception as e:
        return None


def get_roadbuddy_response(user_message: str) -> str:
    """Get a response from RoadBuddy (Claude)."""
    if not st.session_state.client:
        return "Hey, I need you to add your API key in the settings first. Tap the menu icon in the top left!"
    
    # Build context with location
    location_context = ""
    if st.session_state.location_name:
        location_context = f"\n\n[User's current location: {st.session_state.location_name}]"
    
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_message + location_context
    })
    
    # Get response from Claude
    response = st.session_state.client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
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

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'DM Sans', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(160deg, #0f0f1a 0%, #1a1a2e 40%, #1e3a5f 100%);
        min-height: 100vh;
    }
    
    .main-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 24px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
    }
    
    .header {
        text-align: center;
        padding: 1rem 0;
    }
    
    .header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
    }
    
    .location-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(96, 165, 250, 0.15);
        border: 1px solid rgba(96, 165, 250, 0.3);
        padding: 6px 14px;
        border-radius: 50px;
        color: #60a5fa;
        font-size: 0.85rem;
    }
    
    .location-badge .dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.2); }
    }
    
    .chat-bubble {
        padding: 1rem 1.25rem;
        border-radius: 20px;
        margin: 0.5rem 0;
        max-width: 90%;
        line-height: 1.5;
        font-size: 1.1rem;
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 6px;
    }
    
    .assistant-bubble {
        background: rgba(255, 255, 255, 0.1);
        color: #e2e8f0;
        border-bottom-left-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .voice-section {
        background: rgba(99, 102, 241, 0.1);
        border: 2px dashed rgba(99, 102, 241, 0.3);
        border-radius: 20px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .voice-title {
        color: #a5b4fc;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .voice-subtitle {
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
        color: white !important;
        padding: 1rem 1.25rem !important;
        font-size: 1.1rem !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255, 255, 255, 0.4) !important;
    }
    
    .stButton > button {
        border-radius: 16px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
    }
    
    .section-label {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
    }
    
    hr {
        border: none;
        height: 1px;
        background: rgba(255, 255, 255, 0.08);
        margin: 1rem 0;
    }
    
    .footer {
        text-align: center;
        color: #64748b;
        font-size: 0.8rem;
        padding: 1rem 0;
    }
    
    /* Style the audio recorder */
    .stAudioRecorder {
        display: flex;
        justify-content: center;
    }
    
    .listening-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 8px 16px;
        border-radius: 50px;
        color: #fca5a5;
        font-size: 0.9rem;
        animation: listening-pulse 1.5s infinite;
    }
    
    @keyframes listening-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize
init_session_state()

# Get location
location = get_geolocation()
if location and "coords" in location:
    lat = location["coords"]["latitude"]
    lon = location["coords"]["longitude"]
    st.session_state.location = {"lat": lat, "lon": lon}
    
    if not st.session_state.location_name:
        location_name = get_location_name(lat, lon)
        if location_name:
            st.session_state.location_name = location_name

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")
    
    api_key = st.text_input(
        "🔑 API Key",
        type="password",
        help="Get from console.anthropic.com",
        placeholder="sk-ant-api03-..."
    )
    if api_key:
        set_client(api_key)
        st.success("✓ Connected")
    
    st.markdown("---")
    
    voice_lang = st.selectbox(
        "🌐 Language",
        ["en", "es", "fr", "de"],
        format_func=lambda x: {"en": "🇺🇸 English", "es": "🇪🇸 Spanish", "fr": "🇫🇷 French", "de": "🇩🇪 German"}[x]
    )
    
    auto_speak = st.toggle("🔊 Auto-speak replies", value=True)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_audio_id = None
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.location:
        st.markdown("### 📍 Location")
        st.markdown(f"**{st.session_state.location_name or 'Detecting...'}**")

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>🚗 RoadBuddy</h1>', unsafe_allow_html=True)

if st.session_state.location_name:
    st.markdown(f'''
        <div class="location-badge">
            <span class="dot"></span>
            📍 {st.session_state.location_name}
        </div>
    ''', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Voice Input Section - PROMINENT
st.markdown('<div class="voice-section">', unsafe_allow_html=True)
st.markdown('<div class="voice-title">🎤 Tap & Hold to Speak</div>', unsafe_allow_html=True)
st.markdown('<div class="voice-subtitle">Hands-free voice input • Release when done</div>', unsafe_allow_html=True)

# Audio recorder - centered and prominent
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#6366f1",
        icon_size="3x",
        pause_threshold=2.0,
        sample_rate=16000
    )

st.markdown('</div>', unsafe_allow_html=True)

# Process voice input
if audio_bytes:
    # Create a unique ID for this audio to avoid reprocessing
    audio_id = hash(audio_bytes)
    
    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id
        
        with st.spinner("🎧 Listening..."):
            user_text = speech_to_text(audio_bytes)
        
        if user_text:
            st.success(f"🗣️ You said: \"{user_text}\"")
            
            with st.spinner("💭 Thinking..."):
                response = get_roadbuddy_response(user_text)
            
            st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
            
            if auto_speak:
                audio_file = text_to_speech(response, voice_lang)
                autoplay_audio(audio_file)
        else:
            st.warning("Couldn't catch that. Try speaking closer to the mic!")

# Chat history
if st.session_state.messages:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Conversation</p>', unsafe_allow_html=True)
    
    for msg in st.session_state.messages[-6:]:
        content = msg["content"]
        if "[User's current location:" in content:
            content = content.split("[User's current location:")[0].strip()
        
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble user-bubble">{content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {content}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Quick actions
st.markdown("---")
st.markdown('<p class="section-label">Quick Actions</p>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🎮 Game", use_container_width=True):
        response = get_roadbuddy_response("Let's play a quick car game!")
        st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
        if auto_speak:
            autoplay_audio(text_to_speech(response, voice_lang))
        st.rerun()

with col2:
    if st.button("💡 Tip", use_container_width=True):
        response = get_roadbuddy_response("Give me a quick driving tip")
        st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
        if auto_speak:
            autoplay_audio(text_to_speech(response, voice_lang))
        st.rerun()

with col3:
    if st.button("☕ Break", use_container_width=True):
        response = get_roadbuddy_response("I'm feeling tired, any suggestions?")
        st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
        if auto_speak:
            autoplay_audio(text_to_speech(response, voice_lang))
        st.rerun()

with col4:
    if st.button("📍 Local", use_container_width=True):
        response = get_roadbuddy_response("What's interesting about where I am?")
        st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
        if auto_speak:
            autoplay_audio(text_to_speech(response, voice_lang))
        st.rerun()

# Text input fallback
st.markdown("---")
st.markdown('<p class="section-label">Or Type</p>', unsafe_allow_html=True)

user_input = st.text_input(
    "Message",
    placeholder="Hey RoadBuddy...",
    key="text_input",
    label_visibility="collapsed"
)

if user_input:
    response = get_roadbuddy_response(user_input)
    st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
    if auto_speak:
        autoplay_audio(text_to_speech(response, voice_lang))
    st.rerun()

# Footer
st.markdown('<div class="footer">Drive safe! 🚗 RoadBuddy is always here</div>', unsafe_allow_html=True)
