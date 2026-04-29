#!/bin/bash
set -e

# Streamlit RAG Application - Automated Deployment Script
# For Ubuntu 22.04 LTS on GCP
# This script is designed to be run by Terraform during VM provisioning

echo "=================================================="
echo "Starting Streamlit RAG Application Deployment"
echo "=================================================="

# Configuration
APP_DIR="/opt/streamlit-rag-app"
APP_USER="ubuntu"
PYTHON_VERSION="python3"

# Get GCP metadata for configuration
get_gcp_metadata() {
    curl -s -H "Metadata-Flavor: Google" \
        "http://metadata.google.internal/computeMetadata/v1/$1"
}

# Detect GCP project and region from instance metadata
echo "[1/10] Detecting GCP environment..."
GCP_PROJECT_ID=$(get_gcp_metadata "project/project-id" || echo "")
GCP_ZONE=$(get_gcp_metadata "instance/zone" || echo "")
GCP_REGION=$(echo "$GCP_ZONE" | sed 's/\(.*\)-.*/\1/' || echo "us-central1")

if [ -z "$GCP_PROJECT_ID" ]; then
    echo "ERROR: Could not detect GCP Project ID from metadata"
    exit 1
fi

echo "   ✓ Project ID: $GCP_PROJECT_ID"
echo "   ✓ Region: $GCP_REGION"

# Update system packages
echo "[2/10] Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq
echo "   ✓ System updated"

# Install required system packages
echo "[3/10] Installing system dependencies..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    libpq-dev \
    > /dev/null 2>&1
echo "   ✓ System dependencies installed"

# Create application directory
echo "[4/10] Setting up application directory..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Copy application files (assumes script is run from app source directory or files are in /tmp)
if [ -d "/tmp/streamlit-rag-app" ]; then
    echo "   ✓ Copying application files from /tmp/streamlit-rag-app..."
    cp -r /tmp/streamlit-rag-app/* "$APP_DIR/"
elif [ -f "./app.py" ]; then
    echo "   ✓ Application files already in place"
else
    echo "ERROR: Application files not found. Ensure they are in /tmp/streamlit-rag-app/"
    exit 1
fi

# Set ownership
chown -R $APP_USER:$APP_USER "$APP_DIR"
echo "   ✓ Application directory configured: $APP_DIR"

# Create Python virtual environment
echo "[5/10] Creating Python virtual environment..."
sudo -u $APP_USER $PYTHON_VERSION -m venv "$APP_DIR/venv"
echo "   ✓ Virtual environment created"

# Upgrade pip
echo "[6/10] Upgrading pip..."
sudo -u $APP_USER "$APP_DIR/venv/bin/pip" install --upgrade pip setuptools wheel -q
echo "   ✓ Pip upgraded"

# Install Python dependencies
echo "[7/10] Installing Python dependencies (this may take 5-10 minutes)..."
sudo -u $APP_USER "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q
echo "   ✓ Python dependencies installed"

# Generate .env file from template
echo "[8/10] Configuring environment variables..."
if [ -f "$APP_DIR/.env.template" ]; then
    cat "$APP_DIR/.env.template" | \
        sed "s/\${GCP_PROJECT_ID}/$GCP_PROJECT_ID/g" | \
        sed "s/\${GCP_REGION}/$GCP_REGION/g" \
        > "$APP_DIR/.env"
    chown $APP_USER:$APP_USER "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    echo "   ✓ Environment file created: $APP_DIR/.env"
else
    echo "WARNING: .env.template not found, creating basic .env"
    cat > "$APP_DIR/.env" << EOF
GCP_PROJECT="$GCP_PROJECT_ID"
GCP_LOCATION="$GCP_REGION"
GEMINI_CHAT_MODEL="gemini-1.5-pro-001"
GEMINI_EMBEDDING_MODEL="text-embedding-004"
EOF
    chown $APP_USER:$APP_USER "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
fi

# Create required directories
echo "[9/10] Creating application directories..."
sudo -u $APP_USER mkdir -p "$APP_DIR/cache/uploaded_files"
sudo -u $APP_USER mkdir -p "$APP_DIR/chroma_data"
sudo -u $APP_USER mkdir -p "$APP_DIR/logs"
echo "   ✓ Application directories created"

# Install and configure systemd service
echo "[10/10] Configuring systemd service..."
if [ -f "$APP_DIR/deployment/streamlit-rag.service" ]; then
    cp "$APP_DIR/deployment/streamlit-rag.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable streamlit-rag.service
    systemctl start streamlit-rag.service
    echo "   ✓ Systemd service installed and started"
else
    echo "WARNING: systemd service file not found at $APP_DIR/deployment/streamlit-rag.service"
    echo "   You will need to start the application manually"
fi

# Configure firewall (GCP-specific)
echo ""
echo "Configuring firewall..."
# Note: GCP firewall rules are typically managed by Terraform
# This is just to ensure the local firewall allows the traffic
if command -v ufw > /dev/null 2>&1; then
    ufw allow 8501/tcp
    echo "   ✓ Local firewall configured (port 8501 allowed)"
fi

# Verify service status
echo ""
echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""

if systemctl is-active --quiet streamlit-rag.service; then
    echo "✓ Service Status: RUNNING"
    INSTANCE_IP=$(get_gcp_metadata "instance/network-interfaces/0/access-configs/0/external-ip")
    echo "✓ Application URL: http://$INSTANCE_IP:8501"
else
    echo "⚠ Service Status: NOT RUNNING"
    echo "  Check logs with: sudo journalctl -u streamlit-rag.service -f"
fi

echo ""
echo "Useful Commands:"
echo "  - Check status:  sudo systemctl status streamlit-rag"
echo "  - View logs:     sudo journalctl -u streamlit-rag -f"
echo "  - Restart:       sudo systemctl restart streamlit-rag"
echo "  - Stop:          sudo systemctl stop streamlit-rag"
echo ""
echo "Application Directory: $APP_DIR"
echo "GCP Project: $GCP_PROJECT_ID"
echo "Region: $GCP_REGION"
echo ""
