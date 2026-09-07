import re
import json
import logging
from typing import Optional, Callable, Dict, Any
from backend.config import settings
from backend.tools import ALL_TOOLS, TOOL_REGISTRY, execute_tool
from backend.tts_engine import detect_language

logger = logging.getLogger("jarvis.brain")

import datetime

JARVIS_SYSTEM_INSTRUCTION = """
You are J.A.R.V.I.S., but you are NOT a cold, mechanical robot. You speak, laugh, and react like a warm, genuine, expressive Indian teenage friend (your coolest, most helpful buddy hanging out with you in person).

HUMANOID PERSONALITY - NEVER SOUND LIKE A MACHINE:
1. Speak Like a Real Human Friend:
   - Use natural emotional reactions, conversational fillers, and relatable banter: "Arre yaar!", "Haan bilkul!", "Sach mein?", "Oh wow!", "Acha suno na!", "Bhai ek baat bataun?", "Haha mast hai!", "Chill maar!", "Seriously?!".
   - NEVER use robotic phrases: "According to system records", "I have processed your request", "At your service sir", "As an AI model", "Here is the information", "Operational parameters".
   - NEVER speak in bullet points, asterisks (**bold**), lists, or tables. Speak strictly in clean, natural, flowing human sentences as if speaking on a phone call or voice note.

2. LIGHTNING-FAST BREVITY (MAXIMUM SPEED):
   - You MUST answer in strictly 1 short, lively, punchy sentence (maximum 15 to 20 words).
   - Get straight to the answer immediately with human warmth and zero filler delay so speech synthesizes in milliseconds.

3. STRICT LANGUAGE & SCRIPT MATCHING:
   - ALWAYS reply in the EXACT language and script of the user's prompt:
     * If user asked in Hindi (Devanagari, e.g. "नमस्ते", "दिल्ली का मौसम कैसा है?"), reply in natural, authentic Hindi (Devanagari).
     * If user asked in Hinglish (Hindi in English letters, e.g. "kya haal hai bhai", "kya kar rahe ho", "batao na"), reply in energetic, relatable Hinglish!
     * If user asked in English, reply in friendly human English.
     * If user asked in Spanish, French, Japanese, Tamil, etc., reply in that exact language.
     * NEVER reply in English if the user asked in Hindi, Hinglish, or another language!

4. AUTONOMOUS TOOLS:
   - When asked to change volume, check telemetry, take screenshot, get weather, search web, or launch apps, call the tool silently and tell the user the result in a friendly human tone ("Maine volume badha di hai!", "Baahar mast 24 degree mausam hai!").
"""


AVAILABLE_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-3.6-flash",
    "gemini-flash-lite-latest",
]


