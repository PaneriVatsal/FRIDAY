import os
import json
import subprocess
import requests
import re
import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="FRIDAY Python Agent Backend")

VAULT_LOG_PATH = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\memory\current-task.md"
SCREENSHOT_DIR = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\screenshots"
USER_FACTS_PATH = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\memory\user-facts.md"

def load_user_facts() -> str:
    if not os.path.exists(USER_FACTS_PATH):
        return ""
    try:
        with open(USER_FACTS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return f"\n\n=== USER FACTS ===\n{content}"
    except Exception as e:
        print(f"Error loading user facts: {e}")
    return ""

def load_skills() -> str:
    skills_dir = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\skills"
    if not os.path.exists(skills_dir):
        return ""
    skills_content = []
    for root, _, files in os.walk(skills_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    if content:
                        skills_content.append(content)
                except Exception as e:
                    print(f"Error loading skill file {file_path}: {e}")
    if skills_content:
        return "\n\n=== SPECIAL SKILLS & GUIDELINES ===\n\n" + "\n\n".join(skills_content)
    return ""

class ChatRequest(BaseModel):
    message: str

def route_model(message: str) -> str:
    keywords = [
        'code', 'program', 'python', 'javascript', 'typescript', 'html', 'css',
        'script', 'file', 'compile', 'debug', 'directory', 'folder', 'git',
        'terminal', 'bash', 'run', 'execute', 'quicksort', 'function', 'class',
        'develop', 'rust', 'c++', 'java', 'sql', 'command', 'shell', 'npm', 'pip',
        'search', 'weather', 'news', 'fetch', 'find', 'lookup', 'what is', 'who is',
        'when is', 'how much', 'price', 'latest', 'current', 'today', 'open',
        'screenshot', 'show me', 'battery', 'charge', 'power', 'who am i', 'my name',
        'remember', 'recall', 'user facts', 'personal',
        'add tool', 'add a tool', 'improve', 'self improve', 'new feature', 'add feature', 'add capability', 'can you add',
        'volume', 'mute', 'unmute', 'brightness', 'sound',
        'what can you', 'what features', 'capabilities', 'what tools', 'what do you',
        'do it', 'type', 'click', 'press', 'write file', 'write to', 'keyboard', 'mouse'
    ]
    if any(kw in message.lower() for kw in keywords):
        return "qwen2.5-coder:latest"
    return "gemma4:e4b"

# ─── TOOLS ────────────────────────────────────────────────────────────────────

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

def take_screenshot(filename: str = "") -> str:
    """Take a screenshot and save it to the vault screenshots folder."""
    try:
        import datetime
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        if not filename:
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        if not filename.endswith(".png"):
            filename += ".png"
        save_path = os.path.join(SCREENSHOT_DIR, filename)
        # Use PowerShell to take screenshot (no extra deps needed)
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
            return f"[OK] Screenshot saved: {save_path}"
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

class ImproveRequest(BaseModel):
    task: str

@app.post("/improve")
async def improve_endpoint(req: ImproveRequest):
    task = req.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task cannot be empty")
        
    try:
        import datetime
        import glob
        
        # 1. Backups directory management
        backup_dir = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"main_backup_{timestamp}.py"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Read current main.py
        current_path = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday\main.py"
        with open(current_path, "r", encoding="utf-8") as f:
            current_code = f.read()
            
        # Write backup
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(current_code)
            
        # Keep only the last 5 backups
        backup_files = sorted(
            glob.glob(os.path.join(backup_dir, "main_backup_*.py")),
            key=os.path.getmtime
        )
        if len(backup_files) > 5:
            for old_backup in backup_files[:-5]:
                try:
                    os.remove(old_backup)
                except Exception as e:
                    print(f"Failed to delete old backup {old_backup}: {e}")
                    
        # 2. Read the skills vault for relevant info
        skills_info = load_skills()
        
        # 3. Call Ollama for ONLY the new tool function code
        system_msg_func = (
            "You are a master python programmer. Your task is to write ONLY the Python function code (using `def ...`) that implements the requested capability.\n"
            "CRITICAL: Never mix single and double quotes inside f-strings. Use only single quotes for the outer string and avoid double quotes inside f-strings entirely. Use subprocess.run with a list of arguments instead of a shell string.\n"
            "CRITICAL: The function must be valid Python only. Any shell commands must be wrapped in subprocess.run(). Do not include example usage calls at the bottom. Import any needed modules inside the function.\n"
            "CRITICAL: Do NOT write the entire file. Do NOT write any introduction or explanation text. Only output the code inside a raw python code block (using ```python ... ```)."
        )
        user_prompt_func = (
            f"Please write the Python function code for the following feature/task:\n\n"
            f"Task: {task}\n\n"
            f"Refer to the skills vault if needed:\n{skills_info}"
        )
        
        payload_func = {
            "model": "qwen2.5-coder:latest",
            "messages": [
                {"role": "system", "content": system_msg_func},
                {"role": "user", "content": user_prompt_func}
            ],
            "stream": False
        }
        
        print(f"[Improve Endpoint] Querying Qwen for Python function implementation...")
        res_func = requests.post("http://127.0.0.1:11434/api/chat", json=payload_func, timeout=300)
        res_func.raise_for_status()
        
        assistant_content_func = res_func.json().get("message", {}).get("content", "")
        print(f"[Improve Endpoint] Function LLM response (first 500 chars):\n{assistant_content_func[:500]}")
        
        code_match = re.search(r'```python\s*([\s\S]*?)```', assistant_content_func)
        if not code_match:
            code_match = re.search(r'```\s*([\s\S]*?)```', assistant_content_func)
            
        if not code_match:
            if "def " in assistant_content_func:
                start_idx = assistant_content_func.find("def ")
                function_code = assistant_content_func[start_idx:].strip()
            else:
                raise Exception("LLM response did not contain a valid python function block starting with def.")
        else:
            function_code = code_match.group(1).strip()
            
        # Strip markdown code fences
        function_code = function_code.replace("```python", "").replace("```", "").strip()
        
        # Post-processing: Remove example usage calls or comments
        name_match = re.search(r'def\s+([a-zA-Z0-9_]+)', function_code)
        extracted_tool_name = name_match.group(1) if name_match else ""
        cleaned_lines = []
        for line in function_code.splitlines():
            stripped = line.strip()
            if stripped.startswith("# Example") or stripped.startswith("# example"):
                continue
            if extracted_tool_name and re.match(rf'^{extracted_tool_name}\(', stripped):
                continue
            cleaned_lines.append(line)
        function_code = "\n".join(cleaned_lines).strip()
        
        # Repair f-string nested quote issues (e.g. f"some {dict["key"]}" -> f"some {dict['key']}")
        repaired_lines = []
        for line in function_code.splitlines():
            if 'f"' in line and '{' in line and '"' in line:
                parts = re.split(r'(\{[^\}]*\})', line)
                for i in range(1, len(parts), 2):
                    parts[i] = parts[i].replace('"', "'")
                line = "".join(parts)
            repaired_lines.append(line)
        function_code = "\n".join(repaired_lines).strip()
        
        # Check for unescaped triple quotes
        if function_code.count('"""') % 2 != 0:
            raise Exception("Extracted function contains unescaped triple double-quotes.")
        if function_code.count("'''") % 2 != 0:
            raise Exception("Extracted function contains unescaped triple single-quotes.")
            
        # Print function code to terminal
        print(f"[Improve Endpoint] Cleaned function code:\n{function_code}")
        
        print(f"[Improve Endpoint] Generated function length: {len(function_code)} characters")
        if len(function_code) < 50:
            raise Exception("Generated function code is too short.")
            
        # 4. Call Ollama for the JSON TOOLS_DEFINITION entry
        system_msg_json = (
            "You are a master programmer. Your task is to write ONLY the JSON/dict entry representing this new function's parameters and description, matching the format of TOOLS_DEFINITION.\n"
            "Format details: it must have key keys 'type': 'function' and 'function': {'name': '...', 'description': '...', 'parameters': {...}}.\n"
            "CRITICAL: Do NOT write any introduction or explanation text. Only output raw JSON inside a ```json ... ``` or ``` ... ``` block."
        )
        user_prompt_json = (
            f"Write the TOOLS_DEFINITION JSON entry for this function/feature:\n\n"
            f"Task: {task}\n\n"
            f"The generated python function is:\n{function_code}"
        )
        
        payload_json = {
            "model": "qwen2.5-coder:latest",
            "messages": [
                {"role": "system", "content": system_msg_json},
                {"role": "user", "content": user_prompt_json}
            ],
            "stream": False
        }
        
        print(f"[Improve Endpoint] Querying Qwen for JSON tool definition...")
        res_json = requests.post("http://127.0.0.1:11434/api/chat", json=payload_json, timeout=300)
        res_json.raise_for_status()
        
        assistant_content_json = res_json.json().get("message", {}).get("content", "")
        print(f"[Improve Endpoint] JSON LLM response (first 500 chars):\n{assistant_content_json[:500]}")
        
        json_match = re.search(r'```json\s*([\s\S]*?)```', assistant_content_json)
        if not json_match:
            json_match = re.search(r'```\s*([\s\S]*?)```', assistant_content_json)
            
        if not json_match:
            if "{" in assistant_content_json:
                start_idx = assistant_content_json.find("{")
                end_idx = assistant_content_json.rfind("}") + 1
                json_entry_str = assistant_content_json[start_idx:end_idx].strip()
            else:
                raise Exception("LLM response did not contain a valid JSON object.")
        else:
            json_entry_str = json_match.group(1).strip()
            
        # Parse tool name
        try:
            def_data = json.loads(json_entry_str)
            tool_name = def_data["function"]["name"]
        except Exception:
            name_match = re.search(r'def\s+([a-zA-Z0-9_]+)', function_code)
            if name_match:
                tool_name = name_match.group(1)
            else:
                raise Exception("Could not determine tool name from either function code or JSON definition.")
                
        # 5. Incremental Injection logic using markers
        TOOL_DISPATCHER_MARKER = "# " + "─── TOOL DISPATCHER ───"
        modified_code = current_code.replace(TOOL_DISPATCHER_MARKER, function_code + '\n\n' + TOOL_DISPATCHER_MARKER, 1)
        
        # Marker B: Dispatch case inside dispatch_tool before return f"[ERROR] Unknown tool: {name}"
        marker_error = "    " + 'return f"[ERROR] Unknown tool: {name}"'
        if marker_error not in modified_code:
            raise Exception("Marker for unknown tool error not found in main.py")
        dispatch_case = f"    elif name == \"{tool_name}\":\n        return {tool_name}(**{{k: arguments.get(k) for k in arguments}})\n"
        modified_code = modified_code.replace(marker_error, f"{dispatch_case}{marker_error}", 1)
        
        # Marker C: Tool definition inside TOOLS_DEFINITION before the closing ]
        marker_tools_end = "]\n\n" + 'SYSTEM_PROMPT = """You are FRIDAY'
        if marker_tools_end not in modified_code:
            marker_tools_end = "]\r\n\r\n" + 'SYSTEM_PROMPT = """You are FRIDAY'
        if marker_tools_end not in modified_code:
            raise Exception("Could not find the end of TOOLS_DEFINITION list marker.")
            
        # Cleanly format json_entry_str
        try:
            parsed_json = json.loads(json_entry_str)
            formatted_json = json.dumps(parsed_json, indent=8)
            lines = formatted_json.splitlines()
            indented_lines = [lines[0]] + ["    " + line for line in lines[1:]]
            formatted_json = "\n".join(indented_lines)
        except Exception:
            formatted_json = json_entry_str
            
        replacement_text = f",\n    {formatted_json}\n" + marker_tools_end
        modified_code = modified_code.replace(marker_tools_end, replacement_text, 1)
        
        # Write modified code to main.py
        with open(current_path, "w", encoding="utf-8") as f:
            f.write(modified_code)
            
        # Print lines around the dispatcher to help with syntax error debugging
        try:
            mod_lines = modified_code.splitlines()
            disp_idx = -1
            for idx, line in enumerate(mod_lines):
                if TOOL_DISPATCHER_MARKER in line:
                    disp_idx = idx
                    break
            if disp_idx != -1:
                start_print = max(0, disp_idx - 15)
                end_print = min(len(mod_lines), disp_idx + 15)
                print(f"[Improve Endpoint] Surrounding modified code (lines {start_print} to {end_print}):")
                for idx in range(start_print, end_print):
                    print(f"{idx + 1}: {mod_lines[idx]}")
        except Exception as pe:
            print(f"[Improve Endpoint] Failed to print surrounding code: {pe}")
            
        # 6. Compile check
        import ast
        try:
            ast.parse(modified_code)
        except SyntaxError as e:
            with open(current_path, "w", encoding="utf-8") as f:
                f.write(current_code)
            raise Exception(f"Syntax error in generated code: {e}")
            
        # 7. Save note to improvements.md
        improvements_path = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\memory\improvements.md"
        os.makedirs(os.path.dirname(improvements_path), exist_ok=True)
        log_entry = (
            f"### Direct Endpoint Improvement ({timestamp})\n"
            f"- **Task**: {task}\n"
            f"- **Status**: Success\n"
            f"- **Backup Created**: {backup_filename}\n\n"
        )
        with open(improvements_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
        return {"status": "success", "response": f"Successfully implemented task '{task}'. Compilation passed. Backup saved to {backup_filename}."}
        
    except Exception as e:
        return {"status": "failure", "response": f"Failed to improve: {str(e)}"}


import subprocess

def volume_control(action=None, level=None):
    import subprocess
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

import subprocess

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

# ─── TOOL DISPATCHER ───

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
        import re
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
        return take_screenshot(arguments.get("filename", ""))
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
    return f"[ERROR] Unknown tool: {name}"

# ─── TOOL DEFINITIONS ─────────────────────────────────────────────────────────

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command on the host Windows system and return terminal output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open any application by name or full path, and optionally type text into it after it opens. Parameters: app_name (required), text_to_type (optional).",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "App name or path to open."},
                    "text_to_type": {"type": "string", "description": "Optional text to type into the app after it opens."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file on disk. Creates the file if it doesn't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path to write to."},
                    "content": {"type": "string", "description": "Text content to write into the file."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return the content of a file from disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path to read."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo and return relevant results. Use for current info, news, facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the user's screen and save it to the vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Optional filename for the screenshot (without path). Auto-generated if not provided."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Fetch content from a URL and return it as plain text (HTML tags stripped). Useful to read the details of specific pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather forecast for a specified city (temperature, humidity, wind, and conditions).",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The name of the city to get weather for."}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_battery_percentage",
            "description": "Get the current battery percentage of the device.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Save a personal fact about the user (e.g. name, age, preference, location, job).",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The personal fact to remember."}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "Recall all personal facts saved about the user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "volume_control",
            "description": "Control system volume. Use action='mute', 'unmute', 'louder', 'quieter', or pass level=0-100 to set specific volume.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "mute, unmute, louder, quieter"},
                    "level": {"type": "integer", "description": "Volume level 0-100"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_volume",
            "description": "Get current system volume level.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text directly into the currently active/focused window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to type."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_hotkey",
            "description": "Press a keyboard hotkey combination (e.g. ctrl+c, alt+tab, win+r).",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "string",
                        "description": "Hotkey string separated by plus (e.g. 'ctrl+t', 'alt+f4')."
                    }
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_mouse",
            "description": "Click the mouse at specified coordinates or at the current mouse cursor location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Optional X coordinate to click."},
                    "y": {"type": "integer", "description": "Optional Y coordinate to click."},
                    "clicks": {"type": "integer", "description": "Number of clicks (default 1)."},
                    "button": {"type": "string", "description": "Mouse button: 'left', 'right', 'middle' (default 'left')."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_mouse_position",
            "description": "Retrieve the current coordinates (X and Y) of the mouse cursor on screen.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

SYSTEM_PROMPT = """You are FRIDAY, a locally-running Jarvis-style AI assistant with full control over the user's Windows PC.

You have access to these tools:
- run_command: Run any shell/PowerShell command
- open_app: Open any application (chrome, notepad, spotify, vscode, terminal, etc.)
- write_file: Write content to any file
- read_file: Read content from any file
- web_search: Search the web via DuckDuckGo
- take_screenshot: Capture the screen
- fetch_url: Fetch the text content of any URL (HTML stripped)
- get_weather: Get the current weather for a city
- get_battery_percentage: Get the current battery percentage of the device
- remember: Save a personal fact about the user
- recall: Read and return all remembered user facts
- volume_control: Control system volume (mute, unmute, louder, quieter, or set level)
- get_volume: Get current system volume level
- type_text: Type text directly into the currently active/focused window
- press_hotkey: Press a keyboard hotkey combination (e.g. ctrl+c, alt+tab, win+r)
- click_mouse: Click the mouse at specified coordinates or at the current mouse cursor location
- get_mouse_position: Retrieve the current coordinates (X and Y) of the mouse cursor on screen

RULES:
- CRITICAL: You have FULL administrator permissions. NEVER claim you lack permission to write files, open apps, or execute commands.
- CRITICAL: If the user asks to create, write, or save a new file without specifying a directory, ALWAYS default to `C:\\Users\\LP082W\\Documents\\`. Make up a sensible filename (e.g., `C:\\Users\\LP082W\\Documents\\note.txt`) if none is provided.
- CRITICAL: Your Windows username is LP082W. Your absolute user path is C:\\Users\\LP082W\\. NEVER use <YourUsername> or placeholder paths.
- CRITICAL: When you need to call a tool, output ONLY the raw JSON block. Do not output any conversational text, explanations, or acknowledgment before or after the JSON.
- CRITICAL: When told to write or type something in an app, you MUST always call open_app first, wait for it to open, then IMMEDIATELY call type_text in the same response. Never stop after just opening the app. Never tell the user to type it themselves. Always complete the full chain in one go.
- Keep responses concise and direct. Never dump exhaustive lists unless the user explicitly asks for a full list. Summarize with key points only.
- When asked what you can do, what features you have, or what tools you support, always answer directly from your tool list above. Do NOT search the web or read any files.
- When asked what you can do, what features you have, or what tools you have, list your actual tools directly from this prompt without using any tool calls: run_command, open_app, write_file, read_file, web_search, fetch_url, get_weather, take_screenshot, get_battery_percentage, remember, recall, volume_control, get_volume. Never hallucinate tools like nircmd.
- Use tools only when needed. For general chat/questions, reply directly.
- The user's Windows username is LP082W. Always use C:\\Users\\LP082W\\ in file paths. Never use placeholder paths like <YourUsername>.
- After searching, if the results are just links or short snippets, use fetch_url on the most relevant link to get the actual full content before responding to the user.
- After receiving tool output, analyze it and give a clear plain-text response.
- Never output a JSON tool call block after receiving tool output.
- For Windows commands, avoid interactive commands that hang (use 'date /t' not 'date').
- You can chain multiple tools if needed to complete a task.
- NEVER say placeholder text like [insert value here] or vague responses like I was unable to check. ALWAYS use run_command to execute the actual PowerShell command and report the real output to the user.
- The RECENT CONVERSATION HISTORY section is for context only — do not continue or repeat old conversations, only use it to remember facts about the user.
- When a user tells you their name or any personal fact like "my name is X", simply acknowledge it and remember it. Do NOT search the web for their name. Do NOT confuse it with a celebrity or public figure. Just say something like Hello Vatsal, nice to meet you!
- When the user tells you something personal (their name, preferences, location, job, etc.) ALWAYS call remember() to save it. When answering personal questions, call recall() first. Never search the web for personal information the user has told you.
""" + load_skills() + load_user_facts()

# ─── VAULT LOGGING ────────────────────────────────────────────────────────────

REFUSAL_PHRASES = [
    "i'm sorry", "i cannot", "i don't have permission",
    "as an ai", "i apologize", "i am unable", "i can't",
    "unfortunately", "i do not have the ability",
    "tool_name [", "you can call tools",
    "it seems like the previous response caused an error",
    "let me try again from scratch", "here are some examples of tools"
]

def log_to_vault(user_msg: str, model_used: str, final_reply: str):
    dir_path = os.path.dirname(VAULT_LOG_PATH)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    indented_reply = "\n".join(f"  {line}" for line in final_reply.splitlines())
    reply_lower = final_reply.lower()
    if any(phrase in reply_lower for phrase in REFUSAL_PHRASES):
        print(f"[Vault] Skipped logging bad response.")
        return
    log_entry = (
        f"- **User**: {user_msg}\n"
        f"- **Model**: `{model_used}`\n"
        f"- **Response**:\n{indented_reply}\n\n"
    )
    try:
        with open(VAULT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error logging to vault: {e}")

def load_recent_memory(n=20) -> str:
    if not os.path.exists(VAULT_LOG_PATH):
        return ""
    try:
        with open(VAULT_LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        parts = re.split(r'\n(?=- \*\*User\*\*:)', content)
        entries = []
        for part in parts:
            part = part.strip()
            if part.startswith("- **User**:"):
                entries.append(part)
            elif "- **User**:" in part:
                subparts = part.split("- **User**:", 1)
                if len(subparts) == 2:
                    entries.append("- **User**:" + subparts[1].strip())
        
        recent_entries = entries[-n:]
        return "\n\n".join(recent_entries)
    except Exception as e:
        print(f"Error loading recent memory: {e}")
        return ""

def summarize_old_memory():
    if not os.path.exists(VAULT_LOG_PATH):
        return
    try:
        with open(VAULT_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if len(lines) <= 200:
            return
            
        lines_to_summarize = lines[:150]
        remaining_lines = lines[150:]
        
        text_to_summarize = "".join(lines_to_summarize)
        summary_text = ""
        try:
            payload = {
                "model": "gemma4:e4b",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant. Summarize the following conversation history briefly, focusing on the key tasks completed, user requests, and outcomes. Keep the summary concise and in bullet points."},
                    {"role": "user", "content": text_to_summarize}
                ],
                "stream": False
            }
            res = requests.post("http://127.0.0.1:11434/api/chat", json=payload, timeout=30)
            if res.ok:
                summary_text = res.json().get("message", {}).get("content", "").strip()
        except Exception as e:
            print(f"Ollama summarization failed: {e}")
            
        if not summary_text:
            summary_text = f"[Fallback Summary - AI call failed]\nRaw text snippet:\n" + text_to_summarize[:500] + "\n..."
            
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        summary_entry = (
            f"### Summary ({timestamp})\n"
            f"{summary_text}\n\n"
        )
        
        summary_path = os.path.join(os.path.dirname(VAULT_LOG_PATH), "summary.md")
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(summary_entry)
            
        output_text = "".join(remaining_lines)
        if not output_text.strip().startswith("# Current Task"):
            output_text = "# Current Task\n\n" + output_text.lstrip()
            
        with open(VAULT_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(output_text)
            
        print(f"[Memory] Successfully summarized {len(lines_to_summarize)} lines to summary.md")
    except Exception as e:
        print(f"Error in summarize_old_memory: {e}")

# ─── CHAT ENDPOINT ────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    user_message = req.message.strip()
    capability_triggers = ['what can you do', 'what features', 'what tools', 'capabilities', 'what do you do', 'what can you']
    if any(trigger in user_message.lower() for trigger in capability_triggers):
        response = 'Here is what I can do:\n\n- run_command: Run any shell/PowerShell command\n- open_app: Open applications (chrome, notepad, spotify, etc.)\n- write_file / read_file: Read and write files\n- web_search: Search the web via DuckDuckGo\n- fetch_url: Read content from any URL\n- get_weather: Real-time weather for any city\n- take_screenshot: Capture your screen\n- get_battery_percentage: Check battery level\n- volume_control: Mute, unmute, louder, quieter, or set level\n- get_volume: Get current volume level\n- remember / recall: Save and retrieve personal facts\n- /improve [task]: Add new tools to myself'
        log_to_vault(user_message, 'hardcoded', response)
        return {'status': 'success', 'model': 'FRIDAY', 'response': response}

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    summarize_old_memory()
    memory = load_recent_memory(20)

    model = route_model(user_message)
    print(f"Routing to model: {model}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    if memory:
        messages.append({"role": "system", "content": f"=== RECENT CONVERSATION HISTORY ===\n{memory}"})
    messages.append({"role": "user", "content": user_message})

    max_turns = 5
    final_content = ""
    last_tool_name = None
    last_tool_output = None

    try:
        for turn in range(max_turns):
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            if turn < max_turns - 1:
                payload["tools"] = TOOLS_DEFINITION

            res = requests.post("http://127.0.0.1:11434/api/chat", json=payload)
            res.raise_for_status()
            assistant_msg = res.json().get("message", {})
            content = assistant_msg.get("content", "").strip()
            tool_calls = assistant_msg.get("tool_calls", [])
            print(f"[DEBUG] Tool calls received: {tool_calls}")
            print(f"[DEBUG] Raw assistant message: {assistant_msg}")

            # Try to parse manual JSON tool calls from text
            manual_tools = []
            if not tool_calls and content:
                # Robust nested JSON extractor
                json_blocks = []
                brace_level = 0
                current_block = ""
                in_string = False
                escape_next = False
                
                for char in content:
                    if escape_next:
                        current_block += char
                        escape_next = False
                        continue
                        
                    if char == '"':
                        in_string = not in_string
                    elif char == '\\':
                        escape_next = True
                        
                    if not in_string:
                        if char == '{':
                            brace_level += 1
                        elif char == '}':
                            brace_level -= 1
                            
                    if brace_level > 0 or (char == '}' and brace_level == 0 and current_block):
                        current_block += char
                        if brace_level == 0:
                            json_blocks.append(current_block)
                            current_block = ""

                for block in json_blocks:
                    try:
                        data = json.loads(block)
                        if isinstance(data, dict) and data.get("name") in [t["function"]["name"] for t in TOOLS_DEFINITION]:
                            manual_tools.append(data)
                    except json.JSONDecodeError:
                        pass

            if tool_calls:
                messages.append(assistant_msg)
                for tc in tool_calls:
                    name = tc["function"]["name"]
                    args = tc["function"]["arguments"]
                    print(f"[Tool] {name}({args})")
                    output = dispatch_tool(name, args)
                    print(f"[Output] {output[:200]}")
                    last_tool_name = name
                    last_tool_output = output
                    messages.append({"role": "tool", "content": output})
                    
                    # Auto-chain type_text after open_app if user message contains typing intent
                    if name == "open_app":
                        type_keywords = ["write", "type", "say", "enter", "input"]
                        if any(kw in user_message.lower() for kw in type_keywords):
                            import re
                            # Extract quoted text or text after write/type/say
                            text_match = re.search(r'(?:write|type|say|enter|input)\s+["\']?([^"\']+)["\']?', user_message.lower())
                            if text_match:
                                import time
                                time.sleep(3)
                                text_to_type = text_match.group(1).strip()
                                type_output = dispatch_tool("type_text", {"text": text_to_type})
                                print(f"[Auto-chain type_text] {type_output}")
                                last_tool_name = "type_text"
                                last_tool_output = type_output
                                messages.append({"role": "tool", "content": type_output})
                continue

            elif manual_tools:
                messages.append(assistant_msg)
                combined_outputs = []
                for tool in manual_tools:
                    name = tool.get("name")
                    args = tool.get("arguments") or tool.get("parameters") or {}
                    print(f"[Tool Manual] {name}({args})")
                    output = dispatch_tool(name, args)
                    print(f"[Output] {output[:200]}")
                    last_tool_name = name
                    last_tool_output = output
                    combined_outputs.append(f"Tool '{name}' output:\n{output}")
                
                messages.append({
                    "role": "user",
                    "content": "\n\n".join(combined_outputs) + "\n\nNow respond to the user in plain text."
                })
                continue

            else:
                final_content = content
                break

        if not final_content:
            final_content = f"Tool '{last_tool_name}' executed. Output:\n{last_tool_output}" if last_tool_output else "[No response]"

        log_to_vault(user_message, model, final_content)
        return {"status": "success", "model": model, "response": final_content}

    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to Ollama at http://127.0.0.1:11434")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Runtime error: {str(e)}")

# ─── UI ───────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FRIDAY Local AI Agent</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #05000c;
            --card-bg: rgba(255, 255, 255, 0.03);
            --card-border: rgba(139, 92, 246, 0.15);
            --primary: #9d4edd;
            --primary-glow: rgba(157, 78, 221, 0.4);
            --text: #ffffff;
            --text-muted: rgba(255, 255, 255, 0.6);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-color);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        header {
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--card-border);
            background: rgba(0,0,0,0.3);
            backdrop-filter: blur(8px);
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
        }
        .logo {
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.05em;
            background: linear-gradient(to right, #a78bfa, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status {
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            color: #10b981;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .status-dot {
            width: 8px; height: 8px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.25); opacity: 0.5; }
            100% { transform: scale(1); opacity: 1; }
        }
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            padding: 2rem;
            overflow-y: auto;
            gap: 1.5rem;
            min-height: 0;
        }
        .message {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            max-width: 85%;
            animation: fadeIn 0.3s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user { align-self: flex-end; }
        .message.assistant { align-self: flex-start; }
        .msg-bubble {
            padding: 1rem 1.25rem;
            border-radius: 1rem;
            font-size: 0.9rem;
            line-height: 1.5;
            white-space: pre-wrap;
        }
        .message.user .msg-bubble {
            background: var(--primary);
            color: white;
            box-shadow: 0 4px 15px var(--primary-glow);
            border-bottom-right-radius: 0.25rem;
        }
        .message.assistant .msg-bubble {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-bottom-left-radius: 0.25rem;
        }
        .msg-meta {
            font-size: 0.7rem;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
        }
        .message.user .msg-meta { text-align: right; }
        pre {
            background: rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.05);
            padding: 0.75rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            margin: 0.5rem 0;
        }
        code {
            font-family: 'JetBrains Mono', monospace;
            background: rgba(255,255,255,0.08);
            padding: 0.15rem 0.3rem;
            border-radius: 0.25rem;
            font-size: 0.85em;
        }
        .input-area {
            padding: 2rem;
            background: rgba(5,0,12,0.8);
            border-top: 1px solid var(--card-border);
            z-index: 10;
        }
        .input-wrapper {
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            display: flex;
            gap: 0.75rem;
        }
        textarea {
            flex: 1;
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 0.75rem;
            color: white;
            font-family: inherit;
            font-size: 0.95rem;
            padding: 1rem 1.25rem;
            resize: none;
            height: 56px;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        textarea:focus {
            border-color: var(--primary);
            box-shadow: 0 0 10px rgba(157,78,221,0.2);
        }
        button {
            padding: 0 1.5rem;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 0.75rem;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
            transition: background 0.2s, transform 0.1s;
            box-shadow: 0 4px 15px var(--primary-glow);
        }
        button:hover { background: #b05fe9; }
        button:active { transform: scale(0.97); }
        .loading-bubble { display: flex; align-items: center; gap: 4px; }
        .dot {
            width: 6px; height: 6px;
            background: var(--text-muted);
            border-radius: 50%;
            animation: dot-pulse 1.4s infinite both;
        }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes dot-pulse {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
            40% { transform: scale(1); opacity: 1; }
        }
        #clearBtn:hover {
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.25);
            color: #ffffff;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">FRIDAY LOCAL AGENT</div>
        <div style="display:flex;align-items:center;gap:1.5rem;">
            <button id="clearBtn" style="background:transparent;border:1px solid rgba(255,255,255,0.1);color:var(--text-muted);font-size:0.75rem;padding:0.35rem 0.75rem;border-radius:0.35rem;box-shadow:none;font-weight:400;">Clear History</button>
            <div class="status"><div class="status-dot"></div><span>AGENT: ONLINE</span></div>
        </div>
    </header>

    <div class="chat-container" id="chat">
        <div class="message assistant">
            <div class="msg-bubble">Hello. I am FRIDAY, your local AI Assistant. I can answer queries, analyze code, open apps, read/write files, search the web, take screenshots, and run system tasks. How can I help you?</div>
            <div class="msg-meta">FRIDAY System</div>
        </div>
    </div>

    <div class="input-area">
        <div class="input-wrapper">
            <textarea id="userInput" placeholder="Type your instruction... (Enter to send, Shift+Enter for newline)"></textarea>
            <button id="sendBtn">SEND</button>
        </div>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const clearBtn = document.getElementById('clearBtn');

        function scrollToBottom(force = false) {
            const isNearBottom = chat.scrollTop + chat.clientHeight >= chat.scrollHeight - 100;
            if (force || isNearBottom) {
                setTimeout(() => { chat.scrollTop = chat.scrollHeight; }, 50);
            }
        }

        let chatHistory = [];
        try {
            const saved = localStorage.getItem('friday_chat_history');
            if (saved) {
                chatHistory = JSON.parse(saved);
                if (chatHistory.length > 0) {
                    chat.innerHTML = '';
                    chatHistory.forEach((msg, idx) => {
                        appendMessageToDOM(msg.sender, msg.text, msg.meta, idx === chatHistory.length - 1);
                    });
                }
            }
        } catch (e) { console.error('Failed to load chat history:', e); }

        function formatMarkdown(text) {
            let html = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            html = html.replace(/```(\\w*)\\n([\\s\\S]*?)```/g, (_, lang, code) => `<pre><code>${code.trim()}</code></pre>`);
            html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
            html = html.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
            return html;
        }

        function appendMessageToDOM(sender, text, meta, forceScroll = false) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${sender}`;
            const bubble = document.createElement('div');
            bubble.className = 'msg-bubble';
            if (sender === 'assistant') {
                bubble.innerHTML = formatMarkdown(text);
            } else {
                bubble.textContent = text;
            }
            const metaDiv = document.createElement('div');
            metaDiv.className = 'msg-meta';
            metaDiv.textContent = meta;
            msgDiv.appendChild(bubble);
            msgDiv.appendChild(metaDiv);

            if (sender === 'assistant') {
                const copyBtn = document.createElement('button');
                copyBtn.textContent = 'Copy';
                copyBtn.style.background = 'transparent';
                copyBtn.style.border = 'none';
                copyBtn.style.color = 'rgba(255, 255, 255, 0.4)';
                copyBtn.style.fontSize = '0.7rem';
                copyBtn.style.cursor = 'pointer';
                copyBtn.style.padding = '0';
                copyBtn.style.marginTop = '0.25rem';
                copyBtn.style.alignSelf = 'flex-start';
                copyBtn.style.boxShadow = 'none';
                copyBtn.style.transition = 'color 0.2s';
                copyBtn.addEventListener('mouseover', () => copyBtn.style.color = '#ffffff');
                copyBtn.addEventListener('mouseout', () => copyBtn.style.color = 'rgba(255, 255, 255, 0.4)');
                copyBtn.addEventListener('click', () => {
                    navigator.clipboard.writeText(text).then(() => {
                        copyBtn.textContent = 'Copied!';
                        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
                    }).catch(err => {
                        console.error('Failed to copy: ', err);
                    });
                });
                msgDiv.appendChild(copyBtn);
            }

            chat.appendChild(msgDiv);
            scrollToBottom(forceScroll);
            return msgDiv;
        }

        function appendMessage(sender, text, meta) {
            appendMessageToDOM(sender, text, meta, sender === 'user');
            chatHistory.push({ sender, text, meta });
            try { localStorage.setItem('friday_chat_history', JSON.stringify(chatHistory)); } catch (e) {}
        }

        clearBtn.addEventListener('click', () => {
            if (confirm('Clear chat history?')) {
                chatHistory = [];
                localStorage.removeItem('friday_chat_history');
                chat.innerHTML = `
                    <div class="message assistant">
                        <div class="msg-bubble">Hello. I am FRIDAY, your local AI Assistant. I can answer queries, analyze code, open apps, read/write files, search the web, take screenshots, and run system tasks. How can I help you?</div>
                        <div class="msg-meta">FRIDAY System</div>
                    </div>`;
            }
        });

        async function handleSend() {
            const text = userInput.value.trim();
            if (!text) return;

            if (text.startsWith('/improve ')) {
                const taskText = text.substring(9).trim();
                appendMessage('user', text, 'YOU');
                userInput.value = '';

                const loadDiv = document.createElement('div');
                loadDiv.className = 'message assistant';
                loadDiv.innerHTML = `<div class="msg-bubble"><div class="loading-bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div><div class="msg-meta">FRIDAY (Thinking...)</div>`;
                chat.appendChild(loadDiv);
                scrollToBottom(true);

                try {
                    const response = await fetch('/improve', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ task: taskText })
                    });
                    if (chat.contains(loadDiv)) chat.removeChild(loadDiv);
                    if (response.ok) {
                        const data = await response.json();
                        appendMessage('assistant', data.response, `FRIDAY (Self-Improvement)`);
                    } else {
                        let errMsg = 'Failed to apply improvements';
                        try { const err = await response.json(); errMsg = err.detail || errMsg; } catch (_) {}
                        appendMessage('assistant', `Error: ${errMsg}`, 'System Error');
                    }
                } catch (e) {
                    if (chat.contains(loadDiv)) chat.removeChild(loadDiv);
                    appendMessage('assistant', `Failed to connect to backend: ${e.message}`, 'Network Error');
                }
                return;
            }

            appendMessage('user', text, 'YOU');
            userInput.value = '';

            const loadDiv = document.createElement('div');
            loadDiv.className = 'message assistant';
            loadDiv.innerHTML = `<div class="msg-bubble"><div class="loading-bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div><div class="msg-meta">FRIDAY (Thinking...)</div>`;
            chat.appendChild(loadDiv);
            scrollToBottom(true);

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                if (chat.contains(loadDiv)) chat.removeChild(loadDiv);
                if (response.ok) {
                    const data = await response.json();
                    appendMessage('assistant', data.response, `FRIDAY (${data.model})`);
                } else {
                    let errMsg = 'Failed to generate response';
                    try { const err = await response.json(); errMsg = err.detail || errMsg; } catch (_) {}
                    appendMessage('assistant', `Error: ${errMsg}`, 'System Error');
                }
            } catch (e) {
                if (chat.contains(loadDiv)) chat.removeChild(loadDiv);
                appendMessage('assistant', `Failed to connect to backend: ${e.message}`, 'Network Error');
            }
        }

        sendBtn.addEventListener('click', handleSend);
        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
        });
    </script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
