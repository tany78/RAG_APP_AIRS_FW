#! /usr/bin/python3

import os
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from vertexai.language_models import TextEmbeddingModel

load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL_NAME = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-pro-001")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")

try:
    if GCP_PROJECT:
        print(f"🔧 Initializing Vertex AI with Project: {GCP_PROJECT}, Location: {GCP_LOCATION}")
        vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)
    else:
        print(f"🔧 Initializing Vertex AI with Default Credentials, Location: {GCP_LOCATION}")
        vertexai.init(location=GCP_LOCATION)
    print("✅ Vertex AI initialized successfully.")

    # --- Test Chat Model ---
    model = GenerativeModel(
        GEMINI_MODEL_NAME,
        system_instruction="You are a helpful assistant."
    )
    print(f"\n🧠 Using Chat Model: {GEMINI_MODEL_NAME}")

    user_prompt = "What is the capital of France?"
    print(f"🗣️ Sending prompt: '{user_prompt}'")

    generation_config = GenerationConfig(
        temperature=0.5,
        max_output_tokens=50
    )

    response = model.generate_content(
        user_prompt,
        generation_config=generation_config
    )

    print("✅ Vertex AI Chat Responded:")
    if response.text:
        print(response.text.strip())
    else:
        print("❌ Vertex AI responded, but no text found.")

    # --- Test Embedding Model ---
    print(f"\n🧠 Using Embedding Model: {GEMINI_EMBEDDING_MODEL}")
    embedding_model = TextEmbeddingModel.from_pretrained(GEMINI_EMBEDDING_MODEL)
    
    test_text = "This is a test for embeddings."
    print(f"🗣️ Getting embeddings for: '{test_text}'")
    
    embeddings = embedding_model.get_embeddings([test_text])
    
    if embeddings and embeddings[0].values:
        print(f"✅ Vertex AI Embedding Responded! Generated {len(embeddings[0].values)} dimensions.")
    else:
        print("❌ Vertex AI Embedding failed to return dimensions.")

except Exception as e:
    print("❌ Failed to connect to Vertex AI or generate response.")
    print(f"Error: {e}")
    print("\n💡 Make sure you are authenticated with GCP:")
    print("   Run: gcloud auth application-default login")
    print("   Ensure the account has the 'Vertex AI User' role.")