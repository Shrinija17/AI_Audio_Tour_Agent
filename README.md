# 🎧 Self-Guided AI Audio Tour Agent (Claude-Powered)

A conversational voice agent system that generates immersive, self-guided audio tours based on the user's **location**, **areas of interest**, and **tour duration**. Built with **Claude AI** by Anthropic and Google TTS for natural speech output.

---

## 🚀 Features

### 🎙️ Multi-Agent Architecture (Powered by Claude)

- **Planner Agent**  
  Analyzes location, interests, and duration to create optimal time allocation.

- **Orchestrator Agent**  
  Coordinates the overall tour flow, manages transitions, and assembles content from all expert agents.

- **History Agent**  
  Delivers insightful historical narratives with an authoritative voice.

- **Architecture Agent**  
  Highlights architectural details, styles, and design elements using a descriptive and technical tone.

- **Culture Agent**  
  Explores local customs, traditions, and artistic heritage with an enthusiastic voice.

- **Culinary Agent**  
  Describes iconic dishes and food culture in a passionate and engaging tone.

---

### 📍 Location-Aware Content Generation

- Dynamic content generation based on user-input **location**
- Personalized content delivery filtered by user **interest categories**
- Claude's knowledge for rich, detailed information

---

### ⏱️ Customizable Tour Duration

- Selectable tour length: **5 to 60 minutes**
- Time allocations adapt to user interest weights and location relevance
- Ensures well-paced and proportioned narratives across sections

---

### 🔊 Text-to-Speech Output

- Audio generated using **Google TTS** (free, no API key required)
- Multiple language support (English, Spanish, French, German, Italian, Portuguese, Japanese, Korean, Chinese)

---

## 🛠️ How to Get Started

1. **Clone the GitHub repository**

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd voice_ai_agents/ai_audio_tour_agent
```

2. **Install the required dependencies**

```bash
pip install -r requirements.txt
```

3. **Get your Anthropic API Key**

- Sign up for an [Anthropic account](https://console.anthropic.com/) and obtain your API key.

4. **Run the Streamlit App**

```bash
streamlit run ai_audio_tour_agent.py
```

5. **Enter your API key** in the sidebar and start exploring!

---

## 📁 Project Structure

```
ai_audio_tour_agent/
├── ai_audio_tour_agent.py  # Main Streamlit app
├── agent.py                # Claude-powered agent definitions
├── manager.py              # Tour orchestration logic
├── printer.py              # Console progress display
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🔑 API Keys Required

| Service | Purpose | Required |
|---------|---------|----------|
| Anthropic (Claude) | AI content generation | ✅ Yes |
| Google TTS | Text-to-speech | ❌ No (free) |

---

## 💡 Usage Tips

- Select multiple interests for a richer, more diverse tour
- Longer durations (30-60 min) provide more detailed content
- Try different languages for the audio output
- Download the MP3 to listen offline while exploring!