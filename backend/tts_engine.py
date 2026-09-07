import re
import logging
import asyncio
from typing import Optional, Dict
import edge_tts

logger = logging.getLogger("jarvis.tts")

# Mapping of language codes to human-like Azure Neural voices (Male & Female)
MALE_VOICES: Dict[str, str] = {
    # English & Accents
    "en": "en-IN-PrabhatNeural",       # Indian English male (youthful & warm)
    "en-us": "en-US-ChristopherNeural",# American male
    "en-gb": "en-GB-RyanNeural",       # British gentleman (Jarvis UK)
    "en-in": "en-IN-PrabhatNeural",    # Indian English male

    # Indian Regional Languages
    "hi": "hi-IN-MadhurNeural",        # Hindi male (natural, friendly)
    "ta": "ta-IN-ValluvarNeural",      # Tamil male
    "te": "te-IN-MohanNeural",         # Telugu male
    "bn": "bn-IN-BashkarNeural",       # Bengali male
    "mr": "mr-IN-ManoharNeural",       # Marathi male
    "gu": "gu-IN-NiranjanNeural",      # Gujarati male
    "kn": "kn-IN-GaganNeural",         # Kannada male
    "ml": "ml-IN-MidhunNeural",        # Malayalam male
    "ur": "ur-IN-SalmanNeural",        # Urdu male

    # Asian Languages
    "ja": "ja-JP-KeitaNeural",         # Japanese male
    "zh": "zh-CN-YunxiNeural",         # Mandarin Chinese male
    "ko": "ko-KR-InJoonNeural",        # Korean male
    "vi": "vi-VN-NamMinhNeural",       # Vietnamese male
    "th": "th-TH-NiwatNeural",         # Thai male
    "id": "id-ID-ArdiNeural",          # Indonesian male
    "fil": "fil-PH-AngeloNeural",      # Filipino male
    "tl": "fil-PH-AngeloNeural",
    "ms": "ms-MY-OsmanNeural",         # Malay male

    # Middle Eastern Languages
    "ar": "ar-SA-HamedNeural",         # Arabic male
    "fa": "fa-IR-FaridNeural",         # Persian male
    "he": "he-IL-AvriNeural",          # Hebrew male

    # European & Global Languages
    "es": "es-ES-AlvaroNeural",        # Spanish male
    "fr": "fr-FR-HenriNeural",         # French male
    "de": "de-DE-ConradNeural",        # German male
    "ru": "ru-RU-DmitryNeural",        # Russian male
    "it": "it-IT-DiegoNeural",         # Italian male
    "pt": "pt-BR-AntonioNeural",       # Portuguese male
    "nl": "nl-NL-MaartenNeural",       # Dutch male
    "pl": "pl-PL-MarekNeural",         # Polish male
    "uk": "uk-UA-OstapNeural",         # Ukrainian male
    "tr": "tr-TR-AhmetNeural",         # Turkish male
    "el": "el-GR-NestorasNeural",      # Greek male
    "sv": "sv-SE-MattiasNeural",       # Swedish male
    "da": "da-DK-JeppeNeural",         # Danish male
    "fi": "fi-FI-HarriNeural",         # Finnish male
    "nb": "nb-NO-FinnNeural",          # Norwegian male
    "no": "nb-NO-FinnNeural",
    "cs": "cs-CZ-AntoninNeural",       # Czech male
    "ro": "ro-RO-EmilNeural",          # Romanian male
    "hu": "hu-HU-TamasNeural",         # Hungarian male
}

