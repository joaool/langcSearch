import time
import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
import requests
from dotenv import load_dotenv  # <-- Add this import
# Load environment variables from your .env file
load_dotenv()

# --- 1. Define the Custom Tool 
@tool
def serper_search_tool(
    search_type: str, 
    query: str, 
    site: str = None, 
    filetype: str = None, 
    gl: str = "us", 
    hl: str = "en",
    time_filter: str = None,
    num: int = 10,  # Add the result limit here (default to 10)
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
     # 1. Dynamically build the URL based on search_type
    url = f"https://google.serper.dev/{search_type}"
    # 2. Append site and filetype filters directly into the Google query string
    if site:
        query = f"{query} site:{site}"
    if filetype:
        query = f"{query} filetype:{filetype}"   
    print(f"Final query after applying filters: {query}")
   # 3. Build the Serper API payload
    payload = {
        "q": query,
        "gl": gl,
        "hl": hl,
        "num": num  # Map it directly into the JSON body sent to Serper
    }
    # Check the explicitly defined parameter
    if time_filter:
        payload["tbs"] = time_filter  # Serper maps time constraints via Google's 'tbs' parameter
    headers = {'X-API-KEY': os.getenv("SERPER_API_KEY"), 'Content-Type': 'application/json'}
    print(f"Making request to {url} with payload: {payload}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "message": response.text}
        return response.json()
    except Exception as e:
        return {"error": "Request failed", "details": str(e)}

# --- 2. Bundle the Tools List ---
tools = [serper_search_tool]
# --- 3. Initialize the Language Model ---
# Ensure OPENAI_API_KEY is present in your environment/env file.
llm = ChatOpenAI(model="gpt-4o", temperature=0)
# --- 4. Build the Agent Using LangGraph ---
# Prebuilt ReAct agent binds tools to the LLM and runs an execution loop automatically.(OSINT=Open Source Intelligence)
system_message = (
    "You are an advanced market research and OSINT AI agent. "
    "You use your web search tool intelligently by specifying domains, file types, "
    "and temporal restrictions when necessary to find the most accurate facts."
)
agent_executor = create_react_agent(
    model=llm, 
    tools=tools, 
    state_modifier=system_message
)
# --- 5. Streamlit Chat Interface ---
st.title("🕵️‍♂️ OSINT AI Research Agent")
st.caption("Powered by LangGraph, OpenAI, and Serper API")
# 1. Initialize chat history first
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help you research today?"}]

# 2. Display previous chat messages exactly once
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
# Handle new user input
if user_query := st.chat_input("Ask me to research something..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.write(user_query)

    # Generate agent response (Notice how this is now nested inside the IF statement!)
    with st.chat_message("assistant"):
        with st.spinner("Searching and analyzing open-source intelligence..."):
            try:
                # Format history into a clean tuple list for LangGraph
                formatted_history = [(m["role"], m["content"]) for m in st.session_state.messages]
                
                # Run the agent graph execution
                response = agent_executor.invoke({"messages": formatted_history})
                
                # Extract the text from the final message node
                agent_answer = response["messages"][-1].content
                
                # Render and commit to history
                st.write(agent_answer)
                st.session_state.messages.append({"role": "assistant", "content": agent_answer})
                
            except Exception as e:
                st.error(f"Agent Processing Error: {str(e)}")

#search_results = serper_search_tool.invoke({"query": "manual Sony WH-1000XM4","search_type": "search","filetype": "pdf","num":1})
#print("Search Results:", search_results)
#search_results = serper_search_tool.invoke({"query": "\"liste des exposants\" OR \"exhibitors list\"","search_type": "search","site":"expoprotection.com","filetype":"pdf","gl":"fr"})#ok
#search_results = serper_search_tool.invoke({"query": "AI business use cases","search_type": "news","time_filter": "qdr:d"}) #ok search_type is mandatory!
#search_results = serper_search_tool.invoke({"query": "AI","search_type": "search","site":"lowcode.agency"}) #ok search_type is mandatory!
#news_results = serper_search_tool.invoke({"query": "AI news","search_type": "news","time_filter": "qdr:d"}) #ok

