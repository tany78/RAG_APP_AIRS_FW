import os
from dotenv import load_dotenv
import chromadb
from typing import List, Dict
from rag.utils import get_logger
import vertexai
from vertexai.language_models import TextEmbeddingModel

load_dotenv()

GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")

# Initialize Vertex AI with gRPC transport (required for PA firewall SSL decryption)
# This initialization is idempotent - safe to call multiple times
try:
    if GCP_PROJECT:
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION, api_transport="grpc")
    else:
        # Rely on application default credentials on the VM
        vertexai.init(location=GCP_LOCATION, api_transport="grpc")
except Exception as e:
    error_logger = get_logger("vertexai_init_error", "vertexai_init_error.log")
    error_logger.error(f"Failed to initialize Vertex AI in vector_store: {e}")

chroma_client = chromadb.PersistentClient(path="./chroma_data")
collection = chroma_client.get_or_create_collection(name="rag_docs")

def remote_embed(texts: List[str]) -> List[List[float]]:
    model = TextEmbeddingModel.from_pretrained(GEMINI_EMBEDDING_MODEL)
    
    # We batch the texts to avoid hitting potential payload size limits,
    # Vertex AI usually accepts up to 250 texts per request.
    batch_size = 100
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        # Get embeddings for the batch
        embeddings = model.get_embeddings(batch_texts)
        all_embeddings.extend([embedding.values for embedding in embeddings])
        
    return all_embeddings

def add_to_vector_store(doc_id: str, chunks: List[Dict], log=False):
    texts = [c["text"] for c in chunks]
    if not texts:
        if log:
            logger = get_logger("vector_store", "vector_store.log")
            logger.info(f"No text chunks to process for {doc_id}.")
        return

    metadatas = [c["metadata"] for c in chunks]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]

    try:
        embeddings = remote_embed(texts)
        collection.add(documents=texts, metadatas=metadatas, ids=ids, embeddings=embeddings)

        if log:
            logger = get_logger("vector_store", "vector_store.log")
            logger.info(f"Added {len(chunks)} chunks from {doc_id} to local ChromaDB.")
    except Exception as e:
        logger = get_logger("vector_store_error", "vector_store_error.log")
        logger.error(f"Failed to add {doc_id} to vector store: {e}", exc_info=True)


def remove_from_vector_store(doc_id: str, log=False):
    try:
        result = collection.get()
        ids_to_remove = [id_val for id_val, meta in zip(result["ids"], result["metadatas"]) if meta.get("source") == doc_id]
        
        if ids_to_remove:
            collection.delete(ids=ids_to_remove)
            if log:
                logger = get_logger("vector_store", "vector_store.log")
                logger.info(f"Removed {len(ids_to_remove)} vectors for {doc_id} from ChromaDB.")
        elif log:
            logger = get_logger("vector_store", "vector_store.log")
            logger.info(f"No vectors found for {doc_id} to remove (checked all docs).")
    except Exception as e:
        logger = get_logger("vector_store_error", "vector_store_error.log")
        logger.error(f"Error during removal for {doc_id}: {e}", exc_info=True)


def query_vector_store(query: str, k: int = 5) -> List[Dict]:
    if not query.strip():
        return []
    try:
        embedding = remote_embed([query])[0]
        results = collection.query(query_embeddings=[embedding], n_results=k)
        
        if not results or not results.get('documents') or not results['documents'][0]:
            return []
            
        return [
            {"text": doc, "metadata": meta}
            for doc, meta in zip(results['documents'][0], results['metadatas'][0])
        ]
    except Exception as e:
        logger = get_logger("vector_store_error", "vector_store_error.log")
        logger.error(f"Failed to query vector store for '{query[:50]}...': {e}", exc_info=True)
        return []