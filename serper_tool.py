import os
import requests
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
from langchain_core.tools import tool


def _log_tool_call(url: str, payload: dict) -> None:
    """Record the request in Streamlit's session state, when running inside a Streamlit app.
    No-ops when called from a plain Python process (e.g. the API), which has no session state."""
    if get_script_run_ctx() is None:
        return
    if "tool_logs" not in st.session_state:
        st.session_state.tool_logs = []
    st.session_state.tool_logs.append({"url": url, "payload": payload})


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
