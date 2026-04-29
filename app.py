import streamlit as st
import os
from pathlib import Path
from rag.loader import load_document
from rag.vector_store import add_to_vector_store, remove_from_vector_store
from rag.chat_engine import handle_chat, reset_chat_memory

# Constants
UPLOAD_DIR = Path("cache/uploaded_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="RAG Chat App", layout="wide")
st.title("📄 RAG File Upload Interface")

# ---- Debug Toggles ----
st.sidebar.markdown("## 🐞 Debug Options")
log_chunks = st.sidebar.checkbox("Log Retrieved Chunks to File")
log_prompt = st.sidebar.checkbox("Log Prompt to File")
log_latency = st.sidebar.checkbox("Log LLM Latency")
log_vector_ops = st.sidebar.checkbox("Log Vector Store Operations")
log_vertex_raw = st.sidebar.checkbox("Log Raw Vertex Response")

# Sidebar: Upload new document
st.sidebar.header("Upload Document")
uploaded_file = st.sidebar.file_uploader("Choose a PDF or DOCX file", type=["pdf", "docx"])

if uploaded_file:
    file_path = UPLOAD_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"Uploaded: {uploaded_file.name}")
    
    chunks = load_document(file_path)
    add_to_vector_store(file_path.name, chunks, log=log_vector_ops)

# Main: List uploaded documents
st.subheader("Uploaded Documents")
all_docs = [f.name for f in UPLOAD_DIR.glob("*") if f.is_file()]

if not all_docs:
    st.info("No documents uploaded yet.")
else:
    for doc in all_docs:
        col1, col2 = st.columns([4, 1])
        col1.write(doc)
        if col2.button("❌ Delete", key=f"del_{doc}"):
            try:
                os.remove(UPLOAD_DIR / doc)
                remove_from_vector_store(doc, log=log_vector_ops)
                st.success(f"Deleted {doc}")
            except Exception as e:
                st.error(f"Error deleting {doc}: {str(e)}")

# ---- Chat Interface ----
st.subheader("💬 Chat Interface")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("Ask a question about your documents:")

if st.button("Send") and user_input.strip():
    response = handle_chat(user_input, log_chunks, log_prompt, log_latency, log_vertex_raw)
    st.session_state.chat_history.append(("You", user_input))
    st.session_state.chat_history.append(("Bot", response))

if st.button("Reset Chat"):
    reset_chat_memory()
    st.session_state.chat_history = []
    st.success("Chat history reset.")

for role, msg in st.session_state.chat_history:
    st.markdown(f"**{role}:** {msg}")
