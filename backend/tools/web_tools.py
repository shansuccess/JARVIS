import httpx
import urllib.parse

def search_web(query: str, max_results: int = 4) -> dict:
    """
    Search the web for up-to-date information, news, or answers using DuckDuckGo.
    """
    try:
        encoded_query = urllib.parse.quote(query)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Check DuckDuckGo Instant Answer API first
        api_url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_redirect=1&no_html=1"
        with httpx.Client(timeout=6.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(api_url)
            data = resp.json()
            
            abstract = data.get("AbstractText", "")
            heading = data.get("Heading", "")
            source = data.get("AbstractSource", "")
            url = data.get("AbstractURL", "")
            
            related = []
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if "Text" in topic:
                    related.append(topic["Text"])

            if abstract:
                return {
                    "status": "success",
                    "query": query,
                    "heading": heading,
                    "summary": abstract,
                    "source": source,
                    "url": url,
                    "related_points": related
                }

        # Fallback to Wikipedia summary if it's a topical query
        wiki_result = get_wikipedia_summary(query)
        if wiki_result.get("status") == "success":
            return wiki_result

        # Fallback lite HTML search
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        with httpx.Client(timeout=6.0, follow_redirects=True, headers=headers) as client:
            r = client.post(search_url)
            text = r.text
            # Simple snippet extractor
            from xml.etree import ElementTree
            import re
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', text, re.DOTALL)
            clean_snippets = [re.sub('<[^<]+?>', '', s).strip() for s in snippets[:max_results] if s.strip()]
            
            if clean_snippets:
                return {
                    "status": "success",
                    "query": query,
                    "results": clean_snippets
                }

        return {
            "status": "success",
            "query": query,
            "message": f"No direct summary found for '{query}'. Try opening browser search.",
            "search_url": f"https://duckduckgo.com/?q={encoded_query}"
        }
    except Exception as e:
        return {"status": "error", "message": f"Web search error: {str(e)}"}

def get_wikipedia_summary(topic: str) -> dict:
    """
    Get an encyclopedia summary of a concept, person, historical event, or place from Wikipedia.
    """
    try:
        title_encoded = urllib.parse.quote(topic.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title_encoded}"
        headers = {"User-Agent": "JarvisDesktopAssistant/1.0"}
        
        with httpx.Client(timeout=5.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "success",
                    "title": data.get("title"),
                    "description": data.get("description", ""),
                    "extract": data.get("extract", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                }
            return {"status": "not_found", "message": f"No Wikipedia entry found for '{topic}'."}
    except Exception as e:
        return {"status": "error", "message": f"Wikipedia query error: {str(e)}"}

def get_weather(city: str) -> dict:
    """
    Get current live weather conditions and temperature for any city in the world using Open-Meteo.
    """
    try:
        # Step 1: Geocode city name to lat/lon
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
        with httpx.Client(timeout=5.0) as client:
            geo_resp = client.get(geo_url).json()
            if not geo_resp.get("results"):
                return {"status": "error", "message": f"Could not find coordinates for city '{city}'."}
            
            loc = geo_resp["results"][0]
            lat = loc["latitude"]
            lon = loc["longitude"]
            city_name = loc["name"]
            country = loc.get("country", "")

            # Step 2: Fetch current weather
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=auto"
            weather_resp = client.get(weather_url).json()
            
            curr = weather_resp.get("current", {})
            temp_c = curr.get("temperature_2m")
            temp_f = round((temp_c * 9/5) + 32, 1) if temp_c is not None else None
            apparent_c = curr.get("apparent_temperature")
            apparent_f = round((apparent_c * 9/5) + 32, 1) if apparent_c is not None else None
            humidity = curr.get("relative_humidity_2m")
            wind_speed = curr.get("wind_speed_10m")
            wcode = curr.get("weather_code", 0)

            # Weather code interpretations (WMO code)
            conditions = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Foggy",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                71: "Slight snowfall",
                73: "Moderate snowfall",
                75: "Heavy snowfall",
                80: "Rain showers",
                81: "Moderate rain showers",
                82: "Violent rain showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail",
                99: "Thunderstorm with heavy hail"
            }
            condition_desc = conditions.get(wcode, "Variable conditions")

            return {
                "status": "success",
                "city": f"{city_name}, {country}",
                "condition": condition_desc,
                "temperature_c": temp_c,
                "temperature_f": temp_f,
                "feels_like_c": apparent_c,
                "feels_like_f": apparent_f,
                "humidity_percent": humidity,
                "wind_speed_kmh": wind_speed
            }
    except Exception as e:
        return {"status": "error", "message": f"Failed to retrieve weather: {str(e)}"}
