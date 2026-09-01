# Scientific Collaboration Network Analyzer

## SCNA Assistant (local Ollama)

SCNA Assistant is a floating, role-safe assistant available after login. It sends only the records that the current account is permitted to view to a local Ollama model; no SCNA records are sent to a paid external AI provider.

1. Install [Ollama](https://ollama.com/download).
2. In a terminal, run `ollama pull qwen2.5:0.5b` and then `ollama serve` (the desktop app may already run the service).
3. Start the FastAPI backend normally. Its local defaults are in `Backend/.env`.

Environment settings:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:0.5b
OLLAMA_TIMEOUT_SECONDS=8
```

For Docker, run `docker compose up --build`. The compose file starts Ollama and downloads the configured model once into the persistent `ollama_models` volume. The backend stays available if the model service is still starting; the Assistant will display a friendly temporary-unavailable message.

Role scope: System Admin sees system-level records; Institution Admin sees only their institution; Researchers and other regular users see their own records; Reviewers see only assigned reviews. The endpoint is `POST /assistant/chat` and requires a valid JWT.
