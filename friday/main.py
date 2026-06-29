"""
friday.main — FastAPI app with POST /chat, POST /improve, and GET / for HTML UI.
Entry point: python friday/main.py
"""

import os
import sys
import json
import re
import subprocess
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to path so friday package is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from friday.agent import FridayAgent
from friday.memory.vault_log import log_to_vault

app = FastAPI(title="FRIDAY Python Agent Backend")

# Screenshot static mount
SCREENSHOT_DIR = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=SCREENSHOT_DIR), name="screenshots")

# Agent instance
agent = FridayAgent()


class ChatRequest(BaseModel):
    message: str


class ImproveRequest(BaseModel):
    task: str


# ─── CHAT ENDPOINT ────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    user_message = req.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Capability triggers — hardcoded response
    capability_triggers = ['what can you do', 'what features', 'what tools', 'capabilities', 'what do you do', 'what can you']
    if any(trigger in user_message.lower() for trigger in capability_triggers):
        response = 'Here is what I can do:\n\n- run_command: Run any shell/PowerShell command\n- open_app: Open applications\n- write_file / read_file: Read and write files\n- web_search: Search the web\n- fetch_url: Read content from any URL\n- get_weather: Real-time weather\n- take_screenshot: Capture your screen\n- get_battery_percentage: Check battery level\n- volume_control / get_volume: Control volume\n- remember / recall: Save and retrieve personal facts\n- type_text, press_hotkey, click_mouse: Control keyboard and mouse\n- Obsidian: read, write, search notes'
        log_to_vault(user_message, 'hardcoded', response)
        return {'status': 'success', 'model': 'FRIDAY', 'response': response}

    try:
        response = agent.chat(user_message)
        log_to_vault(user_message, "friday", response)
        return {"status": "success", "model": "FRIDAY", "response": response}
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to Ollama")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Runtime error: {str(e)}")


# ─── IMPROVE ENDPOINT (copied from existing main.py) ─────────────────────────

def _test_syntax(code: str, result_queue):
    import ast
    try:
        ast.parse(code)
        result_queue.put("ok")
    except SyntaxError as e:
        result_queue.put(f"syntax_error:{e}")


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


