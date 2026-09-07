from .system_tools import get_system_telemetry, adjust_volume, take_screenshot
from .app_tools import launch_application, open_url
from .web_tools import search_web, get_wikipedia_summary, get_weather
from .utility_tools import add_note, list_notes, add_reminder, list_reminders, get_current_datetime

# Mapping of function names to callable functions
ALL_TOOLS = [
    get_system_telemetry,
    adjust_volume,
    take_screenshot,
    launch_application,
    open_url,
    search_web,
    get_wikipedia_summary,
    get_weather,
    add_note,
    list_notes,
    add_reminder,
    list_reminders,
    get_current_datetime
]

TOOL_REGISTRY = {func.__name__: func for func in ALL_TOOLS}

def execute_tool(name: str, args: dict) -> dict:
    """
    Safely execute a tool by name with arguments.
    """
    if name not in TOOL_REGISTRY:
        return {"status": "error", "message": f"Tool '{name}' not found."}
    
    func = TOOL_REGISTRY[name]
    try:
        if args:
            result = func(**args)
        else:
            result = func()
        return result
    except Exception as e:
        return {"status": "error", "message": f"Error executing {name}: {str(e)}"}
