# J.A.R.V.I.S. (Just A Rather Very Intelligent System)
### Stark Industries Mark VII — Advanced AI Desktop Assistant

An intelligent desktop assistant inspired by Tony Stark's iconic J.A.R.V.I.S., engineered with a **holographic Arc Reactor HUD**, bidirectional voice interaction, **Google Gemini** multimodal intelligence, and real Windows system automation.

---

## Key Features

- **Hyper-Realistic Human Voice (Microsoft Neural Speech)**:
  - Powered by Azure Neural Voice models via `edge-tts` (zero external API keys or subscriptions required).
  - Authentic British gentleman persona voice (`en-GB-RyanNeural`) with human cadence, natural breathing, and inflections.
  - No robotic browser text-to-speech artifacts.
- **Universal Multilingual Listening & Speaking**:
  - Automatically listens and responds fluently in **any language** (English, Hindi, Spanish, French, German, Japanese, Chinese, Arabic, Russian, Portuguese, Italian, Korean, etc.).
  - Automatic language detection using script analysis and AI brain comprehension.
  - Native neural voice models mapped for each language (e.g. `hi-IN-MadhurNeural` for Hindi, `es-ES-AlvaroNeural` for Spanish, `fr-FR-HenriNeural` for French, `ja-JP-KeitaNeural` for Japanese).
  - Quick dialect switcher in the top HUD navigation bar.
- **Ultra-Fast Conversational Responses**:
  - Direct 1-2 sentence response structure tuned for rapid cognitive generation and instant speech turnaround.
  - Asynchronous audio streaming delivering human voice in ~200ms.
- **Holographic Sci-Fi HUD**:
  - Rotating multi-tier Arc Reactor rendered in real-time on HTML5 Canvas.
  - Interactive states: *STANDBY*, *LISTENING*, *ANALYZING*, and *SPEAKING*.
  - Live animated audio waveform visualizer responding dynamically to human speech playback.
  - Real-time CPU, RAM, Disk, and Battery circular gauges.
  - Protocol Diagnostics log streaming every system event, command, and tool execution.

- **Google Gemini Brain & Autonomous Tool Calling**:
  - Powered by the `google-genai` SDK supporting `gemini-2.5-flash`, `gemini-1.5-flash`, and `gemini-2.5-pro`.
  - Autonomous tool calling for system management, information retrieval, and desktop tasks.
  - Multi-turn conversational memory with Tony Stark's assistant persona.
  - **Graceful Offline Engine**: Works out-of-the-box even without an API key using built-in intent parsing.
- **Real Windows System Automation**:
  - **Telemetry**: Real-time CPU load, memory utilization, disk space, battery status, and uptime.
  - **App Launcher**: Open Chrome, Edge, Spotify, VS Code, Notepad, Calculator, Terminal, and more.
  - **Audio Controls**: Mute, unmute, volume up, and volume down via native Windows key events.
  - **Screenshot Capture**: Capture full-screen screenshots saved automatically to `screenshots/`.
  - **Live Weather**: Instant global weather forecasts via Open-Meteo API.
  - **Web Intelligence**: DuckDuckGo search summaries and Wikipedia lookups.
  - **Productivity**: Quick personal notes and reminder tracking.

---

## Quickstart Guide

### 1. Launch J.A.R.V.I.S.

Double-click `run_jarvis.bat` or run in your terminal:
```bash
python run_jarvis.py
```

This will start the local server and automatically open the holographic HUD in your default browser at `http://127.0.0.1:8000`.

### 2. Configure Your Gemini API Key (Optional but Recommended)

To enable Gemini's conversational intellect and autonomous reasoning:
1. Obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Either:
   - Click the **Settings Gear (⚙)** in the top-right corner of the HUD and paste your key.
   - Or paste it into the `.env` file:
     ```env
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

---

## Voice & Interaction Controls

| Action | Shortcut / Trigger |
|---|---|
| **Wake Word** | Say `"Jarvis, [your command]"` |
| **Push to Talk** | Press **[Spacebar]** or click the **Mic** button |
| **Transmit Command** | Type in the text bar and hit **[Enter]** or click **TRANSMIT** |
| **Quick Action Chips** | Click any chip (*System Status*, *Weather*, *Open Chrome*, *Screenshot*, etc.) |
| **Settings** | Click the **Gear (⚙)** icon in the top right |

---

## Example Directives

- *"Jarvis, give me a full system status report."*
- *"Jarvis, what is the weather in New York?"*
- *"Jarvis, open Chrome."*
- *"Jarvis, turn the volume down."*
- *"Jarvis, take a screenshot."*
- *"Jarvis, who was Nikola Tesla?"*
- *"Jarvis, search for the latest developments in quantum computing."*
- *"Jarvis, take a note that my meeting is at 3 PM tomorrow."*
- *"Jarvis, list my recent notes."*
- *"Jarvis, are you online?"*

---

## Project Architecture

```
jarvis/
├── backend/
│   ├── app.py                # FastAPI server & WebSocket broadcaster
│   ├── config.py             # Environment & settings configuration
│   ├── jarvis_brain.py       # Gemini API client & offline intent engine
│   └── tools/
│       ├── __init__.py       # Tool registry & dispatcher
│       ├── system_tools.py   # Windows telemetry, volume, screenshot
│       ├── app_tools.py      # Desktop application launcher
│       ├── web_tools.py      # DuckDuckGo, Wikipedia, Open-Meteo
│       └── utility_tools.py  # Notes, reminders, datetime
├── frontend/
│   ├── index.html            # Stark HUD layout & SVG gauges
│   ├── styles.css            # Sci-fi cyberpunk holographic design
│   └── js/
│       ├── app.js            # HUD orchestrator & WebSocket client
│       ├── reactor.js        # Canvas Arc Reactor animation engine
│       └── voice.js          # Speech recognition & British TTS synthesis
├── screenshots/              # Stored screenshot captures
├── data/                     # Local notes and reminders
├── tests/
│   └── test_jarvis.py        # Automated test suite
├── run_jarvis.py             # Python launcher script
├── run_jarvis.bat            # 1-click Windows batch launcher
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation
```

---

## Running Tests

To run the automated test suite:
```bash
python -m pytest tests/test_jarvis.py -v
```
