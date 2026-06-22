Write-Host "Starting Claude Code locally with Qwen 2.5 Coder 7B via Ollama..." -ForegroundColor Green

$env:ANTHROPIC_BASE_URL = "http://127.0.0.1:11434/v1"
$env:ANTHROPIC_API_KEY = "ollama"
$env:ANTHROPIC_DEFAULT_MODEL = "qwen2.5-coder:7b"

# Explicitly use the model flag to avoid issues with stored config
claude --model qwen2.5-coder:7b
