# OSINT AI Research Agent

A Streamlit chat app that pairs a LangGraph ReAct agent (GPT-4o via `langchain-openai`) with a [Serper.dev](https://serper.dev) Google Search tool, so the agent can look up real-time web, news, images, places, shopping, and scholar results while answering research questions.

## How it works

- [langcSearch.py](langcSearch.py) — Streamlit UI. Loads env vars, builds a `create_react_agent` (LangGraph) with GPT-4o and the search tool, and renders the chat plus a "Tool Executions" panel showing every Serper request the agent made.
- [serper_tool.py](serper_tool.py) — the `serper_search_tool` LangChain tool. Wraps the Serper.dev REST API (`https://google.serper.dev/{search_type}`) and logs each call's URL/payload into `st.session_state.tool_logs` for display in the UI.

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
   ```

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

## Manual search (bypass the AI agent)

The sidebar has a "🔧 Manual Search" form that calls `serper_search_tool` directly with parameters you set (search type, query, site, filetype, gl, hl, time filter, num results) and shows the raw JSON response — no OpenAI call involved. Useful for testing the Serper integration or running a specific query without going through the chat agent.

## Notes

- Every Serper call the agent makes during a turn is recorded and shown in an expandable "🛠️ Tool Executions Detected" panel under the assistant's reply, so you can audit exactly what was searched.
- Chat history persists across reruns via `st.session_state.messages`, including each message's associated tool logs.
- The agent model is hardcoded to `gpt-4o` with `temperature=0` in [langcSearch.py](langcSearch.py#L13); change it there if you want a different model or more creative responses.
