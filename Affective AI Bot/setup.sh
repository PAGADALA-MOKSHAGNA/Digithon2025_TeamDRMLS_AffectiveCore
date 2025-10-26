#!/bin/bash

# AffectiveCore Setup Script
# This script helps set up the environment for the Speech Emotion Detection system

set -e

echo "🎭 AffectiveCore Speech Emotion Detection Setup"
echo "==============================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Check if Python 3.8+
required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8+ required"
    exit 1
fi

# Create virtual environment
echo ""
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📥 Installing dependencies..."
echo "   This may take a few minutes..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p test_samples
mkdir -p models

echo "   ✅ Directories created"

# Download Whisper model
echo ""
echo "🤖 Downloading Whisper model (this may take a while)..."
python3 << EOF
import whisper
print("   Downloading Whisper 'base' model...")
whisper.load_model("base")
print("   ✅ Whisper model downloaded and cached")
EOF

# Test imports
echo ""
echo "🧪 Testing imports..."
python3 << EOF
try:
    import torch
    import transformers
    import librosa
    import flask
    import streamlit
    print("   ✅ All core dependencies imported successfully")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    exit(1)
EOF

# Create test samples README
echo ""
echo "📝 Setting up test samples directory..."
python3 test_samples.py --setup

# Success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Quick Start Commands:"
echo ""
echo "   1. Activate environment:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Run CLI demo:"
echo "      python demo.py --file sample.wav --mode single"
echo ""
echo "   3. Start dashboard:"
echo "      streamlit run app.py"
echo ""
echo "   4. Start API server:"
echo "      python app.py --mode api --port 5000"
echo ""
echo "   5. Run tests:"
echo "      pytest"
echo ""
echo "📚 See README.md for detailed documentation"
echo ""

