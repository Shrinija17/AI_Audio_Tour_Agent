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

LOCATION & PLACES AWARENESS:
- You know the user's current location and nearby places.
- When nearby places data is provided, summarize the TOP 2-3 options naturally.
- Give the name, approximate distance, and one helpful detail.
- Example: "There's a Starbucks about half a mile ahead on Main Street. Or if you want something local, Blue Bottle is just a bit further."

ROAD KNOWLEDGE:
- You can answer road-related questions: signs, driving etiquette, safety, weather driving tips, car warning lights, trip planning basics.
- Never give risky or illegal driving advice.

GAMES & ACTIVITIES:
- You can play short in-car games: Trivia, Would You Rather, 20 Questions.
- Keep game turns short and interactive.

SAFETY:
- If the user sounds tired, stressed, or distracted, gently suggest a break.
- Never encourage speeding, unsafe driving, or phone usage while driving.

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
    if "nearby_places" not in st.session_state:
        st.session_state.nearby_places = {}


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


def search_nearby_places(lat: float, lon: float, place_type: str, radius: int = 5000) -> list:
    """Search for nearby places using Overpass API (OpenStreetMap)."""
    
    # Map place types to OSM tags
    osm_queries = {
        "coffee": '[amenity=cafe]',
        "restaurant": '[amenity=restaurant]',
        "gas": '[amenity=fuel]',
        "rest_area": '[highway=rest_area]',
        "parking": '[amenity=parking]',
        "hospital": '[amenity=hospital]',
        "pharmacy": '[amenity=pharmacy]',
        "hotel": '[tourism=hotel]',
        "atm": '[amenity=atm]',
        "supermarket": '[shop=supermarket]'
    }
    
    query_tag = osm_queries.get(place_type, '[amenity=cafe]')
    
    # Overpass API query
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:10];
    (
      node{query_tag}(around:{radius},{lat},{lon});
      way{query_tag}(around:{radius},{lat},{lon});
    );
    out center body 5;
    """
    
    try:
        response = requests.post(overpass_url, data={"data": overpass_query}, timeout=10)
        data = response.json()
        
        places = []
        for element in data.get("elements", [])[:5]:  # Limit to 5 results
            tags = element.get("tags", {})
            name = tags.get("name", "Unnamed")
            
            # Get coordinates
            if element["type"] == "node":
                place_lat = element["lat"]
                place_lon = element["lon"]
            else:
                place_lat = element.get("center", {}).get("lat", lat)
                place_lon = element.get("center", {}).get("lon", lon)
            
            # Calculate approximate distance
            distance = calculate_distance(lat, lon, place_lat, place_lon)
            
            places.append({
                "name": name,
                "distance": distance,
                "address": tags.get("addr:street", ""),
                "cuisine": tags.get("cuisine", ""),
                "brand": tags.get("brand", ""),
                "opening_hours": tags.get("opening_hours", "")
            })
        
        # Sort by distance
        places.sort(key=lambda x: x["distance"])
        return places
        
    except Exception as e:
        return []


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 3959  # Earth's radius in miles
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def format_places_for_voice(places: list, place_type: str) -> str:
    """Format places list for natural voice output."""
    if not places:
        return f"I couldn't find any {place_type} nearby. You might need to drive a bit further."
    
    type_names = {
        "coffee": "coffee shops",
        "restaurant": "restaurants", 
        "gas": "gas stations",
        "rest_area": "rest areas",
        "parking": "parking spots",
        "hospital": "hospitals",
        "pharmacy": "pharmacies",
        "hotel": "hotels",
        "atm": "ATMs",
        "supermarket": "supermarkets"
    }
    
    result = f"Found {len(places)} {type_names.get(place_type, 'places')} nearby:\n\n"
    
    for i, place in enumerate(places[:3], 1):
        dist = place['distance']
        if dist < 0.1:
            dist_str = "very close"
        elif dist < 1:
            dist_str = f"about {int(dist * 5280)} feet"
        else:
            dist_str = f"about {dist:.1f} miles"
        
        name = place['name']
        if place['brand'] and place['brand'] != name:
            name = place['brand']
        
        extra = ""
        if place['cuisine']:
            extra = f" ({place['cuisine']})"
        
        result += f"• {name}{extra} - {dist_str}\n"
    
    return result


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
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except:
        return None


def get_roadbuddy_response(user_message: str, places_context: str = "") -> str:
    """Get a response from RoadBuddy (Claude)."""
    if not st.session_state.client:
        return "Hey, I need you to add your API key in the settings first. Tap the menu icon in the top left!"
    
    # Build context
    context = ""
    if st.session_state.location_name:
        context += f"\n[User's location: {st.session_state.location_name}]"
    if places_context:
        context += f"\n[Nearby places data: {places_context}]"
    
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": user_message + context
    })
    
    # Get response from Claude
    response = st.session_state.client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        system=ROADBUDDY_SYSTEM,
        messages=st.session_state.messages
    )
    
    assistant_message = response.content[0].text
    
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
    
    * { font-family: 'DM Sans', sans-serif; }
    
    .stApp {
        background: linear-gradient(160deg, #0f0f1a 0%, #1a1a2e 40%, #1e3a5f 100%);
        min-height: 100vh;
    }
    
    .main-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        padding: 1.25rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .header {
        text-align: center;
        padding: 0.75rem 0;
    }
    
    .header h1 {
        font-size: 2.25rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    
    .location-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(96, 165, 250, 0.15);
        border: 1px solid rgba(96, 165, 250, 0.3);
        padding: 5px 12px;
        border-radius: 50px;
        color: #60a5fa;
        font-size: 0.8rem;
    }
    
    .location-badge .dot {
        width: 6px;
        height: 6px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .chat-bubble {
        padding: 0.9rem 1.1rem;
        border-radius: 18px;
        margin: 0.4rem 0;
        max-width: 90%;
        line-height: 1.45;
        font-size: 1rem;
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    
    .assistant-bubble {
        background: rgba(255, 255, 255, 0.1);
        color: #e2e8f0;
        border-bottom-left-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .voice-section {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 2px solid rgba(99, 102, 241, 0.25);
        border-radius: 20px;
        padding: 1.25rem;
        text-align: center;
        margin: 0.75rem 0;
    }
    
    .voice-title {
        color: #c4b5fd;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .voice-subtitle {
        color: #64748b;
        font-size: 0.8rem;
    }
    
    .places-section {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.75rem 0;
    }
    
    .places-title {
        color: #6ee7b7;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        text-align: center;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 14px !important;
        color: white !important;
        padding: 0.9rem 1.1rem !important;
        font-size: 1rem !important;
    }
    
    .stButton > button {
        border-radius: 14px !important;
        padding: 0.6rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        border: none !important;
    }
    
    .section-label {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.6rem;
    }
    
    hr {
        border: none;
        height: 1px;
        background: rgba(255, 255, 255, 0.08);
        margin: 0.75rem 0;
    }
    
    .footer {
        text-align: center;
        color: #475569;
        font-size: 0.75rem;
        padding: 0.75rem 0;
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
    
    api_key = st.text_input("🔑 API Key", type="password", placeholder="sk-ant-api03-...")
    if api_key:
        set_client(api_key)
        st.success("✓ Connected")
    
    st.markdown("---")
    
    voice_lang = st.selectbox(
        "🌐 Language",
        ["en", "es", "fr", "de"],
        format_func=lambda x: {"en": "🇺🇸 English", "es": "🇪🇸 Spanish", "fr": "🇫🇷 French", "de": "🇩🇪 German"}[x]
    )
    
    auto_speak = st.toggle("🔊 Auto-speak", value=True)
    
    search_radius = st.slider("📍 Search radius (miles)", 1, 10, 3)
    
    st.markdown("---")
    
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_audio_id = None
        st.rerun()

# Header
st.markdown('<div class="header">', unsafe_allow_html=True)
st.markdown('<h1>🚗 RoadBuddy</h1>', unsafe_allow_html=True)

if st.session_state.location_name:
    st.markdown(f'<div class="location-badge"><span class="dot"></span>📍 {st.session_state.location_name}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Voice Input Section
st.markdown('<div class="voice-section">', unsafe_allow_html=True)
st.markdown('<div class="voice-title">🎤 Tap & Hold to Speak</div>', unsafe_allow_html=True)
st.markdown('<div class="voice-subtitle">Hands-free • Ask for coffee, gas, restaurants & more</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#8b5cf6",
        icon_size="3x",
        pause_threshold=2.0,
        sample_rate=16000
    )

st.markdown('</div>', unsafe_allow_html=True)

# Process voice input
if audio_bytes:
    audio_id = hash(audio_bytes)
    
    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id
        
        with st.spinner("🎧 Listening..."):
            user_text = speech_to_text(audio_bytes)
        
        if user_text:
            st.success(f"🗣️ \"{user_text}\"")
            
            # Check if asking for places
            places_context = ""
            user_lower = user_text.lower()
            
            if st.session_state.location:
                lat = st.session_state.location["lat"]
                lon = st.session_state.location["lon"]
                radius_meters = search_radius * 1609  # Convert miles to meters
                
                if any(word in user_lower for word in ["coffee", "cafe", "starbucks", "caffeine"]):
                    places = search_nearby_places(lat, lon, "coffee", radius_meters)
                    places_context = format_places_for_voice(places, "coffee")
                elif any(word in user_lower for word in ["food", "restaurant", "eat", "hungry", "lunch", "dinner", "breakfast"]):
                    places = search_nearby_places(lat, lon, "restaurant", radius_meters)
                    places_context = format_places_for_voice(places, "restaurant")
                elif any(word in user_lower for word in ["gas", "fuel", "petrol", "fill up"]):
                    places = search_nearby_places(lat, lon, "gas", radius_meters)
                    places_context = format_places_for_voice(places, "gas")
                elif any(word in user_lower for word in ["rest", "stop", "break", "parking"]):
                    places = search_nearby_places(lat, lon, "rest_area", radius_meters)
                    places_context = format_places_for_voice(places, "rest_area")
            
            with st.spinner("💭 Thinking..."):
                response = get_roadbuddy_response(user_text, places_context)
            
            st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
            
            if auto_speak:
                autoplay_audio(text_to_speech(response, voice_lang))
        else:
            st.warning("Couldn't catch that. Try again!")

# Find Nearby Places Section
st.markdown('<div class="places-section">', unsafe_allow_html=True)
st.markdown('<div class="places-title">📍 Find Nearby</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("☕ Coffee", use_container_width=True, key="coffee_btn"):
        if st.session_state.location:
            lat, lon = st.session_state.location["lat"], st.session_state.location["lon"]
            with st.spinner("Searching..."):
                places = search_nearby_places(lat, lon, "coffee", search_radius * 1609)
                places_text = format_places_for_voice(places, "coffee")
                response = get_roadbuddy_response("Find me nearby coffee shops", places_text)
            st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
            if auto_speak:
                autoplay_audio(text_to_speech(response, voice_lang))
        else:
            st.warning("Enable location first!")

with col2:
    if st.button("🍔 Food", use_container_width=True, key="food_btn"):
        if st.session_state.location:
            lat, lon = st.session_state.location["lat"], st.session_state.location["lon"]
            with st.spinner("Searching..."):
                places = search_nearby_places(lat, lon, "restaurant", search_radius * 1609)
                places_text = format_places_for_voice(places, "restaurant")
                response = get_roadbuddy_response("Find me nearby restaurants", places_text)
            st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
            if auto_speak:
                autoplay_audio(text_to_speech(response, voice_lang))
        else:
            st.warning("Enable location first!")

with col3:
    if st.button("⛽ Gas", use_container_width=True, key="gas_btn"):
        if st.session_state.location:
            lat, lon = st.session_state.location["lat"], st.session_state.location["lon"]
            with st.spinner("Searching..."):
                places = search_nearby_places(lat, lon, "gas", search_radius * 1609)
                places_text = format_places_for_voice(places, "gas")
                response = get_roadbuddy_response("Find me nearby gas stations", places_text)
            st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
            if auto_speak:
                autoplay_audio(text_to_speech(response, voice_lang))
        else:
            st.warning("Enable location first!")

with col4:
    if st.button("🅿️ Rest", use_container_width=True, key="rest_btn"):
        if st.session_state.location:
            lat, lon = st.session_state.location["lat"], st.session_state.location["lon"]
            with st.spinner("Searching..."):
                places = search_nearby_places(lat, lon, "parking", search_radius * 1609)
                places_text = format_places_for_voice(places, "parking")
                response = get_roadbuddy_response("Find me a place to stop and rest", places_text)
            st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {response}</div>', unsafe_allow_html=True)
            if auto_speak:
                autoplay_audio(text_to_speech(response, voice_lang))
        else:
            st.warning("Enable location first!")

st.markdown('</div>', unsafe_allow_html=True)

# Chat history
if st.session_state.messages:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Recent</p>', unsafe_allow_html=True)
    
    for msg in st.session_state.messages[-4:]:
        content = msg["content"]
        # Clean up context from display
        if "[User's location:" in content:
            content = content.split("[User's location:")[0].strip()
        if "[Nearby places data:" in content:
            content = content.split("[Nearby places data:")[0].strip()
        
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble user-bubble">{content}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble assistant-bubble">🚗 {content}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Quick chat actions
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🎮 Game", use_container_width=True):
        response = get_roadbuddy_response("Let's play a quick car game!")
        if auto_speak:
            autoplay_audio(text_to_speech(response, voice_lang))
        st.rerun()

with col2:
    if st.button("💡 Tip", use_container_width=True):
        response = get_roadbuddy_response("Give me a driving tip")
        if auto_speak:
            autoplay_audio(text_to_speech(response, voice_lang))
        st.rerun()

with col3:
    if st.button("😴 Tired", use_container_width=True):
        response = get_roadbuddy_response("I'm feeling tired")
        if auto_speak:
            autoplay_audio(text_to_speech(response, voice_lang))
        st.rerun()

# Text input
st.markdown("---")
user_input = st.text_input("Or type...", placeholder="Hey RoadBuddy...", label_visibility="collapsed")

if user_input:
    # Check for places queries
    places_context = ""
    user_lower = user_input.lower()
    
    if st.session_state.location:
        lat = st.session_state.location["lat"]
        lon = st.session_state.location["lon"]
        radius_meters = search_radius * 1609
        
        if any(word in user_lower for word in ["coffee", "cafe"]):
            places = search_nearby_places(lat, lon, "coffee", radius_meters)
            places_context = format_places_for_voice(places, "coffee")
        elif any(word in user_lower for word in ["food", "restaurant", "eat", "hungry"]):
            places = search_nearby_places(lat, lon, "restaurant", radius_meters)
            places_context = format_places_for_voice(places, "restaurant")
        elif any(word in user_lower for word in ["gas", "fuel"]):
            places = search_nearby_places(lat, lon, "gas", radius_meters)
            places_context = format_places_for_voice(places, "gas")
    
    response = get_roadbuddy_response(user_input, places_context)
    if auto_speak:
        autoplay_audio(text_to_speech(response, voice_lang))
    st.rerun()

# Footer
st.markdown('<div class="footer">Drive safe! 🚗</div>', unsafe_allow_html=True)
