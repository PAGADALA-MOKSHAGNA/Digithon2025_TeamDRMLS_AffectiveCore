#!/bin/bash

# AffectiveCore Startup Script
# This script starts the dashboard with clickable links

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        🎭 Starting AffectiveCore Emotion Detection 🎭         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Loading system..."
echo ""

# Navigate to project directory
cd "/Users/DK19/Downloads/Affective AI Bot"

# Activate virtual environment
source venv/bin/activate

# Clear any previous instances
pkill -f "streamlit run app.py" 2>/dev/null

# Wait a moment
sleep 1

echo "🚀 Starting dashboard..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ AffectiveCore is running!"
echo ""
echo "🌐 Access your dashboard here:"
echo ""
echo "   👉 Local:   http://localhost:8501"
echo "   👉 Network: http://192.168.0.116:8501"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Tip: Click the link above or copy-paste into your browser"
echo ""
echo "🛑 To stop: Press Ctrl+C"
echo ""

# Start Streamlit (this will also display its own links)
streamlit run app.py --server.port 8501 --server.headless=false

