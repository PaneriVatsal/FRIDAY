"""
friday.tools.dispatcher — All tool implementation functions and dispatch_tool().
Copied exactly from existing main.py.
"""

import os
import re
import subprocess
import requests

# ─── PATHS (from existing main.py) ───────────────────────────────────────────

SCREENSHOT_DIR = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

USER_FACTS_PATH = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\memory\user-facts.md"
NOTES_DIR = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\notes"

# ─── TOOL IMPLEMENTATIONS ────────────────────────────────────────────────────


def execute_shell_command(command: str) -> str:
    try:
        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = res.stdout
        if res.stderr:
            output += "\n" + res.stderr
        return output if output.strip() else "[Command executed successfully with no output]"
    except subprocess.TimeoutExpired:
        return "[TIMEOUT] Command took longer than 30 seconds."
    except Exception as e:
        return f"[ERROR] {str(e)}"


def open_app(app_name: str, text_to_type: str = "") -> str:
    import time
    try:
        aliases = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "explorer": "explorer.exe",
            "files": "explorer.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "vscode": "code",
            "vs code": "code",
            "terminal": "wt.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "task manager": "taskmgr.exe",
            "taskmgr": "taskmgr.exe",
            "paint": "mspaint.exe",
            "wordpad": "wordpad.exe",
            "spotify": r"C:\Users\LP082W\AppData\Roaming\Spotify\Spotify.exe",
            "discord": r"C:\Users\LP082W\AppData\Local\Discord\Update.exe --processStart Discord.exe",
        }
        cmd = aliases.get(app_name.lower().strip(), app_name)
        subprocess.Popen(cmd, shell=True)
        if text_to_type:
            time.sleep(3)
            import pyautogui
            pyautogui.write(text_to_type, interval=0.05)
        return f"[OK] Opened '{app_name}'" + (f" and typed: {text_to_type}" if text_to_type else "")
    except Exception as e:
        return f"[ERROR] Could not open '{app_name}': {str(e)}"


def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[OK] File written: {path}"
    except Exception as e:
        return f"[ERROR] Could not write file: {str(e)}"


