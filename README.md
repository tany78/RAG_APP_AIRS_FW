# 📄 Streamlit RAG Chat Application

A production-ready **Retrieval-Augmented Generation (RAG)** chat application built with Streamlit, LangChain, and Google Vertex AI. Upload documents (PDF, DOCX) and chat with them using Google's Gemini models.

![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.32.2-red)

## ✨ Features

- 📤 **Document Upload**: Support for PDF and DOCX files
- 🔍 **Semantic Search**: ChromaDB vector database with sentence transformers
- 🤖 **AI Chat**: Powered by Google Vertex AI Gemini models
- 💬 **Conversational Memory**: Maintains chat context across multiple turns
- 🐞 **Debug Mode**: Built-in logging for chunks, prompts, latency, and API responses
- 🔐 **Security**: Environment-based configuration, no hardcoded credentials
- 🚀 **Production Ready**: Systemd service, automated deployment scripts

## 🏗️ Architecture

```
┌─────────────────┐
│  Streamlit UI   │  ← User Interface (Port 8501)
└────────┬────────┘
         │
         ├─→ Document Upload → Loader → Chunker
         │                                ↓
         │                          Vector Store
         │                          (ChromaDB)
         │                                ↑
         └─→ User Query ──────────────────┤
                                          │
                                    Retrieval
                                          ↓
                                   Context Building
                                          ↓
                              ┌───────────────────┐
                              │  Vertex AI Gemini │
                              │  (Chat Model)     │
                              └───────────────────┘
                                          ↓
                                      Response
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Google Cloud Platform account
- Vertex AI API enabled in your GCP project
- Application Default Credentials configured

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/streamlit-rag-app.git
   cd streamlit-rag-app
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.template .env
   # Edit .env with your GCP project details
   ```

   Your `.env` file should contain:
   ```env
   GCP_PROJECT="your-gcp-project-id"
   GCP_LOCATION="us-central1"
   GEMINI_CHAT_MODEL="gemini-1.5-pro-001"
   GEMINI_EMBEDDING_MODEL="text-embedding-004"
   ```

5. **Authenticate with GCP**
   ```bash
   gcloud auth application-default login
   ```

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Access the app**
   - Open your browser to http://localhost:8501
   - Upload a document (PDF or DOCX)
   - Start chatting!

## 📁 Project Structure

```
streamlit-rag-app/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.template              # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── rag/                       # RAG module
│   ├── chat_engine.py         # Vertex AI integration & chat logic
│   ├── vector_store.py        # ChromaDB vector database
│   ├── loader.py              # Document loading (PDF/DOCX)
│   ├── chunker.py             # Text chunking
│   ├── memory.py              # Conversation memory
│   ├── utils.py               # Logging utilities
│   └── test_gemini_llm.py     # Vertex AI connectivity test
│
├── deployment/                # Deployment scripts
│   ├── deploy.sh              # Automated deployment script
│   └── streamlit-rag.service  # Systemd service file
│
├── cache/                     # Application cache
│   └── uploaded_files/        # User-uploaded documents
│
├── chroma_data/              # ChromaDB persistent storage
└── logs/                     # Application logs (when debug enabled)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GCP_PROJECT` | Your GCP project ID | Required |
| `GCP_LOCATION` | GCP region for Vertex AI | `us-central1` |
| `GEMINI_CHAT_MODEL` | Gemini model for chat | `gemini-1.5-pro-001` |
| `GEMINI_EMBEDDING_MODEL` | Model for embeddings | `text-embedding-004` |

### Debug Options

Enable debug logging via the sidebar:
- **Log Retrieved Chunks**: See which document chunks are retrieved
- **Log Prompt**: View the complete prompt sent to Gemini
- **Log LLM Latency**: Measure response times
- **Log Vector Store Operations**: Track add/remove operations
- **Log Raw Vertex Response**: See raw API responses

Logs are written to the `logs/` directory when enabled.

## 🌐 Production Deployment

### Ubuntu Server Deployment

The application includes automated deployment scripts for Ubuntu 22.04 servers.

1. **Copy application files to server**
   ```bash
   scp -r . user@server:/tmp/streamlit-rag-app
   ```

2. **SSH into server and run deployment**
   ```bash
   ssh user@server
   cd /tmp/streamlit-rag-app
   sudo chmod +x deployment/deploy.sh
   sudo ./deployment/deploy.sh
   ```

The deployment script will:
- ✅ Install system dependencies (Python, build tools)
- ✅ Create application directory at `/opt/streamlit-rag-app`
- ✅ Set up Python virtual environment
- ✅ Install Python dependencies
- ✅ Generate `.env` from template
- ✅ Configure systemd service
- ✅ Start the application