FEMALE_VOICES: Dict[str, str] = {
    # English & Accents
    "en": "en-IN-NeerjaNeural",        # Indian English female (expressive & lively)
    "en-us": "en-US-JennyNeural",      # American female
    "en-gb": "en-GB-SoniaNeural",      # British female
    "en-in": "en-IN-NeerjaNeural",     # Indian English female

    # Indian Regional Languages
    "hi": "hi-IN-SwaraNeural",         # Hindi female (sweet, expressive, humanoid)
    "ta": "ta-IN-PallaviNeural",       # Tamil female
    "te": "te-IN-ShrutiNeural",        # Telugu female
    "bn": "bn-IN-TanishaaNeural",      # Bengali female
    "mr": "mr-IN-AarohiNeural",        # Marathi female
    "gu": "gu-IN-DhwaniNeural",        # Gujarati female
    "kn": "kn-IN-SapnaNeural",         # Kannada female
    "ml": "ml-IN-SobhanaNeural",       # Malayalam female
    "ur": "ur-IN-GulNeural",           # Urdu female

    # Asian Languages
    "ja": "ja-JP-NanamiNeural",        # Japanese female
    "zh": "zh-CN-XiaoxiaoNeural",      # Chinese female
    "ko": "ko-KR-SunHiNeural",         # Korean female
    "vi": "vi-VN-HoaiMyNeural",        # Vietnamese female
    "th": "th-TH-PremwadeeNeural",     # Thai female
    "id": "id-ID-GadisNeural",         # Indonesian female
    "fil": "fil-PH-BlessicaNeural",    # Filipino female
    "tl": "fil-PH-BlessicaNeural",
    "ms": "ms-MY-YasminNeural",        # Malay female

    # Middle Eastern Languages
    "ar": "ar-SA-ZariyahNeural",       # Arabic female
    "fa": "fa-IR-DilaraNeural",        # Persian female
    "he": "he-IL-HilaNeural",          # Hebrew female

    # European & Global Languages
    "es": "es-ES-ElviraNeural",        # Spanish female
    "fr": "fr-FR-DeniseNeural",        # French female
    "de": "de-DE-KatjaNeural",         # German female
    "ru": "ru-RU-SvetlanaNeural",      # Russian female
    "it": "it-IT-ElsaNeural",          # Italian female
    "pt": "pt-BR-FranciscaNeural",     # Portuguese female
    "nl": "nl-NL-FennaNeural",         # Dutch female
    "pl": "pl-PL-ZofiaNeural",         # Polish female
    "uk": "uk-UA-PolinaNeural",        # Ukrainian female
    "tr": "tr-TR-EmelNeural",          # Turkish female
    "el": "el-GR-AthinaNeural",        # Greek female
    "sv": "sv-SE-SofieNeural",         # Swedish female
    "da": "da-DK-ChristelNeural",      # Danish female
    "fi": "fi-FI-NooraNeural",         # Finnish female
    "nb": "nb-NO-PernilleNeural",      # Norwegian female
    "no": "nb-NO-PernilleNeural",
    "cs": "cs-CZ-VlastaNeural",        # Czech female
    "ro": "ro-RO-AlinaNeural",         # Romanian female
    "hu": "hu-HU-NoemiNeural",         # Hungarian female
}

# Legacy alias for backward compatibility
NEURAL_VOICES = MALE_VOICES

VOICE_PERSONAS = {
    "indian_boy": {
        "gender": "male",
        "pitch": "+6Hz",
        "rate": "+10%",
        "name": "Teen Indian Boy (Lively & Friendly)"
    },
    "indian_girl": {
        "gender": "female",
        "pitch": "+10Hz",
        "rate": "+8%",
        "name": "Teen Indian Girl (Sweet & Vibrant)"
    },
    "jarvis_classic": {
        "gender": "male",
        "pitch": "-2Hz",
        "rate": "+4%",
        "name": "Classic Jarvis (British Gentleman)"
    }
}

DEFAULT_VOICE = "en-IN-PrabhatNeural"