def read_file(path: str) -> str:
    """Read content from a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content if content.strip() else "[File is empty]"
    except FileNotFoundError:
        return f"[ERROR] File not found: {path}"
    except Exception as e:
        return f"[ERROR] Could not read file: {str(e)}"


def web_search(query: str) -> str:
    """Search the web using DuckDuckGo with multiple robust fallbacks."""
    results = []

    # Fallback 1: Try duckduckgo_search pip package via ddgs wrapper
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            ddg_results = list(ddgs.text(query, max_results=5))
            for r in ddg_results:
                title = r.get("title", "")
                href = r.get("href", "")
                body = r.get("body", "")
                if title and href:
                    results.append(f"- **{title}**\n  Link: {href}\n  {body}")
        if results:
            print("[Search] Succeeded using duckduckgo_search pip package.")
            return "\n\n".join(results)
    except Exception as e:
        print(f"[Search Debug] duckduckgo_search package failed/missing: {e}")
        results = []

    # Fallback 2: Try ddg-api Heroku app
    try:
        url = "https://ddg-api.herokuapp.com/search"
        resp = requests.get(url, params={"q": query, "limit": 5}, timeout=10)
        if resp.ok:
            data = resp.json()
            for r in data:
                title = r.get("title") or r.get("name") or ""
                href = r.get("href") or r.get("link") or r.get("url") or ""
                snippet = r.get("body") or r.get("snippet") or r.get("description") or ""
                if title and href:
                    results.append(f"- **{title}**\n  Link: {href}\n  {snippet}")
            if results:
                print("[Search] Succeeded using heroku api.")
                return "\n\n".join(results)
    except Exception as e:
        print(f"[Search Debug] heroku api failed: {e}")
        results = []

    # Fallback 3: Try html.duckduckgo.com scraping
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.post(url, data={"q": query}, headers=headers, timeout=10)
        if resp.ok:
            html = resp.text
            parts = html.split("web-result")
            for part in parts[1:]:
                title_m = re.search(r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', part, re.DOTALL)
                snippet_m = re.search(r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>', part, re.DOTALL)

                if title_m and snippet_m:
                    href = title_m.group(1)
                    title_html = title_m.group(2)
                    snippet_html = snippet_m.group(1)

                    title = re.sub(r'<[^>]*>', '', title_html).strip()
                    snippet = re.sub(r'<[^>]*>', '', snippet_html).strip()

                    from urllib.parse import unquote
                    if "uddg=" in href:
                        href = href.split("uddg=")[1].split("&")[0]
                        href = unquote(href)

                    results.append(f"- **{title}**\n  Link: {href}\n  {snippet}")
            if results:
                print("[Search] Succeeded using html scraping.")
                return "\n\n".join(results[:5])
    except Exception as e:
        print(f"[Search Debug] html scraping failed: {e}")

    return f"[No results found for: {query}]"


def take_screenshot(filename: str = "", focus_window: str = "") -> str:
    import datetime
    import time
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        if not filename:
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        if not filename.endswith(".png"):
            filename += ".png"
        save_path = os.path.join(SCREENSHOT_DIR, filename)

        # Focus the target window if specified
        if focus_window:
            focus_script = f"""
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class Win32 {{
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}}
'@
$proc = Get-Process | Where-Object {{ $_.MainWindowTitle -like '*{focus_window}*' -or $_.ProcessName -like '*{focus_window}*' }} | Select-Object -First 1
if ($proc) {{ [Win32]::SetForegroundWindow($proc.MainWindowHandle) }}
"""
            subprocess.run(["powershell", "-Command", focus_script], capture_output=True, timeout=10)
            time.sleep(1.5)

        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save('{save_path}')
$graphics.Dispose()
$bitmap.Dispose()
"""
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=15
        )
        if os.path.exists(save_path):
            return f"[OK] Screenshot saved: {save_path}\n[IMG]/screenshots/{filename}"
        return f"[ERROR] Screenshot failed: {result.stderr}"
    except Exception as e:
        return f"[ERROR] Screenshot failed: {str(e)}"


