"""Shared agent construction, used by both the Streamlit UI (langcSearch.py) and the API (api.py)."""
import os

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from serper_tool import serper_search_tool

tools = [serper_search_tool]

# Routed through OpenRouter's OpenAI-compatible API, so the LLM can be swapped
# via LLM_MODEL (e.g. "openai/gpt-4o", "anthropic/claude-sonnet-5") without code changes.
model = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "openai/gpt-4o"),
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://github.com/joaocarloscoliveira/langchainSearch",
        "X-Title": "langchainSearch",
    },
)

system_prompt = (
    "You are an advanced market research and OSINT AI agent. "
    "Use your web search tool intelligently by specifying domains."
)

# create_react_agent creates a fully compilable state graph automatically
agent_executor = create_react_agent(
    model,
    tools,
    prompt=system_prompt  # LangGraph now expects 'prompt' for string instructions
)
