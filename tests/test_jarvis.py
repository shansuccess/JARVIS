import pytest
import asyncio
from backend.tools.system_tools import get_system_telemetry, adjust_volume
from backend.tools.utility_tools import get_current_datetime, add_note, list_notes, add_reminder, list_reminders
from backend.tools.web_tools import get_wikipedia_summary
from backend.jarvis_brain import JarvisBrain

def test_system_telemetry():
    telemetry = get_system_telemetry()
    assert telemetry["status"] == "success"
    assert "cpu" in telemetry
    assert "memory" in telemetry
    assert "disk" in telemetry
    assert "battery" in telemetry
    assert telemetry["cpu"]["cores"] > 0
    assert telemetry["memory"]["total_gb"] > 0

def test_current_datetime():
    dt = get_current_datetime()
    assert dt["status"] == "success"
    assert "date" in dt
    assert "time" in dt

def test_notes_and_reminders():
    # Test Notes
    res_note = add_note("Mark VII Armor calibration test")
    assert res_note["status"] == "success"
    notes = list_notes()
    assert notes["status"] == "success"
    assert notes["count"] >= 1
    assert any("calibration" in n["content"] for n in notes["notes"])

    # Test Reminders
    res_rem = add_reminder("Upgrade repulsor capacitors", due_time="tomorrow")
    assert res_rem["status"] == "success"
    reminders = list_reminders()
    assert reminders["status"] == "success"
    assert reminders["count"] >= 1

def test_volume_tool():
    res = adjust_volume("mute")
    assert res["status"] == "success"

def test_wikipedia_tool():
    res = get_wikipedia_summary("Artificial intelligence")
    assert res["status"] in ["success", "not_found"]
    if res["status"] == "success":
        assert "Artificial intelligence" in res["title"]

def test_language_detection():
    from backend.tts_engine import detect_language
    assert detect_language("Hello Jarvis, how are you today?") == "en"
    assert detect_language("नमस्ते जार्विस, आप कैसे हैं?") == "hi"
    assert detect_language("kya haal hai bhai") == "hi"
    assert detect_language("kaise ho yaar batao") == "hi"
    assert detect_language("வணக்கம் ஜார்விஸ்") == "ta"
    assert detect_language("నమస్కారం జార్విస్") == "te"
    assert detect_language("নমস্কার জার্ভিস") == "bn"
    assert detect_language("Hola Jarvis, ¿cómo estás?") == "es"
    assert detect_language("Bonjour Jarvis, quel temps fait-il?") == "fr"
    assert detect_language("こんにちはジャーヴィス") == "ja"
    assert detect_language("Привет Джарвис") == "ru"
    assert detect_language("Merhaba Jarvis nasılsın?") == "tr"
    assert detect_language("Xin chào Jarvis") == "vi"

def test_neural_tts_generation():
    from backend.tts_engine import generate_speech_bytes
    # Generate speech for a short phrase in English and Tamil
    audio_en = asyncio.run(generate_speech_bytes("Systems online, sir.", lang="en"))
    assert isinstance(audio_en, bytes)
    assert len(audio_en) > 100

    audio_hi = asyncio.run(generate_speech_bytes("नमस्ते भाई, सब ठीक है।", lang="hi"))
    assert isinstance(audio_hi, bytes)
    assert len(audio_hi) > 100

def test_startup_greeting():
    brain = JarvisBrain()
    greet = brain.get_startup_greeting()
    assert "response" in greet
    assert "J.A.R.V.I.S." in greet["response"]
    assert any(w in greet["response"].lower() for w in ["good morning", "good afternoon", "good evening", "night owl"])