def fetch_url(url: str) -> str:
    """Fetch content of a URL and return it as plain text (HTML tags stripped)."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # Remove script and style elements content first
        html_clean = re.sub(r'<(script|style)[^>]*>([\s\S]*?)</\1>', ' ', html)

        # Replace block tags with newlines or spaces to preserve spacing
        html_clean = re.sub(r'</?(div|p|h1|h2|h3|h4|h5|h6|li|tr|br)[^>]*>', '\n', html_clean)

        # Strip remaining tags
        text = re.sub(r'<[^>]*>', ' ', html_clean)

        # Unescape HTML entities
        import html as html_lib
        text = html_lib.unescape(text)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        cleaned_text = "\n".join([line for line in lines if line])

        # Limit response length to prevent overloading context
        max_chars = 10000
        if len(cleaned_text) > max_chars:
            return cleaned_text[:max_chars] + f"\n\n[Content truncated to {max_chars} characters]"
        return cleaned_text if cleaned_text.strip() else "[No readable text found on page]"
    except Exception as e:
        return f"[ERROR] Failed to fetch URL '{url}': {str(e)}"


def get_weather_desc(code: int) -> str:
    mapping = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return mapping.get(code, f"Unknown ({code})")


def get_weather(city: str) -> str:
    """Get current weather for a city using Open-Meteo API."""
    try:
        # 1. Geocoding request
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geo_url, params={"name": city, "count": 1}, timeout=10)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        results = geo_data.get("results")
        if not results:
            return f"[ERROR] Could not find coordinates for city: {city}"

        location = results[0]
        lat = location.get("latitude")
        lon = location.get("longitude")
        name = location.get("name")
        country = location.get("country", "")

        # 2. Weather forecast request
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weathercode,windspeed_10m",
            "timezone": "auto"
        }
        weather_resp = requests.get(weather_url, params=weather_params, timeout=10)
        weather_resp.raise_for_status()
        weather_data = weather_resp.json()

        current = weather_data.get("current", {})
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("windspeed_10m")
        code = current.get("weathercode")

        conditions = get_weather_desc(code)

        return (
            f"Current Weather in **{name}, {country}**:\n"
            f"- Temperature: {temp}°C\n"
            f"- Relative Humidity: {humidity}%\n"
            f"- Wind Speed: {wind} km/h\n"
            f"- Conditions: {conditions}"
        )
    except Exception as e:
        return f"[ERROR] Failed to fetch weather for '{city}': {str(e)}"


def get_battery_percentage() -> str:
    """Get current battery percentage on Windows."""
    try:
        res = subprocess.run(
            ["powershell", "-Command", "(Get-WmiObject Win32_Battery).EstimatedChargeRemaining"],
            capture_output=True, text=True, timeout=15
        )
        if res.stdout.strip():
            return f"Battery Percentage: {res.stdout.strip()}%"
        if res.stderr.strip():
            return f"[ERROR] Could not fetch battery: {res.stderr.strip()}"
        return "[ERROR] Could not fetch battery (no output)"
    except Exception as e:
        return f"[ERROR] Could not fetch battery: {str(e)}"


def remember(fact: str) -> str:
    """Save a personal fact about the user."""
    try:
        dir_path = os.path.dirname(USER_FACTS_PATH)
        os.makedirs(dir_path, exist_ok=True)
        with open(USER_FACTS_PATH, "a", encoding="utf-8") as f:
            f.write(f"- {fact.strip()}\n")
        return f"[OK] Remembered: {fact}"
    except Exception as e:
        return f"[ERROR] Could not remember fact: {str(e)}"


def recall() -> str:
    """Read and return all remembered user facts."""
    try:
        if not os.path.exists(USER_FACTS_PATH):
            return "[No remembered facts found]"
        with open(USER_FACTS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return content if content else "[No remembered facts found]"
    except Exception as e:
        return f"[ERROR] Could not recall facts: {str(e)}"


def volume_control(action=None, level=None):
    if action is None and level is not None:
        try:
            lvl = int(level)
            if 0 <= lvl <= 100:
                presses = int(lvl / 2)
                ps_cmd = f"$obj = New-Object -ComObject WScript.Shell; for ($i=0; $i -lt 50; $i++) {{ $obj.SendKeys([char]174) }}; for ($i=0; $i -lt {presses}; $i++) {{ $obj.SendKeys([char]175) }}"
                subprocess.run(["powershell", "-Command", ps_cmd])
        except Exception as e:
            print(f"Error setting volume level: {e}")
        return

    if action == "mute" or action == "unmute":
        ps_cmd = "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173)"
        subprocess.run(["powershell", "-Command", ps_cmd])
    elif action == "louder":
        ps_cmd = "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]175)"
        subprocess.run(["powershell", "-Command", ps_cmd])
    elif action == "quieter":
        ps_cmd = "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]174)"
        subprocess.run(["powershell", "-Command", ps_cmd])
    elif level is not None:
        try:
            lvl = int(level)
            if 0 <= lvl <= 100:
                presses = int(lvl / 2)
                ps_cmd = f"$obj = New-Object -ComObject WScript.Shell; for ($i=0; $i -lt 50; $i++) {{ $obj.SendKeys([char]174) }}; for ($i=0; $i -lt {presses}; $i++) {{ $obj.SendKeys([char]175) }}"
                subprocess.run(["powershell", "-Command", ps_cmd])
        except Exception as e:
            print(f"Error setting volume level: {e}")


def get_volume() -> str:
    try:
        ps_code = """
$AudioCode = @'
using System;
using System.Runtime.InteropServices;

