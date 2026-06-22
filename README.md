# FRIDAY — Local AI Assistant

> A locally-running Jarvis-style AI assistant with full Windows PC control. No cloud. No subscriptions. Just your hardware.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-green)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-purple)
![Windows](https://img.shields.io/badge/Windows-11-lightgrey)

## Features
- Open apps, type text, click mouse, take screenshots
- Web search, fetch URLs, real-time weather
- Read/write files, run shell commands
- Volume control, battery status
- Persistent memory (user facts + conversation history)
- Self-improvement via `/improve` endpoint
- Dark themed chat UI

## Stack
- **Backend**: FastAPI (port 8000)
- **LLM**: Ollama (port 11434)
- **Models**: `qwen2.5-coder` for tools, `llama3.1` for chat (or `gemma4:e4b`)

## Setup
```bash
pip install fastapi uvicorn requests pyautogui ddgs pydantic
ollama pull qwen2.5-coder
ollama pull llama3.1
python main.py
```
Open http://127.0.0.1:8000

## Tools
| Tool | Description |
|------|-------------|
| run_command | Execute shell/PowerShell commands |
| open_app | Launch any application |
| write_file / read_file | File access |
| web_search | DuckDuckGo search |
| get_weather | Real-time weather via Open-Meteo |
| take_screenshot | Capture screen |
| remember / recall | Persistent user facts |
| volume_control | System volume control |
| type_text / press_hotkey / click_mouse | PC automation |
