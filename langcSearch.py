import time
import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from serper_tool import serper_search_tool 
from dotenv import load_dotenv  # <-- Add this import
# Load environment variables from your .env file
load_dotenv()
# --- Build the Agent Using Core LangChain ---
tools = [serper_search_tool]
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
st.title("🕵️‍♂️ OSINT AI Research Agent v3")
st.caption("Powered by FrameLink and Serper.dev")
# --- Display existing chat history from session state ---
if user_input := st.chat_input("What would you like to research today?"):
    
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Reset tool log array for the fresh execution loop
    st.session_state.tool_logs = []
    
    with st.spinner("Searching and analyzing..."):
        try:
            # Create a placeholder container to append real-time tracking widgets into
            status_container = st.container()
            
            response = agent_executor.invoke({
                "messages": [("user", user_input)]
            })
            
            # --- NEW: Render tool executions inside an expandable status drawer ---
            captured_logs = st.session_state.get("tool_logs", [])
            if captured_logs:
                with status_container:
                    with st.status("🛠️ Tool Executions Detected", expanded=False) as status_box:
                        for log in captured_logs:
                            st.write(f"**Endpoint Triggered:** `{log['url']}`")
                            st.json(log['payload'])
                        status_box.update(label="API Calls Inspected Successfully", state="complete")
            
            final_answer = response["messages"][-1].content
            
            with st.chat_message("assistant"):
                st.markdown(final_answer)
                
            # Append message alongside its associated search trace array to maintain persistence on webpage refreshes
            st.session_state.messages.append({
                "role": "assistant", 
                "content": final_answer,
                "logs": captured_logs
            })
            
        except Exception as e:
            st.error(f"Agent failed to execute: {str(e)}")
#search_results = serper_search_tool.invoke({"query": "manual Sony WH-1000XM4","search_type": "search","filetype": "pdf","num":1})
#print("Search Results:", search_results)
#search_results = serper_search_tool.invoke({"query": "\"liste des exposants\" OR \"exhibitors list\"","search_type": "search","site":"expoprotection.com","filetype":"pdf","gl":"fr"})#ok
#search_results = serper_search_tool.invoke({"query": "AI business use cases","search_type": "news","time_filter": "qdr:d"}) #ok search_type is mandatory!
#search_results = serper_search_tool.invoke({"query": "AI","search_type": "search","site":"lowcode.agency"}) #ok search_type is mandatory!
#news_results = serper_search_tool.invoke({"query": "AI news","search_type": "news","time_filter": "qdr:d"}) #ok