[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {
    int f(); int g(); int h(); int i();
    int SetMasterVolumeLevelScalar(float fLevel, Guid pguidEventContext);
    int j();
    int GetMasterVolumeLevelScalar(out float pfLevel);
}

[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {
    int Activate(ref Guid id, int clsCtx, int activationParams, out IAudioEndpointVolume aev);
}

[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {
    int f();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
}

[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumeratorComObject { }

public class AudioVolume {
    public static float GetVolume() {
        var enumerator = new MMDeviceEnumeratorComObject() as IMMDeviceEnumerator;
        IMMDevice dev = null;
        enumerator.GetDefaultAudioEndpoint(0, 1, out dev);
        IAudioEndpointVolume epv = null;
        var epvid = typeof(IAudioEndpointVolume).GUID;
        dev.Activate(ref epvid, 23, 0, out epv);
        float v = -1;
        epv.GetMasterVolumeLevelScalar(out v);
        return v;
    }
}
'@
Add-Type -TypeDefinition $AudioCode
[math]::Round([AudioVolume]::GetVolume() * 100)
"""
        res = subprocess.run(['powershell', '-Command', ps_code], capture_output=True, text=True, timeout=10)
        vol = res.stdout.strip()
        if vol and vol.isdigit():
            return f"Current volume: {vol}%"
        return f"Current volume info: {vol} (Error: {res.stderr.strip()})"
    except Exception as e:
        return f"[ERROR] Could not get volume: {str(e)}"


def type_text(text: str) -> str:
    import pyautogui
    import time
    time.sleep(3)
    pyautogui.write(text, interval=0.05)
    return f"[OK] Typed text: {text}"


def press_hotkey(keys) -> str:
    import pyautogui
    if isinstance(keys, str):
        keys_list = [k.strip() for k in keys.split("+")]
    else:
        keys_list = keys
    pyautogui.hotkey(*keys_list)
    return f"[OK] Pressed hotkey: {keys_list}"


def click_mouse(x: int = None, y: int = None, clicks: int = 1, button: str = "left") -> str:
    import pyautogui
    pyautogui.click(x=x, y=y, clicks=clicks, button=button)
    return f"[OK] Clicked mouse at ({x}, {y}) with {button} button {clicks} times."


def get_mouse_position() -> str:
    import pyautogui
    x, y = pyautogui.position()
    return f"Mouse position: ({x}, {y})"


def obsidian_write_note(title: str, content: str) -> str:
    os.makedirs(NOTES_DIR, exist_ok=True)
    path = os.path.join(NOTES_DIR, f"{title}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"[OK] Note saved: {path}"


def obsidian_read_note(title: str) -> str:
    path = os.path.join(NOTES_DIR, f"{title}.md")
    if not os.path.exists(path):
        return f"[ERROR] Note not found: {title}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def obsidian_search_notes(query: str) -> str:
    if not os.path.exists(NOTES_DIR):
        return "[No notes found]"
    results = []
    for fname in os.listdir(NOTES_DIR):
        if fname.endswith(".md"):
            fpath = os.path.join(NOTES_DIR, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            if query.lower() in content.lower() or query.lower() in fname.lower():
                results.append(f"- {fname}: {content[:200]}")
    return "\n".join(results) if results else f"[No notes matching: {query}]"


def obsidian_list_notes() -> str:
    if not os.path.exists(NOTES_DIR):
        return "[No notes directory found]"
    files = [f for f in os.listdir(NOTES_DIR) if f.endswith(".md")]
    return "\n".join(files) if files else "[No notes found]"


def get_system_uptime():
    from datetime import datetime
    try:
        res = subprocess.run(
            ["powershell", "-Command", "(gcim Win32_OperatingSystem).LastBootUpTime.ToString('o')"],
            capture_output=True, text=True, timeout=10
        )
        boot_time_str = res.stdout.strip()
        boot_time = datetime.fromisoformat(boot_time_str[:26])
        uptime = datetime.now() - boot_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes = remainder // 60
        return f"System uptime: {days} days, {hours} hours, {minutes} minutes"
    except Exception as e:
        return f"[ERROR] Could not get uptime: {str(e)}"


# ─── TOOL DISPATCHER ───────────────────────────────────────────────────────────

def dispatch_tool(name: str, arguments: dict) -> str:
    if name == "run_command":
        return execute_shell_command(arguments.get("command", ""))
    elif name == "open_app":
        return open_app(arguments.get("app_name", ""), arguments.get("text_to_type", ""))
    elif name == "write_file":
        return write_file(arguments.get("path", ""), arguments.get("content", ""))
    elif name == "read_file":
        return read_file(arguments.get("path", ""))
    elif name == "web_search":
        query = arguments.get("query", "")
        search_results = web_search(query)
        urls = re.findall(r'Link:\s*(https?://[^\s\n]+)', search_results)
        if urls:
            stopwords = {
                'weather', 'news', 'latest', 'current', 'today', 'search', 'find', 'lookup',
                'what', 'is', 'who', 'when', 'how', 'much', 'price', 'open', 'screenshot',
                'show', 'me', 'in', 'for', 'of', 'at', 'on', 'the', 'a', 'an', 'and', 'or',
                'to', 'near', 'forecast', 'temperature', 'humidity', 'wind', 'rain', 'snow',
                'weather forecast', 'reports'
            }
            cleaned_query = re.sub(r'[^\w\s]', ' ', query)
            query_words = [w.lower() for w in cleaned_query.split()]
            city_candidates = [w for w in query_words if w not in stopwords]

            chosen_url = ""
            fetched_content = ""

            if city_candidates:
                print(f"[Autofetch] Query city candidates: {city_candidates}")
                for url in urls:
                    url_lower = url.lower()
                    url_has_city = any(city in url_lower for city in city_candidates)

                    content = fetch_url(url)
                    content_lower = content.lower()
                    content_has_city = any(city in content_lower for city in city_candidates)

                    if url_has_city or content_has_city:
                        chosen_url = url
                        fetched_content = content
                        print(f"[Autofetch] Found matching URL containing city: {url}")
                        break
                    else:
                        print(f"[Autofetch] Skipping URL: {url} (no city keyword matched)")

            if not chosen_url:
                chosen_url = urls[0]
                print(f"[Autofetch] Falling back to first URL: {chosen_url}")
                fetched_content = fetch_url(chosen_url)

            combined_output = (
                f"=== Search Results ===\n{search_results}\n\n"
                f"=== Auto-Fetched Content from {chosen_url} ===\n{fetched_content}"
            )
            return combined_output
        return search_results
    elif name == "take_screenshot":
        return take_screenshot(arguments.get("filename", ""), arguments.get("focus_window", ""))
    elif name == "fetch_url":
        return fetch_url(arguments.get("url", ""))
    elif name == "get_weather":
        return get_weather(arguments.get("city", ""))
    elif name == "get_battery_percentage":
        return get_battery_percentage()
    elif name == "remember":
        return remember(arguments.get("fact", ""))
    elif name == "recall":
        return recall()
    elif name == "volume_control":
        return volume_control(**{k: arguments.get(k) for k in arguments}) or "[OK] Volume action executed"
    elif name == "get_volume":
        return str(get_volume())
    elif name == "type_text":
        return type_text(arguments.get("text", ""))
    elif name == "press_hotkey":
        return press_hotkey(arguments.get("keys"))
    elif name == "click_mouse":
        return click_mouse(
            x=arguments.get("x"),
            y=arguments.get("y"),
            clicks=arguments.get("clicks", 1),
            button=arguments.get("button", "left")
        )
    elif name == "get_mouse_position":
        return get_mouse_position()
    elif name == "obsidian_write_note":
        return obsidian_write_note(arguments.get("title", ""), arguments.get("content", ""))
    elif name == "obsidian_read_note":
        return obsidian_read_note(arguments.get("title", ""))
    elif name == "obsidian_search_notes":
        return obsidian_search_notes(arguments.get("query", ""))
    elif name == "obsidian_list_notes":
        return obsidian_list_notes()
    elif name == "get_system_uptime":
        return get_system_uptime(**{k: arguments.get(k) for k in arguments})
    return f"[ERROR] Unknown tool: {name}"
