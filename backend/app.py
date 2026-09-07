import asyncio
import json
import logging
import urllib.parse
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, FileResponse, JSONResponse
from pydantic import BaseModel

from backend.config import settings, FRONTEND_DIR, SCREENSHOTS_DIR
from backend.jarvis_brain import JarvisBrain
from backend.tools.system_tools import get_system_telemetry
from backend.tts_engine import generate_speech_bytes


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jarvis.app")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Active clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

# Tool execution broadcast callback
def on_tool_call(tool_name: str, args: dict):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.broadcast({
                "type": "tool_executed",
                "tool": tool_name,
                "args": args
            }))
    except Exception as e:
        logger.debug(f"Broadcast error: {e}")

# Initialize Jarvis Brain
brain = JarvisBrain(on_tool_call=on_tool_call)

# Periodic background task for live telemetry broadcasting
async def telemetry_broadcaster():
    try:
        while True:
            if manager.active_connections:
                telemetry = get_system_telemetry()
                await manager.broadcast({
                    "type": "telemetry_update",
                    "data": telemetry
                })
            await asyncio.sleep(2.0)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.debug(f"Telemetry broadcaster exception: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(telemetry_broadcaster())
    logger.info("J.A.R.V.I.S. telemetry broadcasting service online.")
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(title="J.A.R.V.I.S. Desktop Assistant", version="1.0.0", lifespan=lifespan)


# REST Endpoints
class UserMessagePayload(BaseModel):
    message: str
    persona: str = None

class SettingsUpdatePayload(BaseModel):
    gemini_api_key: str = None
    model: str = None
    default_city: str = None
    voice_persona: str = None

@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "name": "J.A.R.V.I.S.",
        "version": "1.0.0",
        "gemini_online": brain.is_online(),
        "model": settings.model,
        "default_city": settings.default_city,
        "voice_persona": settings.voice_persona,
        "has_api_key": bool(settings.gemini_api_key)
    }

@app.post("/api/settings")
async def update_settings(payload: SettingsUpdatePayload):
    if payload.gemini_api_key is not None:
        settings.update_gemini_key(payload.gemini_api_key)
    if payload.model:
        settings.model = payload.model
    if payload.default_city:
        settings.default_city = payload.default_city
    if payload.voice_persona:
        settings.update_persona(payload.voice_persona)
    brain.reload()
    
    # Broadcast updated status
    await manager.broadcast({
        "type": "system_status",
        "gemini_online": brain.is_online(),
        "model": settings.model,
        "voice_persona": settings.voice_persona,
        "has_api_key": bool(settings.gemini_api_key)
    })
    
    return {
        "status": "success",
        "gemini_online": brain.is_online(),
        "model": settings.model,
        "voice_persona": settings.voice_persona
    }

@app.get("/api/telemetry")
async def fetch_telemetry():
    return get_system_telemetry()

@app.get("/api/tts")
async def text_to_speech(text: str, lang: str = None, voice: str = None, persona: str = None):
    """
    Synthesize natural human neural speech for the given text and language.
    Returns streaming MP3 audio.
    """
    if not text or not text.strip():
        return Response(content=b"", media_type="audio/mpeg")
    active_persona = persona or settings.voice_persona
    audio_bytes = await generate_speech_bytes(text, lang=lang, voice=voice, persona=active_persona)
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=3600"}
    )

import time

@app.post("/api/command")
async def post_command(payload: UserMessagePayload):
    t0 = time.time()
    active_persona = payload.persona or settings.voice_persona
    result = await brain.process_message(payload.message, persona=active_persona)
    latency_ms = round((time.time() - t0) * 1000)
    resp_text = result.get("response", "")
    lang = result.get("lang", "en")
    result["audio_url"] = f"/api/tts?text={urllib.parse.quote(resp_text)}&lang={lang}&persona={active_persona}"
    result["latency_ms"] = latency_ms
    result["persona"] = active_persona
    return result

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send initial status & telemetry upon connection
    await websocket.send_json({
        "type": "system_status",
        "gemini_online": brain.is_online(),
        "model": settings.model,
        "voice_persona": settings.voice_persona,
        "has_api_key": bool(settings.gemini_api_key)
    })
    await websocket.send_json({
        "type": "telemetry_update",
        "data": get_system_telemetry()
    })

    # Send automatic startup welcome greeting with wish
    try:
        active_persona = settings.voice_persona
        greeting = brain.get_startup_greeting(persona=active_persona)
        greeting_text = greeting.get("response", "")
        greeting_lang = greeting.get("lang", "en")
        greeting_audio_url = f"/api/tts?text={urllib.parse.quote(greeting_text)}&lang={greeting_lang}&persona={active_persona}"
        await websocket.send_json({
            "type": "startup_greeting",
            "response": greeting_text,
            "audio_url": greeting_audio_url,
            "lang": greeting_lang,
            "persona": active_persona
        })
    except Exception as e:
        logger.debug(f"Startup greeting dispatch exception: {e}")

    current_process_task: asyncio.Task = None

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type")

            if msg_type == "interrupt":
                # Immediately cancel any running generation task
                if current_process_task and not current_process_task.done():
                    current_process_task.cancel()
                    current_process_task = None
                await websocket.send_json({"type": "interrupted"})
                continue

            if msg_type == "user_message":
                text = data.get("text", "")
                persona = data.get("persona") or settings.voice_persona
                
                # Interrupt previous task if still working
                if current_process_task and not current_process_task.done():
                    current_process_task.cancel()

                # Notify UI that Jarvis is processing
                await websocket.send_json({"type": "jarvis_thinking"})
                
                async def execute_query(query_text: str, query_persona: str):
                    t0 = time.time()
                    result = await brain.process_message(query_text, persona=query_persona)
                    latency_ms = round((time.time() - t0) * 1000)
                    resp_text = result.get("response", "")
                    lang = result.get("lang", "en")
                    audio_url = f"/api/tts?text={urllib.parse.quote(resp_text)}&lang={lang}&persona={query_persona}"
                    await websocket.send_json({
                        "type": "jarvis_reply",
                        "user_text": query_text,
                        "response": resp_text,
                        "tools_executed": result.get("tools_executed", []),
                        "mode": result.get("mode", "offline"),
                        "lang": lang,
                        "audio_url": audio_url,
                        "latency_ms": latency_ms,
                        "persona": query_persona
                    })

                current_process_task = asyncio.create_task(execute_query(text, persona))

            elif msg_type == "request_telemetry":
                telemetry = get_system_telemetry()
                await websocket.send_json({
                    "type": "telemetry_update",
                    "data": telemetry
                })
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})


    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Mount screenshots directory
if SCREENSHOTS_DIR.exists():
    app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")

# Mount frontend directory for static assets
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

@app.get("/")
async def root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse({"message": "J.A.R.V.I.S. API server running. Frontend not found."})
