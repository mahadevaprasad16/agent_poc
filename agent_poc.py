import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool


# ---------------------------------------------------------
# STREAMLIT UI
# ---------------------------------------------------------
st.set_page_config(page_title="Gemini + ServiceNow Agentic POC", layout="wide")
st.title("ServiceNow Agentic POC (LangGraph)")
st.write("Demonstrates tool-calling using Gemini + LangGraph.")
load_dotenv()

# ---------------------------------------------------------
# ENVIRONMENT VARIABLES
# ---------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SN_INSTANCE = os.environ.get("SN_INSTANCE")
SN_USERNAME = os.environ.get("SN_USERNAME")
SN_PASSWORD = os.environ.get("SN_PASSWORD")

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY missing. Export it before running.")
    st.stop()


# ---------------------------------------------------------
# INIT LLM (Gemini 2.5 Flash)
# ---------------------------------------------------------
@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=GEMINI_API_KEY,
        temperature=0.2
    )

llm = load_llm()


# ---------------------------------------------------------
# TOOL: ServiceNow incident fetcher
# ---------------------------------------------------------
@tool
def get_servicenow_incidents(status: str) -> str:
    """
    Fetch incidents from ServiceNow by status.
    """
    if not all([SN_INSTANCE, SN_USERNAME, SN_PASSWORD]):
        return "ERROR: Missing SN_INSTANCE, SN_USERNAME, SN_PASSWORD."

    status_map = {
        "new": "1",
        "in progress": "2",
        "active": "2",
        "resolved": "6",
        "closed": "7"
    }

    state = status_map.get(status.lower())
    if not state:
        return "ERROR: Invalid status. Use new, in progress, resolved, closed."

    try:
        url = f"https://{SN_INSTANCE}/api/now/table/incident"
        params = {
            "sysparm_limit": 50,
            "sysparm_query": f"state={state}",
            "sysparm_fields": "number,short_description,priority,state,assigned_to"
        }
        r = requests.get(
            url,
            auth=(SN_USERNAME, SN_PASSWORD),
            headers={"Accept": "application/json"},
            params=params,
            timeout=12
        )
        r.raise_for_status()
        return {
            "status_code": r.status_code,
            "headers": dict(r.headers),
            "body_preview": r.text[:2000]
        }

    except Exception as e:
        return f"ERROR: {str(e)}"


tools = [get_servicenow_incidents]


# ---------------------------------------------------------
# CREATE REACT AGENT (NO state_modifier)
# ---------------------------------------------------------
@st.cache_resource
def init_agent():
    return create_react_agent(llm, tools)

agent = init_agent()


# ---------------------------------------------------------
# SYSTEM PROMPT —
# Injected manually on each call
# ---------------------------------------------------------
SYSTEM_PROMPT = """
You are a ServiceNow ITSM expert using Gemini 2.5 Flash.

Rules:
- ALWAYS call the tool `get_servicenow_incidents` when asked about incident states.
- After tool execution, summarize the results clearly in bullet points.
- If the tool returns an ERROR, explain it clearly.
"""


# ---------------------------------------------------------
# STREAMLIT CHAT LOOP
# ---------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("Ask something like: 'Show me resolved incidents'")

if user_input:
    st.session_state.chat_history.append(("user", user_input))

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ]

            result = agent.invoke({"messages": messages})

            # FIX: result is an AIMessage
            last_msg = result["messages"][-1]
            # Gemini 2.5 Flash returns: content=[{"type": "text", "text": "..."}]
        if hasattr(last_msg, "content") and isinstance(last_msg.content, list):
            output = last_msg.content[0]["text"]
        else:
            # fallback if LC ever switches format
            output = str(last_msg)
        st.write(output)
        st.session_state.chat_history.append(("assistant", output))


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.write("Try")
    st.write("- show me new incidents")
    st.write("- list resolved tickets")
    st.write("- what is in progress?")
