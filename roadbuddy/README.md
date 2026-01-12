# 🚗 RoadBuddy - Your Calm Car Companion

A voice-first AI car companion powered by Claude. RoadBuddy sits in your passenger seat and keeps you company on the road with conversation, games, driving tips, and safety reminders.

## Features

- **Voice Input** - Tap to speak, hands-free interaction
- **Voice Output** - RoadBuddy speaks responses aloud
- **Short Responses** - Designed for minimal distraction while driving
- **Car Games** - Trivia, Would You Rather, 20 Questions
- **Road Knowledge** - Driving tips, sign meanings, safety advice
- **Safety First** - Suggests breaks when you sound tired

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run roadbuddy.py
```

3. Enter your Anthropic API key in the sidebar
4. Tap the microphone to speak or type a message

## Voice Commands Examples

- "Hey, let's play a game"
- "What does that yellow diamond sign mean?"
- "I'm feeling a bit tired"
- "Tell me something interesting"
- "How far is it to the next rest stop?"

## Safety Note

RoadBuddy is designed for passenger use or hands-free voice interaction. Please drive safely and follow local laws regarding device usage while driving.

## Tech Stack

- **AI**: Claude claude-sonnet-4-20250514 (Anthropic)
- **Voice Input**: SpeechRecognition + Google Speech API
- **Voice Output**: Google TTS
- **UI**: Streamlit

## License

MIT
