# serper_tool.py

A LangChain `@tool`-decorated function, `serper_search_tool`, that wraps the [Serper.dev](https://serper.dev) Google Search API so it can be called directly in Python or handed to a LangChain/LangGraph agent as a tool.

## What it does

- Builds a request to `https://google.serper.dev/{search_type}` (e.g. `.../search`, `.../news`, `.../images`).
- Appends `site:` and `filetype:` operators to the query string when provided.
- Sends the request with your `SERPER_API_KEY` (read from the environment) and returns the parsed JSON response.
- Logs every request's URL and payload into `st.session_state.tool_logs`, so a Streamlit app can display which searches the agent performed (see [langcSearch.py](langcSearch.py) for an example consumer).

## Requirements

- `SERPER_API_KEY` set in the environment (e.g. via a `.env` file loaded with `python-dotenv`).
- A Streamlit app context — `st.session_state` is used unconditionally, so calling this tool outside of a running Streamlit script will raise an error. See [Standalone / non-Streamlit use](#standalone--non-streamlit-use) below if you need it elsewhere.

## Function signature

```python
serper_search_tool(
    search_type: str,          # required
    query: str,                # required
    site: str = None,
    filetype: str = None,
    gl: str = "us",
    hl: str = "en",
    time_filter: str = None,
    num: int = 10,
) -> dict
```

| Parameter     | Type | Required | Description                                                                    |
|---------------|------|----------|----------------------------------------------------------------------------------|
| `search_type` | str  | Yes      | Serper endpoint to hit: `search`, `news`, `images`, `places`, `shopping`, `scholar`. |
| `query`       | str  | Yes      | Raw search keywords.                                                              |
| `site`        | str  | No       | Restricts results to a domain by appending `site:<domain>` to the query.          |
| `filetype`    | str  | No       | Restricts results to a file extension by appending `filetype:<ext>` to the query. |
| `gl`          | str  | No       | Two-letter country code (default `"us"`).                                         |
| `hl`          | str  | No       | Two-letter language code (default `"en"`).                                        |
| `time_filter` | str  | No       | Google `tbs` time filter, e.g. `qdr:h` (past hour), `qdr:d` (past day), `qdr:w` (past week), `qdr:m` (past month), `qdr:y` (past year). |
| `num`         | int  | No       | Number of results to request (default `10`).                                      |

## Return value

Returns the Serper.dev JSON response as a `dict`, e.g. for `search_type="search"`:

```json
{
  "searchParameters": { "q": "...", "gl": "us", "hl": "en", "num": 10, "type": "search" },
  "organic": [
    { "title": "...", "link": "...", "snippet": "...", "position": 1 }
  ]
}
```

On failure it returns an error dict instead of raising:

- `{"error": "HTTP <status>", "message": "<response body>"}` for non-200 responses.
- `{"error": "Request failed", "details": "<exception message>"}` for network/connection errors.

## Usage as an agent tool

```python
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from serper_tool import serper_search_tool

agent = create_react_agent(ChatOpenAI(model="gpt-4o"), [serper_search_tool])
```

The agent reads the tool's docstring to decide when/how to call it, so `search_type` and `query` must always be supplied by the model — `search_type` has no default and will fail validation if omitted.

## Usage called directly

```python
from serper_tool import serper_search_tool

# Recent news from the past day
results = serper_search_tool.invoke({
    "query": "AI business use cases",
    "search_type": "news",
    "time_filter": "qdr:d",
})

# PDF documents on a specific site
results = serper_search_tool.invoke({
    "query": "manual Sony WH-1000XM4",
    "search_type": "search",
    "filetype": "pdf",
    "num": 1,
})

# Site-restricted French-language search
results = serper_search_tool.invoke({
    "query": '"liste des exposants" OR "exhibitors list"',
    "search_type": "search",
    "site": "expoprotection.com",
    "filetype": "pdf",
    "gl": "fr",
})
```

Because it's a LangChain `@tool`, invoke it with `.invoke({...})` rather than calling it as a plain function.

## Standalone / non-Streamlit use

The current implementation calls `st.session_state` unconditionally to log requests, so it only runs inside a live Streamlit session. To use it in a plain script or notebook, either:

- Run it under `streamlit run your_script.py`, or
- Remove/guard the `st.session_state` logging block (lines 35–51 in [serper_tool.py](serper_tool.py)) if you don't need the UI-visible request log.
