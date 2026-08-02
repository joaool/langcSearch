import contextvars
import os
from contextlib import contextmanager

import requests
from langchain_core.tools import tool

# LangGraph executes tool calls on a worker thread from langchain_core's internal
# thread pool, not the caller's thread. That pool copies contextvars into the
# worker thread (unlike thread-local state), so a ContextVar is what lets callers
# (e.g. the Streamlit UI) capture calls made during a specific agent invocation.
_current_log: contextvars.ContextVar[list[dict] | None] = contextvars.ContextVar(
    "_serper_tool_log", default=None
)


@contextmanager
def capture_tool_calls():
    """Yield a list that fills up with {url, payload} for every Serper call made
    while inside this block, including calls made by the agent on its own worker
    thread. No-ops (yields nothing useful) for calls made outside this context."""
    log: list[dict] = []
    token = _current_log.set(log)
    try:
        yield log
    finally:
        _current_log.reset(token)


def _log_tool_call(url: str, payload: dict) -> None:
    log = _current_log.get()
    if log is not None:
        log.append({"url": url, "payload": payload})


@tool
def serper_search_tool(
    search_type: str, 
    query: str, 
    site: str = None, 
    filetype: str = None, 
    gl: str = "us", 
    hl: str = "en",
    time_filter: str = None,
    num: int = 10,
) -> dict:
    """Search Google for real-time information and breaking news using Serper.
     Args:
        search_type: The endpoint to use ('search', 'news', 'images', 'places', 'shopping', 'scholar'). MANDATORY.
        query: The raw keywords to search for.
        site: Optional. Restrict search results to a specific domain (e.g., 'lowcode.agency').
        filetype: Optional. Restrict results to a specific file extension (e.g., 'pdf', 'docx').
        gl: Optional. Two-letter country code (default: 'us').
        hl: Optional. Two-letter language code (default: 'en').
        time_filter: Optional. Temporal restrictions using Google format (e.g., 'qdr:d' for past day, 'qdr:w' for past week).
        num: Optional. The maximum number of results to return (integer between 10 and 100, default is 10).    
    """
    url = f"https://google.serper.dev/{search_type}"
    
    if site:
        query = f"{query} site:{site}"
    if filetype:
        query = f"{query} filetype:{filetype}"   

    payload = {
        "q": query,
        "gl": gl,
        "hl": hl,
        "num": num
    }
    if time_filter:
        payload["tbs"] = time_filter

    _log_tool_call(url, payload)

    print(f"Making request to {url} with payload: {payload}")
    headers = {'X-API-KEY': os.getenv("SERPER_API_KEY"), 'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "message": response.text}
        return response.json()
    except Exception as e:
        return {"error": "Request failed", "details": str(e)}