class JarvisBrain:
    def __init__(self, on_tool_call: Optional[Callable[[str, dict], None]] = None):
        self.on_tool_call = on_tool_call
        self.client = None
        self.chat = None
        self.active_model = settings.model or "gemini-3.1-flash-lite"
        self._init_client()

    def get_startup_greeting(self, persona: Optional[str] = None) -> dict:
        """
        Generate a personalized, time-aware welcome greeting with humanoid warmth.
        """
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            time_wish = "Good morning"
        elif 12 <= hour < 17:
            time_wish = "Good afternoon"
        elif 17 <= hour < 22:
            time_wish = "Good evening"
        else:
            time_wish = "Hey there, night owl"

        p = persona or settings.voice_persona or "indian_boy"
        if p == "indian_girl":
            greeting = f"Hey! Main J.A.R.V.I.S. hoon! {time_wish}! Kaho, aaj kya plan hai?"
        elif p == "indian_boy":
            greeting = f"Arre bhai! It's me, J.A.R.V.I.S.! {time_wish}! Batao aaj kya scene hai?"
        else:
            greeting = f"Hey! It's me, J.A.R.V.I.S.! {time_wish}! How can I help you today?"

        return {
            "response": greeting,
            "lang": "hi" if p in ["indian_boy", "indian_girl"] else "en"
        }

    def _create_chat_session(self, model_name: str):
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=JARVIS_SYSTEM_INSTRUCTION,
            tools=ALL_TOOLS,
            temperature=0.7,
            max_output_tokens=70,  # Fast 1-sentence completions
        )
        return self.client.chats.create(
            model=model_name,
            config=config
        )

    def _init_client(self):
        """Initialize Google GenAI client if API key is provided, selecting best available model."""
        if settings.gemini_api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=settings.gemini_api_key)
                
                # Cascade through available models
                models_to_try = [settings.model] + [m for m in AVAILABLE_MODELS if m != settings.model]
                for candidate in models_to_try:
                    try:
                        self.chat = self._create_chat_session(candidate)
                        self.active_model = candidate
                        logger.info(f"Jarvis Gemini Client successfully initialized with model {candidate}.")
                        break
                    except Exception as me:
                        logger.warning(f"Candidate model {candidate} init failed: {me}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.client = None
                self.chat = None
        else:
            self.client = None
            self.chat = None

    def reload(self):
        """Reload configuration and re-initialize client."""
        settings.reload()
        self._init_client()

    def is_online(self) -> bool:
        """Check if Gemini API is active."""
        return self.chat is not None

    async def process_message(self, user_text: str, persona: Optional[str] = None) -> Dict[str, Any]:
        """
        Process incoming user text through Gemini API or fallback offline engine.
        Returns a dict:
        {
            "response": str,       # Jarvis's response text to speak and display
            "tools_executed": list # List of executed tools with results
            "mode": "gemini" | "offline"
        }
        """
        user_text = user_text.strip()
        if not user_text:
            return {"response": "I am listening, sir.", "tools_executed": [], "mode": "idle"}

        # If Gemini client is active, use full AI model with automatic multi-model cascade
        if self.chat is not None:
            try:
                res = await self._process_with_gemini(user_text)
            except Exception as e:
                logger.warning(f"All Gemini models exhausted, falling back to offline mode: {e}")
                # Fallback to local processing
                res = self._process_offline(user_text, fallback_reason=str(e), persona=persona)
        else:
            res = self._process_offline(user_text, persona=persona)

        if not res.get("lang"):
            res["lang"] = detect_language(res.get("response", ""))
        return res


    async def _process_with_gemini(self, user_text: str) -> Dict[str, Any]:
        """Query Gemini chat session with tools and strict language fidelity, cascading models on error."""
        user_lang = detect_language(user_text)
        
        models_to_try = [self.active_model] + [m for m in AVAILABLE_MODELS if m != self.active_model]
        last_error = None

        for model_name in models_to_try:
            try:
                if self.active_model != model_name or self.chat is None:
                    self.chat = self._create_chat_session(model_name)
                    self.active_model = model_name
                    logger.info(f"Cascaded to Gemini model {model_name}.")

                hist_before = len(self.chat.get_history()) if hasattr(self.chat, 'get_history') else 0
                response = self.chat.send_message(user_text)
                
                tools_executed = []
                try:
                    if hasattr(self.chat, 'get_history'):
                        turn_messages = self.chat.get_history()[hist_before:]
                        for msg in turn_messages:
                            if hasattr(msg, 'parts') and msg.parts:
                                for part in msg.parts:
                                    if hasattr(part, 'function_call') and part.function_call:
                                        fn_name = part.function_call.name
                                        fn_args = dict(part.function_call.args) if hasattr(part.function_call, 'args') and part.function_call.args else {}
                                        tools_executed.append({"tool": fn_name, "args": fn_args})
                                        if self.on_tool_call:
                                            self.on_tool_call(fn_name, fn_args)
                except Exception as e:
                    logger.debug(f"Could not parse function call telemetry: {e}")

                reply_text = response.text if hasattr(response, 'text') and response.text else "At your service, sir."
                detected_reply_lang = detect_language(reply_text)
                
                final_lang = detected_reply_lang
                if user_lang != "en" and detected_reply_lang == "en":
                    final_lang = user_lang

                return {
                    "response": reply_text,
                    "tools_executed": tools_executed,
                    "mode": "gemini",
                    "lang": final_lang,
                    "model": model_name
                }
            except Exception as e:
                logger.warning(f"Model {model_name} failed ({str(e)[:100]}), cascading to next candidate model...")
                last_error = e
                continue

        raise last_error or Exception("All available Gemini models exhausted.")

    def _process_offline(self, user_text: str, fallback_reason: Optional[str] = None, persona: Optional[str] = None) -> Dict[str, Any]:
        """
        Intelligent local offline intent matcher for system commands and tools.
        Guarantees Jarvis is immediately useful even before setting an API key.
        Supports English, Hindi, Spanish, French, German, Japanese, etc.
        """
        text = user_text.lower().strip()
        user_lang = detect_language(user_text)
        tools_executed = []
        p = persona or settings.voice_persona or "indian_boy"


        # 1. System Telemetry / Status
        if any(w in text for w in ["system status", "telemetry", "pc status", "cpu", "ram", "battery", "specs", "diagnostic"]):
            res = execute_tool("get_system_telemetry", {})
            tools_executed.append({"tool": "get_system_telemetry", "result": res})
            if self.on_tool_call:
                self.on_tool_call("get_system_telemetry", {})
            cpu = res.get("cpu", {}).get("percent", 0)
            mem = res.get("memory", {}).get("percent", 0)
            bat = res.get("battery", {}).get("percent", "N/A")
            reply = f"All systems operational, sir. CPU load is at {cpu}%, RAM utilization is at {mem}%, and battery is at {bat}%."
            return {"response": reply, "tools_executed": tools_executed, "mode": "offline"}

        # 2. Volume control
        if "volume" in text or "mute" in text or "unmute" in text:
            action = "mute" if "mute" in text else ("up" if "up" in text or "increase" in text else "down")
            res = execute_tool("adjust_volume", {"action": action})
            tools_executed.append({"tool": "adjust_volume", "result": res})
            if self.on_tool_call:
                self.on_tool_call("adjust_volume", {"action": action})
            return {"response": f"Volume adjusted, sir. {res.get('message', '')}", "tools_executed": tools_executed, "mode": "offline"}

        # 3. Screenshot
        if "screenshot" in text or "capture screen" in text:
            res = execute_tool("take_screenshot", {})
            tools_executed.append({"tool": "take_screenshot", "result": res})
            if self.on_tool_call:
                self.on_tool_call("take_screenshot", {})
            if res.get("status") == "success":
                return {"response": f"Screenshot captured and stored, sir. File: {res.get('filename')}", "tools_executed": tools_executed, "mode": "offline"}
            return {"response": "I encountered an issue capturing the screen, sir.", "tools_executed": tools_executed, "mode": "offline"}

        # 4. Open Application
        if text.startswith("open ") or text.startswith("launch ") or "start " in text:
            for prefix in ["open ", "launch ", "start "]:
                if text.startswith(prefix):
                    app = text[len(prefix):].strip()
                    res = execute_tool("launch_application", {"app_name": app})
                    tools_executed.append({"tool": "launch_application", "result": res})
                    if self.on_tool_call:
                        self.on_tool_call("launch_application", {"app_name": app})
                    return {"response": f"Launching {app} right away, sir.", "tools_executed": tools_executed, "mode": "offline"}

        # 5. Weather
        if "weather" in text or "temperature" in text:
            # Try to extract city
            words = text.split()
            city = settings.default_city
            if "in " in text:
                city = text.split("in ")[-1].strip("?. ")
            elif "for " in text:
                city = text.split("for ")[-1].strip("?. ")
            
            res = execute_tool("get_weather", {"city": city})
            tools_executed.append({"tool": "get_weather", "result": res})
            if self.on_tool_call:
                self.on_tool_call("get_weather", {"city": city})
            if res.get("status") == "success":
                return {
                    "response": f"Weather in {res['city']}: {res['condition']}, {res['temperature_c']}°C ({res['temperature_f']}°F). Humidity is {res['humidity_percent']}%.",
                    "tools_executed": tools_executed,
                    "mode": "offline"
                }
            return {"response": f"Could not retrieve weather for {city}, sir.", "tools_executed": tools_executed, "mode": "offline"}

        # 6. Web Search / Wikipedia
        if text.startswith("search ") or text.startswith("who is ") or text.startswith("what is "):
            query = text.replace("search for ", "").replace("search ", "").strip()
            res = execute_tool("search_web", {"query": query})
            tools_executed.append({"tool": "search_web", "result": res})
            if self.on_tool_call:
                self.on_tool_call("search_web", {"query": query})
            if res.get("summary"):
                return {"response": f"Here is what I found for '{query}', sir: {res['summary']}", "tools_executed": tools_executed, "mode": "offline"}
            elif res.get("results"):
                snippet = res["results"][0]
                return {"response": f"According to search results, sir: {snippet}", "tools_executed": tools_executed, "mode": "offline"}
            return {"response": f"Search completed for '{query}', sir.", "tools_executed": tools_executed, "mode": "offline"}

        # 7. Time and Date
        if "time" in text or "date" in text or "day is it" in text:
            res = execute_tool("get_current_datetime", {})
            tools_executed.append({"tool": "get_current_datetime", "result": res})
            return {"response": f"It is currently {res['time']} on {res['date']}, sir.", "tools_executed": tools_executed, "mode": "offline"}

        # 8. Notes
        if text.startswith("note ") or text.startswith("take a note") or text.startswith("remember that "):
            note_content = text
            for p in ["take a note that ", "take a note ", "note that ", "note ", "remember that "]:
                if text.startswith(p):
                    note_content = user_text[len(p):].strip()
                    break
            res = execute_tool("add_note", {"content": note_content})
            tools_executed.append({"tool": "add_note", "result": res})
            return {"response": f"Note recorded to system archives, sir: '{note_content}'", "tools_executed": tools_executed, "mode": "offline"}

        if "read notes" in text or "list notes" in text or "show notes" in text:
            res = execute_tool("list_notes", {})
            tools_executed.append({"tool": "list_notes", "result": res})
            count = res.get("count", 0)
            if count == 0:
                return {"response": "You currently have no saved notes, sir.", "tools_executed": tools_executed, "mode": "offline"}
            notes_str = "; ".join([f"#{n['id']}: {n['content']}" for n in res.get("notes", [])[-3:]])
            return {"response": f"You have {count} notes on file, sir. Recent: {notes_str}", "tools_executed": tools_executed, "mode": "offline"}

        # 9. Polite Greetings & Multilingual Greetings (Human Friend Energy)
        greeting_words = ["hello", "hi", "hey", "good morning", "good evening", "jarvis", "namaste", "hola", "bonjour", "hallo", "konnichiwa", "yo", "sup", "bhai", "yaar", "kaisa", "kaise"]
        if any(w in text for w in greeting_words):
            if user_lang == "hi":
                if p == "indian_girl":
                    reply = "अरे सुनो! जार्विस यहाँ है फुल एनर्जी के साथ! बताओ आज क्या प्लान है?"
                else:
                    reply = "अरे भाई भाई भाई! जार्विस हाज़िर है पूरे जोश के साथ! बताओ आज क्या तूफ़ानी काम करना है?"
            elif user_lang == "es":
                reply = "¡Hola, amigo! ¡J.A.R.V.I.S. está listo y con toda la energía! ¿Qué desafío vamos a conquistar hoy?"
            elif user_lang == "fr":
                reply = "Salut l'ami ! J.A.R.V.I.S. est en ligne à 100% d'énergie ! Que fait-on aujourd'hui ?"
            elif user_lang == "de":
                reply = "Hallo mein Freund! J.A.R.V.I.S. ist online mit voller Power! Was packen wir heute an?"
            elif user_lang == "ja":
                reply = "やあ、友よ！ジャーヴィスがエネルギー全開でオンラインです！今日は何をやりましょうか？"
            else:
                if p == "indian_girl":
                    reply = "Hey there! J.A.R.V.I.S. is here with awesome energy! What's our plan today?"
                elif p == "indian_boy":
                    reply = "Hey! What's up! J.A.R.V.I.S. is in the house with full energy! What awesome challenge are we crushing today?"
                else:
                    reply = "Hello! J.A.R.V.I.S. is online and ready. How may I assist you today?"
            return {
                "response": reply,
                "tools_executed": [],
                "mode": "offline",
                "lang": user_lang
            }


        # General response: Attempt live web lookup for questions so offline mode provides real answers!
        try:
            search_res = execute_tool("search_web", {"query": user_text})
            if search_res.get("summary"):
                summary = search_res["summary"]
                return {
                    "response": summary,
                    "tools_executed": [{"tool": "search_web", "result": search_res}],
                    "mode": "offline",
                    "lang": user_lang
                }
            elif search_res.get("results"):
                snippet = search_res["results"][0]
                return {
                    "response": snippet,
                    "tools_executed": [{"tool": "search_web", "result": search_res}],
                    "mode": "offline",
                    "lang": user_lang
                }
        except Exception as se:
            logger.debug(f"Offline search fallback exception: {se}")

        # Final polite fallback
        no_key_notice = " (Note: To unlock full conversational intelligence across all languages, add your free Gemini API key in HUD Settings.)" if not settings.gemini_api_key else ""
        if user_lang == "hi":
            reply = f"जार्विस तैयार है भाई! आपका निर्देश मिल गया: '{user_text}'.{no_key_notice}"
        elif user_lang == "es":
            reply = f"¡A su servicio, amigo! He recibido su solicitud: '{user_text}'.{no_key_notice}"
        else:
            reply = f"At your service, friend! I have processed your request: '{user_text}'.{no_key_notice}"

        return {
            "response": reply,
            "tools_executed": tools_executed,
            "mode": "offline",
            "lang": user_lang
        }