def test_jarvis_brain_offline_processing():
    brain = JarvisBrain()
    
    # Test offline engine directly
    off_reply = brain._process_offline("Jarvis, what is my system status?")
    assert "status" in off_reply["response"].lower() or "system" in off_reply["response"].lower() or "cpu" in off_reply["response"].lower()

    off_vol = brain._process_offline("Jarvis, turn volume down")
    assert "volume" in off_vol["response"].lower()

    off_greet = brain._process_offline("Hello Jarvis", persona="indian_boy")
    assert "jarvis" in off_greet["response"].lower() or "energy" in off_greet["response"].lower()

    off_hi = brain._process_offline("नमस्ते जार्विस", persona="indian_boy")
    assert "जार्विस" in off_hi["response"] or "भाई" in off_hi["response"]
    assert off_hi["lang"] == "hi"

    # Test full processing
    reply = asyncio.run(brain.process_message("Jarvis, what is my system status?"))
    assert "system" in reply["response"].lower() or "status" in reply["response"].lower() or "cpu" in reply["response"].lower() or "power" in reply["response"].lower()
    assert "lang" in reply

def test_voice_personas():
    from backend.tts_engine import get_voice_for_language, clean_spoken_text, generate_speech_bytes

    # Clean spoken text test
    dirty = "**Hello!** Check out https://google.com #awesome 😀 `code` and *bullet*"
    cleaned = clean_spoken_text(dirty)
    assert "**" not in cleaned
    assert "https://" not in cleaned
    assert "#" not in cleaned
    assert "😀" not in cleaned
    assert "code" in cleaned

    # Test voice and pitch selection for personas
    voice_boy, rate_boy, pitch_boy = get_voice_for_language("hi", persona="indian_boy")
    assert "Madhur" in voice_boy or "Prabhat" in voice_boy
    assert rate_boy == "+10%"
    assert pitch_boy == "+6Hz"

    voice_girl, rate_girl, pitch_girl = get_voice_for_language("hi", persona="indian_girl")
    assert "Swara" in voice_girl or "Neerja" in voice_girl
    assert rate_girl == "+8%"
    assert pitch_girl == "+10Hz"

    # Test audio generation for Indian boy and Indian girl
    audio_boy = asyncio.run(generate_speech_bytes("Arre bhai kya haal chaal!", lang="hi", persona="indian_boy"))
    assert isinstance(audio_boy, bytes) and len(audio_boy) > 100

    audio_girl = asyncio.run(generate_speech_bytes("Hey! Sab badhiya hai!", lang="hi", persona="indian_girl"))
    assert isinstance(audio_girl, bytes) and len(audio_girl) > 100

def test_startup_greeting_personas():
    brain = JarvisBrain()
    greet_boy = brain.get_startup_greeting(persona="indian_boy")
    assert "Arre bhai!" in greet_boy["response"]
    assert "J.A.R.V.I.S." in greet_boy["response"]

    greet_girl = brain.get_startup_greeting(persona="indian_girl")
    assert "Hey! Main J.A.R.V.I.S. hoon!" in greet_girl["response"]

    greet_classic = brain.get_startup_greeting(persona="jarvis_classic")
    assert "Hey! It's me, J.A.R.V.I.S.!" in greet_classic["response"]

def test_fastapi_endpoints():
    from fastapi.testclient import TestClient
    from backend.app import app

    with TestClient(app, raise_server_exceptions=True) as client:
        # Status endpoint
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "J.A.R.V.I.S."
        assert "gemini_online" in data
        assert "voice_persona" in data

        # Telemetry endpoint
        resp_tel = client.get("/api/telemetry")
        assert resp_tel.status_code == 200
        assert resp_tel.json()["status"] == "success"

        # Update settings endpoint
        resp_set = client.post("/api/settings", json={"voice_persona": "indian_girl"})
        assert resp_set.status_code == 200
        assert resp_set.json()["voice_persona"] == "indian_girl"

        # Command endpoint with latency measurement and persona
        resp_cmd = client.post("/api/command", json={"message": "system status", "persona": "indian_girl"})
        assert resp_cmd.status_code == 200
        cmd_data = resp_cmd.json()
        assert "response" in cmd_data
        assert "audio_url" in cmd_data
        assert "persona=indian_girl" in cmd_data["audio_url"]
        assert "latency_ms" in cmd_data
        assert isinstance(cmd_data["latency_ms"], int)

        # TTS endpoint with persona
        resp_tts = client.get("/api/tts?text=All+systems+operational&lang=en&persona=indian_boy")
        assert resp_tts.status_code == 200
        assert resp_tts.headers["content-type"] == "audio/mpeg"
        assert len(resp_tts.content) > 100


