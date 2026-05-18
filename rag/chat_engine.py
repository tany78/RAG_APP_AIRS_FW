import os
import time
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part, GenerationConfig
from rag.vector_store import query_vector_store
from rag.memory import ChatMemory
from rag.utils import get_logger

load_dotenv()

GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Initialize Vertex AI
try:
    if GCP_PROJECT:
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION, api_transport="grpc")
    else:
        # Rely on application default credentials on the VM
        vertexai.init(location=GCP_LOCATION, api_transport="grpc")
except Exception as e:
    error_logger = get_logger("vertexai_config_error", "vertexai_config_error.log")
    error_logger.error(f"Failed to initialize Vertex AI: {e}")

try:
    gemini_chat_model = GenerativeModel(GEMINI_CHAT_MODEL)
except Exception as e:
    error_logger = get_logger("vertex_model_init_error", "vertex_model_init_error.log")
    error_logger.critical(f"Failed to initialize Vertex GenerativeModel '{GEMINI_CHAT_MODEL}': {e}", exc_info=True)
    gemini_chat_model = None

chat_memory = ChatMemory()

def build_messages_for_gemini(query: str, retrieved_chunks, history):
    contents = []
    context_text = "\n\n".join([chunk["text"] for chunk in retrieved_chunks])

    for h_entry in history:
        contents.append(Content(role="user", parts=[Part.from_text(h_entry["user"])]))
        contents.append(Content(role="model", parts=[Part.from_text(h_entry["bot"])]))

    user_query_with_context = query
    if context_text:
        user_query_with_context = f"Context from documents:\n{context_text}\n\nQuestion: {query}"
    
    contents.append(Content(role="user", parts=[Part.from_text(user_query_with_context)]))
    
    return contents


def handle_chat(user_input: str, log_chunks=False, log_prompt=False, log_latency=False, log_raw=False) -> str:
    if not gemini_chat_model:
        return "[Error: Vertex AI chat model is not available. Check application logs for configuration issues.]"

    retrieved = query_vector_store(user_input)
    if log_chunks:
        logger = get_logger("retrieved_chunks", "retrieved_chunks.log")
        for i, chunk in enumerate(retrieved):
            logger.info(f"Chunk {i}: {chunk['text'][:100]}")

    history = chat_memory.get()
    messages_for_gemini = build_messages_for_gemini(user_input, retrieved, history)

    if log_prompt:
        logger = get_logger("prompt", "prompt.log")
        # Log the prompt contents appropriately
        logger.info(str([{"role": c.role, "parts": [p.text for p in c.parts]} for c in messages_for_gemini]))

    try:
        start = time.time()
        
        generation_config = GenerationConfig(
            temperature=0.7,
            max_output_tokens=512
        )
        
        response = gemini_chat_model.generate_content(
            messages_for_gemini,
            generation_config=generation_config,
        )
        latency = time.time() - start

        # Extract text reply from Vertex AI response
        if hasattr(response, 'text') and response.text:
            bot_reply = response.text.strip()
        elif response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            bot_reply = "".join(part.text for part in response.candidates[0].content.parts).strip()
        else:
            bot_reply = "[Error: Could not extract reply from Vertex AI response. Check logs.]"
            if log_raw:
                raw_logger = get_logger("vertex_raw_error", "vertex_raw_error.log")
                raw_logger.error(f"Unexpected Vertex AI response structure: {response}")

        if log_raw:
            logger = get_logger("vertex_raw", "vertex_raw.log")
            try:
                logger.info(str(response))
            except Exception as e:
                logger.error(f"Could not serialize Vertex AI response for logging: {e}")

        if log_latency:
            logger = get_logger("latency", "latency.log")
            logger.info(f"LLM (Vertex AI) response time: {latency:.2f}s")

        chat_memory.add(user_input, bot_reply)
        return bot_reply
    except Exception as e:
        error_logger = get_logger("vertex_error", "vertex_error.log")
        error_logger.error(f"Error contacting Vertex AI in handle_chat: {str(e)}", exc_info=True)
        return f"[Error contacting Vertex AI: {str(e)}]"

def reset_chat_memory():
    chat_memory.reset()