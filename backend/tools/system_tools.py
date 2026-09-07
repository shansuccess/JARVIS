import os
import sys
import time
import datetime
import subprocess
import ctypes
import psutil
from pathlib import Path
from backend.config import SCREENSHOTS_DIR

# Windows Virtual Key Codes for Audio
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP   = 0xAF
KEYEVENTF_KEYUP = 0x0002

def _press_key(vk_code: int):
    """Simulate key press on Windows."""
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
    except Exception as e:
        pass

def get_system_telemetry() -> dict:
    """
    Get real-time CPU, RAM, Disk, Battery, and Uptime status of the host machine.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        cpu_mhz = round(cpu_freq.current) if cpu_freq else 0

        mem = psutil.virtual_memory()
        ram_total_gb = round(mem.total / (1024 ** 3), 2)
        ram_used_gb = round(mem.used / (1024 ** 3), 2)
        ram_percent = mem.percent

        disk = psutil.disk_usage('/')
        disk_total_gb = round(disk.total / (1024 ** 3), 2)
        disk_used_gb = round(disk.used / (1024 ** 3), 2)
        disk_percent = disk.percent

        battery_info = {"has_battery": False, "percent": 100, "power_plugged": True}
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_info = {
                    "has_battery": True,
                    "percent": round(battery.percent),
                    "power_plugged": battery.power_plugged,
                    "secs_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else -1
                }
        except Exception:
            pass

        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = int(time.time() - psutil.boot_time())
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))

        return {
            "status": "success",
            "cpu": {
                "percent": cpu_percent,
                "cores": cpu_count,
                "frequency_mhz": cpu_mhz
            },
            "memory": {
                "total_gb": ram_total_gb,
                "used_gb": ram_used_gb,
                "percent": ram_percent
            },
            "disk": {
                "total_gb": disk_total_gb,
                "used_gb": disk_used_gb,
                "percent": disk_percent
            },
            "battery": battery_info,
            "uptime": uptime_str,
            "boot_time": boot_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to gather telemetry: {str(e)}"}

def adjust_volume(action: str, steps: int = 5) -> dict:
    """
    Adjust master audio volume on Windows.
    action: 'up', 'down', 'mute', or 'unmute'
    steps: number of 2% step increments (default 5 = 10%)
    """
    action = action.lower().strip()
    try:
        if action == "mute" or action == "unmute" or action == "toggle_mute":
            _press_key(VK_VOLUME_MUTE)
            return {"status": "success", "message": "Toggled master audio mute state."}
        elif action == "up":
            for _ in range(max(1, min(steps, 25))):
                _press_key(VK_VOLUME_UP)
            return {"status": "success", "message": f"Increased audio volume by {steps * 2}%."}
        elif action == "down":
            for _ in range(max(1, min(steps, 25))):
                _press_key(VK_VOLUME_DOWN)
            return {"status": "success", "message": f"Decreased audio volume by {steps * 2}%."}
        else:
            return {"status": "error", "message": f"Unknown volume action '{action}'. Use up, down, or mute."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to adjust volume: {str(e)}"}

def take_screenshot(custom_name: str = None) -> dict:
    """
    Take a full-screen screenshot and save it to the screenshots directory.
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{custom_name}_{timestamp}.png" if custom_name else f"screenshot_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename

        # Use PowerShell to capture screen cleanly without extra dependencies
        ps_script = f"""
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $screens = [System.Windows.Forms.Screen]::PrimaryScreen
        $top    = ($screens.Bounds.Top)
        $left   = ($screens.Bounds.Left)
        $width  = ($screens.Bounds.Width)
        $height = ($screens.Bounds.Height)
        $bitmap = New-Object System.Drawing.Bitmap $width, $height
        $graphic = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphic.CopyFromScreen($left, $top, 0, 0, $bitmap.Size)
        $bitmap.Save('{str(filepath)}')
        $graphic.Dispose()
        $bitmap.Dispose()
        """
        result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=10)
        if filepath.exists() and filepath.stat().st_size > 0:
            return {
                "status": "success",
                "message": f"Screenshot captured and saved to {filepath.name}",
                "path": str(filepath),
                "filename": filepath.name
            }
        else:
            return {"status": "error", "message": f"Screenshot generation failed: {result.stderr}"}
    except Exception as e:
        return {"status": "error", "message": f"Screenshot failed: {str(e)}"}