def detect_language(text: str) -> str:
    """
    Fast, comprehensive language detector supporting 30+ languages and scripts.
    """
    if not text:
        return "en"

    # 1. Indian & South Asian Scripts
    # Tamil
    if re.search(r'[\u0B80-\u0BFF]', text):
        return "ta"
    # Telugu
    if re.search(r'[\u0C00-\u0C7F]', text):
        return "te"
    # Bengali / Assamese
    if re.search(r'[\u0980-\u09FF]', text):
        return "bn"
    # Gujarati
    if re.search(r'[\u0A80-\u0AFF]', text):
        return "gu"
    # Kannada
    if re.search(r'[\u0C80-\u0CFF]', text):
        return "kn"
    # Malayalam
    if re.search(r'[\u0D00-\u0D7F]', text):
        return "ml"
    # Devanagari (Hindi / Marathi)
    if re.search(r'[\u0900-\u097F]', text):
        marathi_cues = ["आहे", "नाही", "कसा", "काय", "तुम्ही", "नमस्कार"]
        if any(c in text for c in marathi_cues):
            return "mr"
        return "hi"

    # 2. East & Southeast Asian Scripts
    # Japanese (Hiragana & Katakana)
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text):
        return "ja"
    # Korean (Hangul)
    if re.search(r'[\uAC00-\uD7AF\u1100-\u11FF]', text):
        return "ko"
    # Thai
    if re.search(r'[\u0E00-\u0E7F]', text):
        return "th"
    # Chinese (Hanzi)
    if re.search(r'[\u4E00-\u9FFF]', text):
        return "zh"

    # 3. Middle Eastern Scripts
    # Hebrew
    if re.search(r'[\u0590-\u05FF]', text):
        return "he"
    # Arabic / Urdu / Persian
    if re.search(r'[\u0600-\u06FF\u0750-\u077F]', text):
        # Urdu cues
        if any(c in text for c in ["ہیں", "تھا", "آپ", "کیا", "کیسے"]):
            return "ur"
        # Persian cues
        if any(c in text for c in ["است", "من", "را", "برای"]):
            return "fa"
        return "ar"

    # 4. Cyrillic & Greek Scripts
    # Greek
    if re.search(r'[\u0370-\u03FF]', text):
        return "el"
    # Ukrainian specific letters
    if re.search(r'[ієїґІЄЇҐ]', text):
        return "uk"
    # General Cyrillic (Russian)
    if re.search(r'[\u0400-\u04FF]', text):
        return "ru"

    # 5. Latin Special Characters & Language-Specific Markers
    # Spanish inverted question/exclamation mark or ñ
    if re.search(r'[¿¡ñÑ]', text):
        return "es"
    # Vietnamese unique diacritics (excluding standard accents like á, é, ó used in Spanish)
    if re.search(r'[ăâđêôơưĂÂĐÊÔƠƯắằẳẵặấầẩẫậếềểễệốồổỗộớờởỡợứừửữựảẻỉỏủỷạẹịọụỵ]', text):
        return "vi"
    # Polish unique letters (excluding ó which is shared with Spanish/Portuguese)
    if re.search(r'[ąćęłśźżĄĆĘŁŚŹŻ]', text):
        return "pl"
    # Turkish unique letters (excluding ç, ö, ü which exist in French/German)
    if re.search(r'[ğİıĞşŞ]', text):
        return "tr"
    # Czech unique letters
    if re.search(r'[čďěřšťžůČĎĚŘŠŤŽŮ]', text):
        return "cs"
    # Hungarian unique letters
    if re.search(r'[őűŐŰ]', text):
        return "hu"


    # German unique letter ß
    if "ß" in text:
        return "de"

    # 6. Latin-based word vocabulary analysis with prioritized scoring
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if not words:
        return "en"

    # Priority 1: Hindi written in Latin script (Hinglish)
    hinglish_markers = {
        "kaise", "kaisa", "kaisi", "kya", "kyun", "kyu", "aap", "tum", "tu", "namaste", "shukriya",
        "theek", "hai", "hain", "kripya", "bhai", "yaar", "batao", "bata", "chal", "chalo", "raha",
        "rahi", "rahe", "kar", "karo", "karein", "karna", "sab", "badhiya", "kuch", "haan", "nahi",
        "sun", "suno", "mera", "meri", "mere", "tera", "teri", "tere", "apna", "apni", "dost",
        "haal", "chaal", "bolo", "bol", "accha", "acha", "sahi", "bataye", "batana", "dhanyawad",
        "dilli", "bharat", "karoonga", "karunga", "karungi", "desh"
    }
    if len(words.intersection(hinglish_markers)) >= 1:
        return "hi"

    # Priority 2: Distinct language vocabulary matching
    lang_vocab = {
        "es": {"hola", "gracias", "por", "favor", "buenos", "dias", "días", "tardes", "noches", "amigo", "cómo", "como", "está", "estás", "qué", "que", "para", "cuál", "cual", "dónde", "donde", "quién", "quien", "señor", "pero", "hacer", "todo", "bien"},
        "fr": {"bonjour", "merci", "salut", "s'il", "vous", "plaît", "plait", "comment", "pourquoi", "quand", "avec", "dans", "pour", "nous", "sont", "c'est", "très", "bien", "aujourd'hui"},
        "de": {"hallo", "danke", "bitte", "guten", "morgen", "tag", "abend", "wie", "warum", "nicht", "alles", "freund", "deutsch", "sehr", "heute"},
        "it": {"ciao", "grazie", "buongiorno", "prego", "come", "perché", "perche", "cosa", "tutto", "bene", "amico", "sono", "nostro", "anche"},
        "pt": {"olá", "ola", "obrigado", "obrigada", "você", "voce", "bom", "dia", "boa", "tarde", "noite", "amigo", "tudo", "como", "está"},
        "nl": {"goedemorgen", "alsjeblieft", "dankje", "dank", "waarom", "hoe", "nederlands", "welkom", "alles", "goed"},
        "tr": {"merhaba", "nasılsın", "nasilsin", "teşekkürler", "tesekkurler", "evet", "hayır", "hayir", "lütfen", "lutfen", "günaydın", "gunaydin"},
        "vi": {"xin", "chao", "chào", "cam", "cảm", "on", "ơn", "toi", "tôi", "ban", "bạn"},
        "id": {"halo", "selamat", "terima", "kasih", "bagaimana", "kabar", "apa", "siapa", "dimana"},
        "fil": {"kamusta", "salamat", "magandang", "umaga", "hapon", "gabi"},
        "pl": {"cześć", "czesc", "dzień", "dobry", "dziękuję", "dziekuje", "tak", "nie", "proszę", "prosze"},
        "sv": {"hej", "tack", "god", "morgon", "hur", "mår", "du", "varför"},
    }

    english_markers = {
        "the", "is", "are", "was", "were", "what", "which", "how", "why", "when", "who", "where",
        "you", "your", "my", "our", "this", "that", "these", "those", "have", "has", "had",
        "can", "could", "would", "should", "will", "just", "about", "with", "from", "for",
        "please", "thanks", "thank", "hello", "system", "status", "currently", "running",
        "operational", "percent", "percentage", "weather", "time", "date", "cpu", "load",
        "ram", "battery", "sure", "here", "all", "right", "good", "great"
    }

    # Count hits
    en_score = len(words.intersection(english_markers))
    best_lang = "en"
    best_score = en_score

    for lang_code, vocab in lang_vocab.items():
        score = len(words.intersection(vocab))
        if score > best_score:
            best_score = score
            best_lang = lang_code

    return best_lang



