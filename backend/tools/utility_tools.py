import json
import datetime
from pathlib import Path
from backend.config import DATA_DIR

NOTES_FILE = DATA_DIR / "notes.json"
REMINDERS_FILE = DATA_DIR / "reminders.json"

def _load_json(file_path: Path) -> list:
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def _save_json(file_path: Path, data: list):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def add_note(content: str) -> dict:
    """
    Save a quick personal note or thought to Jarvis's memory log.
    """
    try:
        notes = _load_json(NOTES_FILE)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        note_entry = {
            "id": len(notes) + 1,
            "timestamp": now_str,
            "content": content
        }
        notes.append(note_entry)
        _save_json(NOTES_FILE, notes)
        return {"status": "success", "message": f"Note saved: '{content}' (Note #{note_entry['id']})"}
    except Exception as e:
        return {"status": "error", "message": f"Could not save note: {str(e)}"}

def list_notes() -> dict:
    """
    Retrieve all saved notes from Jarvis's memory log.
    """
    notes = _load_json(NOTES_FILE)
    return {"status": "success", "count": len(notes), "notes": notes}

def add_reminder(task: str, due_time: str = None) -> dict:
    """
    Add a task or reminder for Jarvis to remember.
    """
    try:
        reminders = _load_json(REMINDERS_FILE)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        item = {
            "id": len(reminders) + 1,
            "created_at": now_str,
            "task": task,
            "due": due_time or "unscheduled",
            "completed": False
        }
        reminders.append(item)
        _save_json(REMINDERS_FILE, reminders)
        return {"status": "success", "message": f"Reminder recorded: '{task}'", "due": item["due"]}
    except Exception as e:
        return {"status": "error", "message": f"Could not save reminder: {str(e)}"}

def list_reminders() -> dict:
    """
    List all pending and completed reminders.
    """
    reminders = _load_json(REMINDERS_FILE)
    return {"status": "success", "count": len(reminders), "reminders": reminders}

def get_current_datetime() -> dict:
    """
    Get current local date, time, and day of the week.
    """
    now = datetime.datetime.now()
    return {
        "status": "success",
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M:%S %p"),
        "iso": now.isoformat()
    }
