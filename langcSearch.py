import time
import os
import streamlit as st
# Modern LangChain Core imports
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

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
    #print(f"Final query after applying filters: {query}")
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
    #print(f"Making request to {url} with payload: {payload}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}", "message": response.text}
        return response.json()
    except Exception as e:
        return {"error": "Request failed", "details": str(e)}

# --- Build the Agent Using Core LangChain ---
tools = [serper_search_tool]
# Initialize your foundational LLM
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Define your system instructions directly as a string or SystemMessage
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
# --- Initialize Chat History Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Streamlit Chat Interface ---
st.title("🕵️‍♂️ OSINT AI Research Agent")
st.caption("Powered by FrameLink and Serper.dev")
# --- Display existing chat history from session state ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Capture live user input from the UI chat bar ---
if user_input := st.chat_input("What would you like to research today?"):
    
    # 1. Display user message in the UI and save to session state
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Call your LangGraph agent loop
    with st.spinner("Searching and analyzing..."):
        try:
            response = agent_executor.invoke({
                "messages": [("user", user_input)]
            })
            
            # Extract the final answer text string from the response message array
            final_answer = response["messages"][-1].content
            
            # 3. Display the agent's answer in the UI and save it
            with st.chat_message("assistant"):
                st.markdown(final_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})
            
        except Exception as e:
            st.error(f"Agent failed to execute: {str(e)}")

#search_results = serper_search_tool.invoke({"query": "manual Sony WH-1000XM4","search_type": "search","filetype": "pdf","num":1})
#print("Search Results:", search_results)
#search_results = serper_search_tool.invoke({"query": "\"liste des exposants\" OR \"exhibitors list\"","search_type": "search","site":"expoprotection.com","filetype":"pdf","gl":"fr"})#ok
#search_results = serper_search_tool.invoke({"query": "AI business use cases","search_type": "news","time_filter": "qdr:d"}) #ok search_type is mandatory!
#search_results = serper_search_tool.invoke({"query": "AI","search_type": "search","site":"lowcode.agency"}) #ok search_type is mandatory!
#news_results = serper_search_tool.invoke({"query": "AI news","search_type": "news","time_filter": "qdr:d"}) #ok

