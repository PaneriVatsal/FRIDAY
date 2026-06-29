"""
friday.tools.registry — Full TOOLS_DEFINITION list.
Copied exactly from existing main.py lines 898-1195.
"""

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
                    "filename": {"type": "string", "description": "Optional filename for the screenshot (without path). Auto-generated if not provided."},
                    "focus_window": {"type": "string", "description": "Optional app or window name to focus before taking screenshot (e.g. 'chrome', 'obsidian', 'notepad')."}
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
    },
    {
        "type": "function",
        "function": {
            "name": "obsidian_write_note",
            "description": "Create or overwrite a markdown note in the vault.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Note title (filename without .md)"},
                    "content": {"type": "string", "description": "Markdown content of the note"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obsidian_read_note",
            "description": "Read a note from the vault by title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Note title (filename without .md)"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obsidian_search_notes",
            "description": "Search notes in the vault by keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obsidian_list_notes",
            "description": "List all notes in the vault.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
                "name": "get_system_uptime",
                "description": "This tool returns the current system uptime by querying the last boot time using PowerShell.",
                "parameters": {}
        }
    }
]