@app.post("/improve")
async def improve_endpoint(req: ImproveRequest):
    task = req.task.strip()
    if not task:
        raise HTTPException(status_code=400, detail="Task cannot be empty")

    try:
        import datetime
        import glob
        import multiprocessing
        import ast

        # 1. Classify risk level
        risk_keywords_high = ['orchestrator', 'chat_endpoint', 'improve_endpoint', 'dispatch_tool', 'summarize', 'vault', 'memory']
        risk_keywords_medium = ['existing', 'modify', 'update', 'change', 'edit', 'replace', 'routing', 'system_prompt']

        task_lower = task.lower()
        if any(kw in task_lower for kw in risk_keywords_high):
            risk = "high"
        elif any(kw in task_lower for kw in risk_keywords_medium):
            risk = "medium"
        else:
            risk = "low"

        print(f"[Improve] Risk level: {risk} for task: {task}")

        if risk == "high":
            return {"status": "blocked", "response": f"Task classified as HIGH RISK. This would modify core systems. Manual edit required.\nTask: {task}"}

        # 2. Backup
        backup_dir = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"main_backup_{timestamp}.py"
        backup_path = os.path.join(backup_dir, backup_filename)
        current_path = os.path.join(PROJECT_ROOT, "main.py")

        with open(current_path, "r", encoding="utf-8") as f:
            current_code = f.read()
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(current_code)

        backup_files = sorted(glob.glob(os.path.join(backup_dir, "main_backup_*.py")), key=os.path.getmtime)
        if len(backup_files) > 5:
            for old in backup_files[:-5]:
                try: os.remove(old)
                except: pass

        # 3. Generate function code
        skills_info = load_skills()
        system_msg_func = (
            "You are a master python programmer. Write ONLY the Python function code (using def ...) that implements the requested capability.\n"
            "CRITICAL: Never mix single and double quotes inside f-strings. Import needed modules inside the function.\n"
            "CRITICAL: Do NOT write the entire file. Output only code inside a ```python ... ``` block."
        )
        payload_func = {
            "model": "qwen2.5-coder:latest",
            "messages": [
                {"role": "system", "content": system_msg_func},
                {"role": "user", "content": f"Task: {task}\n\nSkills:\n{skills_info}"}
            ],
            "stream": False,
            "options": {"num_predict": -1}
        }
        res_func = requests.post("http://127.0.0.1:11434/api/chat", json=payload_func, timeout=300)
        res_func.raise_for_status()
        assistant_content_func = res_func.json().get("message", {}).get("content", "")

        code_match = re.search(r'```python\s*([\s\S]*?)```', assistant_content_func) or re.search(r'```\s*([\s\S]*?)```', assistant_content_func)
        if code_match:
            function_code = code_match.group(1).strip()
        elif "def " in assistant_content_func:
            function_code = assistant_content_func[assistant_content_func.find("def "):].strip()
        else:
            raise Exception("No valid function found in LLM response.")

        function_code = function_code.replace("```python", "").replace("```", "").strip()

        name_match = re.search(r'def\s+([a-zA-Z0-9_]+)', function_code)
        extracted_tool_name = name_match.group(1) if name_match else ""
        cleaned_lines = [l for l in function_code.splitlines() if not l.strip().startswith("# Example") and not (extracted_tool_name and re.match(rf'^{extracted_tool_name}\(', l.strip()))]
        function_code = "\n".join(cleaned_lines).strip()

        if len(function_code) < 50:
            raise Exception("Generated function code is too short.")

        # 4. Timeout test using multiprocessing
        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=_test_syntax, args=(function_code, result_queue))
        p.start()
        p.join(timeout=10)
        if p.is_alive():
            p.terminate()
            raise Exception("Function code timed out during syntax check.")
        result = result_queue.get() if not result_queue.empty() else "unknown"
        if result != "ok":
            raise Exception(f"Syntax error in generated code: {result}")

        # 5. Generate JSON tool definition
        system_msg_json = (
            "Write ONLY the JSON entry for TOOLS_DEFINITION matching format: {'type':'function','function':{'name':'...','description':'...','parameters':{...}}}.\n"
            "Output raw JSON inside a ```json ... ``` block only."
        )
        payload_json = {
            "model": "qwen2.5-coder:latest",
            "messages": [
                {"role": "system", "content": system_msg_json},
                {"role": "user", "content": f"Task: {task}\n\nFunction:\n{function_code}"}
            ],
            "stream": False,
            "options": {"num_predict": -1}
        }
        res_json = requests.post("http://127.0.0.1:11434/api/chat", json=payload_json, timeout=300)
        res_json.raise_for_status()
        assistant_content_json = res_json.json().get("message", {}).get("content", "")

        json_match = re.search(r'```json\s*([\s\S]*?)```', assistant_content_json) or re.search(r'```\s*([\s\S]*?)```', assistant_content_json)
        if json_match:
            json_entry_str = json_match.group(1).strip()
        elif "{" in assistant_content_json:
            json_entry_str = assistant_content_json[assistant_content_json.find("{"):assistant_content_json.rfind("}")+1].strip()
        else:
            raise Exception("No valid JSON found in LLM response.")

        try:
            def_data = json.loads(json_entry_str)
            tool_name = def_data["function"]["name"]
        except Exception:
            tool_name = extracted_tool_name
            if not tool_name:
                raise Exception("Could not determine tool name.")

        # 6. Inject into main.py
        TOOL_DISPATCHER_MARKER = "# " + "─── TOOL DISPATCHER ───"
        modified_code = current_code.replace(TOOL_DISPATCHER_MARKER, function_code + '\n\n' + TOOL_DISPATCHER_MARKER, 1)

        marker_error = "    " + 'return f"[ERROR] Unknown tool: {name}"'
        if marker_error not in modified_code:
            raise Exception("Dispatcher marker not found.")
        dispatch_case = f"    elif name == \"{tool_name}\":\n        return {tool_name}(**{{k: arguments.get(k) for k in arguments}})\n"
        modified_code = modified_code.replace(marker_error, f"{dispatch_case}{marker_error}", 1)

        marker_tools_end = "]\n\n" + 'SYSTEM_PROMPT = """You are FRIDAY'
        if marker_tools_end not in modified_code:
            marker_tools_end = "]\r\n\r\n" + 'SYSTEM_PROMPT = """You are FRIDAY'
        if marker_tools_end not in modified_code:
            raise Exception("TOOLS_DEFINITION end marker not found.")

        try:
            parsed_json = json.loads(json_entry_str)
            formatted_json = json.dumps(parsed_json, indent=8)
            lines = formatted_json.splitlines()
            formatted_json = "\n".join([lines[0]] + ["    " + l for l in lines[1:]])
        except Exception:
            formatted_json = json_entry_str

        modified_code = modified_code.replace(marker_tools_end, f",\n    {formatted_json}\n" + marker_tools_end, 1)

        # 7. Final AST check before writing
        try:
            ast.parse(modified_code)
        except SyntaxError as e:
            raise Exception(f"Syntax error in modified file: {e}")

        with open(current_path, "w", encoding="utf-8") as f:
            f.write(modified_code)

        # 8. Log
        improvements_path = r"C:\Users\LP082W\.gemini\antigravity\scratch\friday-vault\memory\improvements.md"
        os.makedirs(os.path.dirname(improvements_path), exist_ok=True)
        with open(improvements_path, "a", encoding="utf-8") as f:
            f.write(f"### {timestamp}\n- Task: {task}\n- Risk: {risk}\n- Status: Success\n- Backup: {backup_filename}\n\n")

        return {"status": "success", "response": f"[{risk.upper()} RISK] Successfully implemented: '{task}'. Backup: {backup_filename}."}

    except Exception as e:
        # Rollback
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                original = f.read()
            with open(current_path, "w", encoding="utf-8") as f:
                f.write(original)
            print(f"[Improve] Rolled back to {backup_filename}")
        except Exception as rollback_err:
            print(f"[Improve] Rollback failed: {rollback_err}")
        return {"status": "failure", "response": f"Failed: {str(e)}. Rolled back to {backup_filename}."}


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
            html = html.replace(/\\[IMG\\](\\S+)/g, '<img src="$1" style="max-width:100%;border-radius:0.5rem;margin-top:0.5rem;display:block;" />');
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
    uvicorn.run("friday.main:app", host="127.0.0.1", port=8000, reload=False)
