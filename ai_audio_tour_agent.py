import streamlit as st
import asyncio
from pathlib import Path
from gtts import gTTS
from manager import TourManager
from agent import set_anthropic_client


def tts(text: str, lang: str = "en") -> Path:
    """Convert text to speech using Google TTS (free, no API key required)."""
    speech_file_path = Path(__file__).parent / "speech_tour.mp3"
    tts_audio = gTTS(text=text, lang=lang, slow=False)
    tts_audio.save(str(speech_file_path))
    return speech_file_path


def run_async(func, *args, **kwargs):
    """Helper to run async functions in Streamlit."""
    try:
        return asyncio.run(func(*args, **kwargs))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))


# Set page config for a better UI
st.set_page_config(
    page_title="AI Audio Tour Agent (Claude)",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .welcome-card h3 {
        margin: 0 0 0.5rem 0;
        color: white;
    }
    .welcome-card p {
        margin: 0;
        opacity: 0.9;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for API key
with st.sidebar:
    st.title("🔑 Settings")
    api_key = st.text_input("Anthropic API Key:", type="password", help="Enter your Claude API key")
    if api_key:
        st.session_state["ANTHROPIC_API_KEY"] = api_key
        set_anthropic_client(api_key)
        st.success("API key saved!")
    
    st.markdown("---")
    st.markdown("### 🎙️ TTS Info")
    st.markdown("Using **Google TTS** (free, no API key needed)")

# Main content
st.title("🎧 AI Audio Tour Agent")
st.markdown("*Powered by Claude*")

st.markdown("""
    <div class='welcome-card'>
        <h3>Welcome to your personalized audio tour guide!</h3>
        <p>I'll help you explore any location with an engaging, natural-sounding tour tailored to your interests. Now powered by Claude AI!</p>
    </div>
""", unsafe_allow_html=True)

# Create a clean layout with cards
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📍 Where would you like to explore?")
    location = st.text_input("", placeholder="Enter a city, landmark, or location...", key="location")
    
    st.markdown("### 🎯 What interests you?")
    interests = st.multiselect(
        "",
        options=["History", "Architecture", "Culinary", "Culture"],
        default=["History", "Architecture"],
        help="Select the topics you'd like to learn about",
        key="interests"
    )

with col2:
    st.markdown("### ⏱️ Tour Settings")
    duration = st.slider(
        "Tour Duration (minutes)",
        min_value=5,
        max_value=60,
        value=10,
        step=5,
        help="Choose how long you'd like your tour to be"
    )
    
    st.markdown("### 🌐 Language")
    language = st.selectbox(
        "Audio Language",
        options=["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh-CN"],
        format_func=lambda x: {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ja": "Japanese",
            "ko": "Korean",
            "zh-CN": "Chinese"
        }.get(x, x),
        help="Select the language for the audio tour"
    )

# Generate Tour Button
if st.button("🎧 Generate Tour", type="primary"):
    if "ANTHROPIC_API_KEY" not in st.session_state:
        st.error("Please enter your Anthropic API key in the sidebar.")
    elif not location:
        st.error("Please enter a location.")
    elif not interests:
        st.error("Please select at least one interest.")
    else:
        with st.spinner(f"🤖 Claude is creating your personalized tour of {location}..."):
            mgr = TourManager()
            final_tour = run_async(
                mgr.run, location, interests, duration
            )

            # Display the tour content in an expandable section
            with st.expander("📝 Tour Content", expanded=True):
                st.markdown(final_tour)
            
            # Add a progress bar for audio generation
            with st.spinner("🎙️ Generating audio tour..."):
                progress_bar = st.progress(0)
                tour_audio = tts(final_tour, lang=language)
                progress_bar.progress(100)
            
            # Display audio player with custom styling
            st.markdown("### 🎧 Listen to Your Tour")
            st.audio(str(tour_audio), format="audio/mp3")
            
            # Add download button for the audio
            with open(tour_audio, "rb") as file:
                st.download_button(
                    label="📥 Download Audio Tour",
                    data=file,
                    file_name=f"{location.lower().replace(' ', '_')}_tour.mp3",
                    mime="audio/mp3"
                )

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666;'>Built with Claude AI by Anthropic 🧠</p>",
    unsafe_allow_html=True
)