### Systemd Service Management

Once deployed, manage the application with systemd:

```bash
# Check status
sudo systemctl status streamlit-rag

# Start the service
sudo systemctl start streamlit-rag

# Stop the service
sudo systemlit stop streamlit-rag

# Restart the service
sudo systemctl restart streamlit-rag

# View logs
sudo journalctl -u streamlit-rag -f
```

### GCP Deployment (Terraform)

This application can be deployed as part of a larger GCP infrastructure using Terraform. The typical pattern:

1. **Clone from Git**: Terraform startup script clones this repository
2. **Run Deployment**: Executes `deployment/deploy.sh` automatically
3. **Configure Networking**: Sets up firewall rules for port 8501
4. **IAM**: Attaches service account with Vertex AI permissions

## 🧪 Testing

### Test Vertex AI Connectivity

Run the included test script to verify Vertex AI access:

```bash
python rag/test_gemini_llm.py
```

Expected output:
```
🔧 Initializing Vertex AI with Default Credentials, Location: us-central1
✅ Vertex AI initialized successfully

💬 Testing Chat Model: gemini-1.5-pro-001
User: Hello, how are you?
Bot: [Gemini response]

🧠 Using Embedding Model: text-embedding-004
✅ Generated embedding with 768 dimensions
```

## 📊 Technical Details

### Dependencies

- **Streamlit** (1.32.2): Web UI framework
- **LangChain** (0.1.17): RAG orchestration
- **ChromaDB** (0.4.24): Vector database
- **Sentence Transformers** (2.6.1): Text embeddings
- **Google Cloud AI Platform** (1.49.0): Vertex AI SDK
- **PyMuPDF** (1.24.1) & **pypdf** (4.2.0): PDF processing
- **python-docx** (1.1.0): DOCX processing

### Vector Database

- **Database**: ChromaDB (local, persistent)
- **Storage**: `./chroma_data/`
- **Collection**: `rag_docs`
- **Embedding Model**: Vertex AI `text-embedding-004` (768 dimensions)

### LLM Configuration

- **Provider**: Google Vertex AI
- **Chat Model**: Gemini 1.5 Pro (configurable)
- **Max Output Tokens**: 512
- **Temperature**: Default (configurable in code)

## 🔐 Security Considerations

### Current Security Features

✅ **No Hardcoded Credentials**: All sensitive values in environment variables  
✅ **`.gitignore` Configured**: Prevents committing secrets, cache, logs  
✅ **Application Default Credentials**: Uses GCP IAM for authentication  
✅ **Environment-based Config**: `.env.template` for safe sharing  

### Production Hardening Recommendations

For production deployments, consider:

- 🔒 **Authentication**: Add user authentication (e.g., OAuth, SAML)
- 🌐 **HTTPS**: Use reverse proxy (nginx) with SSL/TLS
- 🔥 **Firewall**: Restrict access by IP address
- 🔑 **Secret Management**: Use GCP Secret Manager instead of `.env`
- 📊 **Monitoring**: Set up Cloud Monitoring and alerting
- 💾 **Backups**: Schedule backups of `chroma_data/`
- 🚫 **Rate Limiting**: Implement API rate limiting
- 📝 **Audit Logging**: Enable comprehensive audit logs

## 🐛 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'vertexai'`  
**Solution**: Install dependencies: `pip install -r requirements.txt`

**Issue**: `Permission denied` when accessing Vertex AI  
**Solution**: 
```bash
# Authenticate
gcloud auth application-default login

# Verify service account has roles/aiplatform.user role
gcloud projects get-iam-policy PROJECT_ID
```

**Issue**: Streamlit port 8501 not accessible  
**Solution**: Check firewall rules and ensure port 8501 is open

**Issue**: Documents not being retrieved in chat  
**Solution**: 
- Verify documents were uploaded successfully
- Check `chroma_data/` directory exists and has data
- Enable "Log Retrieved Chunks" debug option

### Debug Mode

Enable debug options in the sidebar to troubleshoot:
1. Check `logs/` directory for detailed logs
2. Review chunk retrieval quality
3. Inspect prompt construction
4. Measure LLM latency

## 📄 License

Apache License 2.0

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Support

For issues and questions:
- 🐛 **Bug Reports**: Open an issue on GitHub
- 💡 **Feature Requests**: Submit an issue with enhancement label
- 📖 **Documentation**: Check this README and code comments

## 🙏 Acknowledgments

- Google Cloud Vertex AI for LLM capabilities
- Streamlit for the amazing web framework
- ChromaDB for vector storage
- LangChain for RAG orchestration

---

**Built with ❤️ for the AI community**
