"""
Streamlit chat frontend for the Banking KB RAG Assistant.

Calls Part 8's FastAPI backend (GET /health, POST /query) and renders
answers with expandable source citations. This is the only file in the
whole project that talks over HTTP to a separate process instead of
importing another part's module directly -- everything upstream (retrieval,
Claude, indexing) runs inside the FastAPI service; this app only knows HTTP,
so it never needs embedding/vector-store/Claude credentials itself.

Usage:
    streamlit run app.py
"""
import sys
from pathlib import Path

import requests
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../3Day_mod
sys.path.insert(0, str(PROJECT_ROOT))

from shared import config

REQUEST_TIMEOUT_SECONDS = 60

st.set_page_config(page_title="Banking KB Assistant", page_icon="🏦", layout="centered")


def check_health() -> dict | None:
    try:
        response = requests.get(f"{config.API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def ask_backend(query: str, top_k: int) -> dict:
    response = requests.post(
        f"{config.API_BASE_URL}/query",
        json={"query": query, "top_k": top_k},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def render_sources(sources: list[dict]) -> None:
    with st.expander(f"Sources ({len(sources)})"):
        for source in sources:
            st.markdown(
                f"**[{source['number']}]** `{source['source_file']}` -- "
                f"{source['heading_path']} (score: {source['score']:.3f})"
            )


# --- Sidebar -----------------------------------------------------------------
with st.sidebar:
    st.header("Banking KB Assistant")
    st.caption(
        "Ask questions about the Enterprise Digital Banking Platform's "
        "internal documentation -- BRD, SRS, HLD/LLD, ADRs, security "
        "guidelines, and more."
    )

    health = check_health()
    if health:
        st.success("Backend connected")
        st.caption(f"Vector store: `{health['vector_store']}`")
        st.caption(f"Embeddings: `{health['embedding_provider']}`")
        st.caption(f"Model: `{health['claude_model']}`")
    else:
        st.error(f"Cannot reach backend at {config.API_BASE_URL}")
        st.caption("Start it with: `python Part8_FastAPI_Backend/main.py`")

    top_k = st.slider("Sources to retrieve", min_value=1, max_value=10, value=config.TOP_K)

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

# --- Chat state ----------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🏦 Banking Knowledge Base Assistant")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            render_sources(message["sources"])

if prompt := st.chat_input("Ask a question about the banking platform..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving context and asking Claude..."):
            try:
                result = ask_backend(prompt, top_k)
                answer = result["answer"]
                sources = result["sources"]
            except requests.RequestException as exc:
                answer = f"Sorry, I couldn't reach the backend: {exc}"
                sources = []

        st.markdown(answer)
        if sources:
            render_sources(sources)

    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
