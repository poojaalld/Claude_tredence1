"""
Streamlit Frontend for Banking RAG Assistant
Interactive web interface for querying the banking knowledge base
"""

import streamlit as st
import requests
from typing import List, Dict
import json
from datetime import datetime


# Page configuration
st.set_page_config(
    page_title="Banking RAG Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .response-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .source-box {
        background-color: #e8f4f8;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"


def get_api_url():
    """Get API URL from sidebar"""
    with st.sidebar:
        st.header("Configuration")
        api_url = st.text_input(
            "API URL",
            value=st.session_state.api_url,
            help="URL of the Banking RAG API"
        )
        st.session_state.api_url = api_url
        return api_url


def query_rag_api(query: str, top_k: int, max_tokens: int) -> Dict:
    """
    Send query to RAG API
    
    Args:
        query: User query
        top_k: Number of chunks to retrieve
        max_tokens: Maximum tokens in response
        
    Returns:
        API response or error dict
    """
    try:
        response = requests.post(
            f"{st.session_state.api_url}/query",
            json={
                "query": query,
                "top_k": top_k,
                "max_tokens": max_tokens
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
            
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API. Is the server running?"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}


def display_response(response: Dict):
    """Display API response"""
    if "error" in response:
        st.error(f"Error: {response['error']}")
        return
    
    # Display answer
    st.markdown("### Answer")
    st.markdown(f'<div class="response-box">{response.get("response", "")}</div>', 
                unsafe_allow_html=True)
    
    # Display metadata
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Confidence", f"{response.get('confidence', 0):.1%}")
    
    with col2:
        st.metric("Processing Time", f"{response.get('processing_time', 0):.2f}s")
    
    with col3:
        st.metric("Chunks Retrieved", response.get("chunks_retrieved", 0))
    
    # Display sources
    st.markdown("### Sources")
    sources = response.get("sources", [])
    if sources:
        for source in sources:
            st.markdown(f'<div class="source-box">📄 {source}</div>', 
                       unsafe_allow_html=True)
    else:
        st.info("No sources")


def display_statistics(stats: Dict):
    """Display API statistics"""
    if "error" in stats:
        st.warning(f"Could not fetch statistics: {stats['error']}")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Queries", stats.get("total_queries", 0))
    
    with col2:
        st.metric("Avg Processing Time", f"{stats.get('average_processing_time', 0):.2f}s")
    
    with col3:
        st.metric("Total Chunks", stats.get("total_chunks_retrieved", 0))
    
    with col4:
        st.metric("Avg Confidence", f"{stats.get('average_confidence', 0):.1%}")


def main():
    """Main application"""
    # Header
    st.markdown("# 🏦 Banking RAG Assistant")
    st.markdown("""
    Welcome to the Banking RAG Assistant! Ask questions about our banking products, 
    services, and policies. The system will retrieve relevant information and provide 
    accurate answers based on our knowledge base.
    """)
    
    # Get API URL
    api_url = get_api_url()
    
    # Sidebar
    with st.sidebar:
        st.markdown("---")
        
        # Advanced settings
        st.markdown("### Advanced Settings")
        top_k = st.slider("Number of chunks to retrieve", 1, 10, 5)
        max_tokens = st.slider("Maximum response tokens", 256, 4096, 2048, step=256)
        
        # Clear history button
        if st.button("Clear History"):
            st.session_state.messages = []
            st.rerun()
        
        # Statistics
        st.markdown("---")
        st.markdown("### Statistics")
        if st.button("Refresh Statistics"):
            pass
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["Chat", "Statistics", "About"])
    
    with tab1:
        # Display conversation history
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(message["response"])
                    
                    # Display metadata
                    with st.expander("View Details"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Confidence", f"{message.get('confidence', 0):.1%}")
                        with col2:
                            st.metric("Time", f"{message.get('processing_time', 0):.2f}s")
                        with col3:
                            st.metric("Chunks", message.get('chunks_retrieved', 0))
                        
                        if message.get("sources"):
                            st.markdown("**Sources:**")
                            for source in message["sources"]:
                                st.markdown(f"- {source}")
        
        # Query input
        st.markdown("---")
        user_input = st.chat_input("Ask about our banking products and services...")
        
        if user_input:
            # Add user message to history
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Get response from API
            with st.spinner("Searching knowledge base and generating response..."):
                response = query_rag_api(user_input, top_k, max_tokens)
            
            # Display response
            with st.chat_message("assistant"):
                if "error" not in response:
                    st.markdown(response.get("response", ""))
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": user_input,
                        **response
                    })
                    
                    # Display metadata
                    with st.expander("View Details"):
                        display_response(response)
                else:
                    st.error(response["error"])
            
            st.rerun()
    
    with tab2:
        st.markdown("### System Statistics")
        
        # Get statistics from API
        try:
            response = requests.get(
                f"{api_url}/stats",
                timeout=5
            )
            if response.status_code == 200:
                stats = response.json()
                display_statistics(stats)
            else:
                st.error("Could not fetch statistics")
        except Exception as e:
            st.error(f"Error fetching statistics: {str(e)}")
    
    with tab3:
        st.markdown("### About Banking RAG Assistant")
        st.markdown("""
        The Banking RAG Assistant is a Retrieval-Augmented Generation (RAG) system 
        that combines a knowledge base with advanced language models to provide 
        accurate, contextual answers to banking-related questions.
        
        **Key Features:**
        - Semantic search over banking documents
        - Contextual answer generation using Claude AI
        - Source attribution for all responses
        - Real-time confidence scoring
        - Conversation history
        
        **Technology Stack:**
        - FastAPI backend for REST API
        - FAISS for vector similarity search
        - Anthropic Claude for generation
        - Streamlit for user interface
        
        **How It Works:**
        1. Your question is converted to an embedding vector
        2. Similar chunks from the banking knowledge base are retrieved
        3. Retrieved chunks are formatted as context
        4. Claude generates an answer based on the context
        5. Sources are provided for verification
        """)
        
        st.markdown("---")
        st.markdown("### Example Questions")
        
        example_questions = [
            "What is the interest rate for savings accounts?",
            "How much does a personal loan cost?",
            "What are the fees for ATM withdrawals?",
            "How do I apply for a mortgage?",
            "What is your fraud protection policy?",
        ]
        
        for i, question in enumerate(example_questions, 1):
            if st.button(f"📝 {question}", key=f"example_{i}"):
                st.session_state.messages.append({
                    "role": "user",
                    "content": question
                })
                st.rerun()


if __name__ == "__main__":
    main()
