# AI Voice Agents Collection

A collection of voice-powered AI agents built with Claude API and Streamlit.

---

## 🎧 AI Audio Tour Agent

Generate personalized, self-guided audio tours for any location based on your interests.

**Features:**
- Multi-agent architecture (History, Architecture, Culture, Culinary)
- Customizable tour duration (5-60 minutes)
- Text-to-speech output with multi-language support

**Run:**
```bash
pip install -r requirements.txt
streamlit run ai_audio_tour_agent.py
```

[View Documentation](./README_AUDIO_TOUR.md)

---

## 🚗 RoadBuddy

A voice-first AI car companion that keeps you company on the road.

**Features:**
- Voice input (tap to speak)
- Voice output (auto-play responses)
- Short, calm responses for minimal distraction
- Car games, driving tips, and safety reminders

**Run:**
```bash
cd roadbuddy
pip install -r requirements.txt
streamlit run roadbuddy.py
```

[View Documentation](./roadbuddy/README.md)

---

## Tech Stack

- **AI**: Claude claude-sonnet-4-20250514 (Anthropic)
- **UI**: Streamlit
- **TTS**: Google TTS (free)
- **STT**: Google Speech Recognition

## Requirements

- Python 3.9+
- Anthropic API key

## License

MIT
