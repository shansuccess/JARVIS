import os
import subprocess
import webbrowser

COMMON_APPS = {
    "notepad": "notepad.exe",
    "calc": "calc.exe",
    "calculator": "calc.exe",
    "mspaint": "mspaint.exe",
    "paint": "mspaint.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "code": "code",
    "vs code": "code",
    "vscode": "code",
    "spotify": "spotify",
    "settings": "start ms-settings:",
    "control panel": "control",
}

def launch_application(app_name: str) -> dict:
    """
    Launch a desktop application by name or common alias.
    Examples: 'chrome', 'notepad', 'calculator', 'vs code', 'spotify', 'task manager'.
    """
    cleaned = app_name.lower().strip()
    target_cmd = COMMON_APPS.get(cleaned, cleaned)
    
    try:
        # Special handling for Windows URI schemes
        if target_cmd.startswith("start "):
            os.system(target_cmd)
            return {"status": "success", "message": f"Successfully launched {app_name}."}

        # Try launching directly with startfile or Popen
        try:
            os.startfile(target_cmd)
            return {"status": "success", "message": f"Successfully launched {app_name}."}
        except Exception:
            # Fallback to subprocess via shell
            subprocess.Popen(f"start {target_cmd}", shell=True)
            return {"status": "success", "message": f"Initiated launch of {app_name}."}
    except Exception as e:
        return {"status": "error", "message": f"Could not launch application '{app_name}': {str(e)}"}

def open_url(url: str) -> dict:
    """
    Open a website URL in the user's default web browser.
    """
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        webbrowser.open(url)
        return {"status": "success", "message": f"Opened {url} in web browser."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to open URL: {str(e)}"}
