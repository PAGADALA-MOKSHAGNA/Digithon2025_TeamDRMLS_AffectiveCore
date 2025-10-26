#!/usr/bin/env python3
"""
AffectiveCore Startup Script
Starts the dashboard and opens browser automatically
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("\n" + "="*70)
    print("🎭 AffectiveCore - Speech Emotion Detection System 🎭")
    print("="*70 + "\n")

def check_venv():
    """Check if running in virtual environment"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Not running in virtual environment")
        print("   Activate with: source venv/bin/activate\n")
        return False
    return True

def kill_existing():
    """Kill any existing Streamlit processes"""
    try:
        subprocess.run(['pkill', '-f', 'streamlit run app.py'], 
                      stderr=subprocess.DEVNULL)
        time.sleep(1)
    except:
        pass

def start_streamlit():
    """Start Streamlit server"""
    print("🚀 Starting dashboard...\n")
    print("-" * 70)
    print("\n✅ AffectiveCore is starting!\n")
    print("🌐 Your dashboard will open automatically in your browser")
    print("\n📍 Dashboard URLs:")
    print("   • Local:   http://localhost:8501")
    print("   • Network: http://192.168.0.116:8501")
    print("\n" + "-" * 70)
    print("\n💡 Tips:")
    print("   • Upload audio files to detect emotions")
    print("   • Try the Batch Analysis tab for multiple files")
    print("   • Check Statistics tab for performance metrics")
    print("\n🛑 To stop: Press Ctrl+C in this terminal")
    print("\n" + "="*70 + "\n")
    
    # Wait a moment for user to read
    time.sleep(2)
    
    # Open browser
    print("🌐 Opening browser...\n")
    webbrowser.open('http://localhost:8501')
    time.sleep(1)
    
    # Start Streamlit
    try:
        subprocess.run([
            'streamlit', 'run', 'app.py',
            '--server.port', '8501',
            '--server.headless', 'false',
            '--browser.gatherUsageStats', 'false'
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down AffectiveCore...")
        print("   Thank you for using AffectiveCore! 🎭\n")
        sys.exit(0)

def main():
    """Main entry point"""
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Print banner
    print_banner()
    
    # Check environment
    if not check_venv():
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Kill existing instances
    kill_existing()
    
    # Start Streamlit
    start_streamlit()

if __name__ == "__main__":
    main()

