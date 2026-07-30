"""Shared agent construction, used by both the Streamlit UI (langcSearch.py) and the API (api.py)."""
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from serper_tool import serper_search_tool

tools = [serper_search_tool]
model = ChatOpenAI(model="gpt-4o", temperature=0)

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
