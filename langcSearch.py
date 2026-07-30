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

# --- Password Gate ---
def check_password() -> bool:
    """Blocks access to the app until the correct APP_PASSWORD is entered."""
    app_password = os.getenv("APP_PASSWORD")
    if not app_password:
        st.error("APP_PASSWORD is not set. Configure it as an environment variable to enable access.")
        return False

    if st.session_state.get("authenticated", False):
        return True

    st.title("🔒 OSINT AI Research Agent")
    entered_password = st.text_input("Password", type="password")
    if st.button("Log in"):
        if entered_password == app_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

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

# --- Manual Search Sidebar (bypass the AI agent, call Serper directly) ---
with st.sidebar:
    st.header("🔧 Manual Search")
    st.caption("Call the Serper tool directly with your own parameters, skipping the AI agent.")
    with st.form("manual_search_form"):
        manual_query = st.text_input("Query")
        manual_search_type = st.selectbox(
            "Search type",
            ["search", "news", "images", "places", "shopping", "scholar"],
        )
        manual_site = st.text_input("Site (optional)")
        manual_filetype = st.text_input("Filetype (optional)")
        col1, col2 = st.columns(2)
        with col1:
            manual_gl = st.text_input("Country (gl)", value="us")
        with col2:
            manual_hl = st.text_input("Language (hl)", value="en")
        time_filter_labels = {
            "": "None",
            "qdr:h": "Past hour",
            "qdr:d": "Past day",
            "qdr:w": "Past week",
            "qdr:m": "Past month",
            "qdr:y": "Past year",
        }
        manual_time_filter = st.selectbox(
            "Time filter (optional)",
            list(time_filter_labels.keys()),
            format_func=lambda v: time_filter_labels[v],
        )
        manual_num = st.number_input("Num results", min_value=1, max_value=100, value=10)
        manual_submit = st.form_submit_button("Run Search")

    if manual_submit:
        if not manual_query:
            st.warning("Query is required.")
        else:
            manual_payload = {
                "search_type": manual_search_type,
                "query": manual_query,
                "gl": manual_gl,
                "hl": manual_hl,
                "num": int(manual_num),
            }
            if manual_site:
                manual_payload["site"] = manual_site
            if manual_filetype:
                manual_payload["filetype"] = manual_filetype
            if manual_time_filter:
                manual_payload["time_filter"] = manual_time_filter

            with st.spinner("Searching..."):
                st.session_state.manual_result = serper_search_tool.invoke(manual_payload)
                st.session_state.manual_payload = manual_payload

    if "manual_result" in st.session_state:
        st.subheader("Result")
        st.json(st.session_state.manual_result)

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