def clean_spoken_text(text: str) -> str:
    """Strip all markdown formatting, emojis, links, and code symbols for natural human speech."""
    if not text:
        return ""
    # Strip markdown bold, italics, headers, code, blockquotes
    cleaned = re.sub(r'[*_#`~\[\]<>]', ' ', text)
    # Strip URLs
    cleaned = re.sub(r'\(http[^\)]+\)', '', cleaned)
    cleaned = re.sub(r'http\S+', '', cleaned)
    # Remove emojis and unpronounceable symbols, preserving Latin, Devanagari, Arabic, Asian scripts, and basic punctuation
    cleaned = re.sub(r'[^\w\s.,!?:;\'"¿¡\u0600-\u06FF\u0900-\u0D7F\u3040-\u30FF\u4E00-\u9FFF-]', ' ', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()


def get_voice_for_language(lang: str, persona: Optional[str] = None) -> tuple[str, str, str]:
    """
    Return (voice_name, rate, pitch) based on language and humanoid persona.
    Personas: 'indian_boy', 'indian_girl', 'jarvis_classic'.
    """
    clean_lang = lang.lower().split("-")[0] if lang else "en"
    persona_key = persona or "indian_boy"
    cfg = VOICE_PERSONAS.get(persona_key, VOICE_PERSONAS["indian_boy"])
    gender = cfg.get("gender", "male")
    pitch = cfg.get("pitch", "+0Hz")
    rate = cfg.get("rate", "+0%")

    if persona_key == "jarvis_classic" and clean_lang in ["en", "en-us", "en-gb"]:
        return ("en-GB-RyanNeural", "+4%", "-2Hz")

    if gender == "female":
        voice = FEMALE_VOICES.get(clean_lang, FEMALE_VOICES.get(lang.lower(), "hi-IN-SwaraNeural" if clean_lang == "hi" else "en-IN-NeerjaNeural"))
    else:
        voice = MALE_VOICES.get(clean_lang, MALE_VOICES.get(lang.lower(), "hi-IN-MadhurNeural" if clean_lang == "hi" else "en-IN-PrabhatNeural"))

    return (voice, rate, pitch)


async def generate_speech_bytes(
    text: str,
    lang: Optional[str] = None,
    voice: Optional[str] = None,
    persona: Optional[str] = None
) -> bytes:
    """
    Synthesize high-fidelity humanoid voice audio using Edge TTS with persona pitch and rate.
    Returns MP3 audio bytes.
    """
    clean_text = clean_spoken_text(text)
    if not clean_text:
        return b""

    detected_lang = lang or detect_language(clean_text)
    target_voice, rate, pitch = get_voice_for_language(detected_lang, persona=persona)
    if voice:
        target_voice = voice

    try:
        communicate = edge_tts.Communicate(clean_text, target_voice, rate=rate, pitch=pitch)
        audio_buffer = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.extend(chunk["data"])
        return bytes(audio_buffer)
    except Exception as e:
        logger.error(f"Failed to generate neural speech with {target_voice}: {e}")
        # Fallback without custom pitch/rate
        try:
            communicate = edge_tts.Communicate(clean_text, target_voice)
            audio_buffer = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.extend(chunk["data"])
            return bytes(audio_buffer)
        except Exception as e2:
            logger.error(f"Fallback voice failed: {e2}")
        return b""
