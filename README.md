# OSINT AI Research Agent

A Streamlit chat app that pairs a LangGraph ReAct agent (GPT-4o via `langchain-openai`) with a [Serper.dev](https://serper.dev) Google Search tool, so the agent can look up real-time web, news, images, places, shopping, and scholar results while answering research questions.

## How it works

- [agent_core.py](agent_core.py) — builds the GPT-4o + LangGraph `create_react_agent`. Shared by both `langcSearch.py` and `api.py` so the agent is defined in exactly one place.
- [langcSearch.py](langcSearch.py) — Streamlit UI. Password-gated; renders the chat plus a "Tool Executions" panel showing every Serper request the agent made, and a Manual Search sidebar that bypasses the agent.
- [api.py](api.py) — FastAPI service exposing the same two capabilities as the UI over HTTP (see [API](#api) below).
- [serper_tool.py](serper_tool.py) — the `serper_search_tool` LangChain tool. Wraps the Serper.dev REST API (`https://google.serper.dev/{search_type}`). When run inside Streamlit it also logs each call's URL/payload into `st.session_state.tool_logs` for the UI's tool-log panel; it no-ops that logging when called from the API, where there's no Streamlit session.

## Prerequisites

- Python 3.10+
- An OpenAI API key ([platform.openai.com](https://platform.openai.com))
- A Serper.dev API key ([serper.dev](https://serper.dev) — free tier available)

## Setup

1. **Create/activate a virtual environment** (a `.venv` already exists in this repo):

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**

   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure API keys** — create a `.env` file in the project root (it's already git-ignored):

   ```
   SERPER_API_KEY=your_serper_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   APP_PASSWORD=choose_a_password
   API_KEY=choose_a_separate_api_key
   ```

   `APP_PASSWORD` gates the Streamlit UI (see [Password gate](#password-gate) below); `API_KEY` gates the REST API (see [API](#api) below). They're deliberately separate secrets for separate consumers.

   > A `.env` already exists in this project with live keys. Since it was committed to the working tree, treat those keys as exposed and consider rotating them at serper.dev and platform.openai.com before sharing this repo or its history with anyone.

## Running the app

```powershell
streamlit run langcSearch.py
```

This opens the chat UI in your browser (default: http://localhost:8501). Type a research question in the chat box — the agent decides when and how to call the search tool.

## Using the search tool directly

`serper_search_tool` can also be invoked standalone (see the commented examples at the bottom of [langcSearch.py](langcSearch.py)):

```python
from serper_tool import serper_search_tool

results = serper_search_tool.invoke({
    "query": "AI business use cases",
    "search_type": "news",
    "time_filter": "qdr:d",   # past day
})
```

### Tool parameters

| Parameter     | Type | Required | Description                                                                 |
|---------------|------|----------|-------------------------------------------------------------------------------|
| `search_type` | str  | Yes      | Serper endpoint: `search`, `news`, `images`, `places`, `shopping`, `scholar`. |
| `query`       | str  | Yes      | Raw search keywords.                                                          |
| `site`        | str  | No       | Restrict results to a domain, e.g. `lowcode.agency`.                          |
| `filetype`    | str  | No       | Restrict results to a file extension, e.g. `pdf`.                             |
| `gl`          | str  | No       | Two-letter country code (default `us`).                                       |
| `hl`          | str  | No       | Two-letter language code (default `en`).                                      |
| `time_filter` | str  | No       | Google `tbs` time filter, e.g. `qdr:d` (past day), `qdr:w` (past week).       |
| `num`         | int  | No       | Max results to return (default `10`).                                         |

Note: `search_type` is mandatory even though it's not the first positional field — omitting it will raise a validation error from the tool schema.

## Password gate

The whole app sits behind a single shared password read from the `APP_PASSWORD` environment variable — nothing loads (agent, sidebar, chat) until it's entered correctly in the login screen. This exists because the app is often deployed with a public URL, and every chat message or manual search burns billed OpenAI/Serper API calls. It's session-based (`st.session_state.authenticated`) and stored in plaintext in the env var — fine for keeping casual visitors out, not a substitute for real auth if you need per-user accounts or stronger security.

## Manual search (bypass the AI agent)

The sidebar has a "🔧 Manual Search" form that calls `serper_search_tool` directly with parameters you set (search type, query, site, filetype, gl, hl, time filter, num results) and shows the raw JSON response — no OpenAI call involved. Useful for testing the Serper integration or running a specific query without going through the chat agent.

## API

`api.py` exposes the same two capabilities as the UI over HTTP, so other systems can call this agent programmatically. Every endpoint requires an `X-API-Key` header matching the `API_KEY` env var.

Run locally with:

```powershell
uvicorn api:app --reload
```

### `POST /search/ai` — equivalent to the chat panel

The agent decides whether and how to search.

```bash
curl -X POST http://localhost:8000/search/ai \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"query": "What is today'\''s top AI business news?"}'
```

Response:

```json
{
  "answer": "...",
  "structured_answer": null,
  "tool_calls": [
    {"tool": "serper_search_tool", "args": {"search_type": "news", "query": "AI business news", "time_filter": "qdr:d"}}
  ]
}
```

#### Requesting a specific JSON shape

Pass `response_schema` — a [JSON Schema](https://json-schema.org/) object — and the endpoint runs a second pass that formats the agent's findings into that exact shape, returned as `structured_answer` (the plain-text `answer` is still included too). The schema **must have a top-level `"title"`** (used as the underlying function name for OpenAI's structured outputs) and, for strict enforcement, every property listed in `"required"` with `"additionalProperties": false`.

```bash
curl -X POST http://localhost:8000/search/ai \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "query": "What is today'\''s top AI business news?",
    "response_schema": {
      "title": "AINewsSummary",
      "type": "object",
      "properties": {
        "headline": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]}
      },
      "required": ["headline", "key_points", "sentiment"],
      "additionalProperties": false
    }
  }'
```

```json
{
  "structured_answer": {
    "headline": "...",
    "key_points": ["...", "..."],
    "sentiment": "neutral"
  }
}
```

### `POST /search/direct` — equivalent to the Manual Search panel

Calls `serper_search_tool` directly, bypassing the agent. Body mirrors the [tool parameters](#tool-parameters) above.

```bash
curl -X POST http://localhost:8000/search/direct \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"search_type": "search", "query": "AI business use cases", "num": 5}'
```

Returns the raw Serper JSON response.

### Deploying the API

The API is meant to run as its own service, separate from the Streamlit UI deployment — see [Dockerfile.api](Dockerfile.api) (built with `uvicorn api:app --host 0.0.0.0 --port $PORT`, same pattern as the UI's [Dockerfile](Dockerfile)). On Railway, deploy it as a second service from this same repo pointing at `Dockerfile.api`, with `OPENAI_API_KEY`, `SERPER_API_KEY`, and `API_KEY` set in its own Variables tab.

## Notes

- Every Serper call the agent makes during a turn is recorded and shown in an expandable "🛠️ Tool Executions Detected" panel under the assistant's reply, so you can audit exactly what was searched.
- Chat history persists across reruns via `st.session_state.messages`, including each message's associated tool logs.
- The agent model is hardcoded to `gpt-4o` with `temperature=0` in [agent_core.py](agent_core.py); change it there if you want a different model or more creative responses — it applies to both the UI and the API since they share this module.
