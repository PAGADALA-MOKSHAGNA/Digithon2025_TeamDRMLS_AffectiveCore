"""
CREMA-D Dataset Downloader and Setup Script

CREMA-D (Crowd-Sourced Emotional Multimodal Actors Dataset)
- 7,442 audio clips
- 91 actors (48 male, 43 female)
- 12 sentences spoken with 6 emotions
- Emotions: Anger, Disgust, Fear, Happy, Neutral, Sad
- Perfect for acoustic feature calibration!

Usage:
    python download_cremad.py
"""

import os
import sys
from pathlib import Path

def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║              🎭 CREMA-D Dataset Setup Instructions 🎭          ║
╚════════════════════════════════════════════════════════════════╝

📊 DATASET INFO:
   Name:     CREMA-D (Crowd-Sourced Emotional Multimodal Actors)
   Size:     ~2.5 GB
   Files:    7,442 audio clips (WAV format)
   Emotions: Anger, Disgust, Fear, Happy, Neutral, Sad
   Duration: 2-5 seconds per clip
   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 DOWNLOAD LINK:

Option 1: Kaggle (Easiest - No login required for CLI)
   
   Step 1: Install Kaggle CLI
   $ pip install kaggle
   
   Step 2: Download dataset
   $ kaggle datasets download -d ejlok1/cremad
   
   Step 3: Extract to Data/CREMA-D/
   $ unzip cremad.zip -d Data/CREMA-D/

Option 2: Direct GitHub Download
   
   $ cd Data/CREMA-D/
   $ wget https://github.com/CheyneyComputerScience/CREMA-D/raw/master/AudioWAV.zip
   $ unzip AudioWAV.zip

Option 3: Manual Download (Browser)
   
   1. Visit: https://www.kaggle.com/datasets/ejlok1/cremad
   2. Click "Download" button
   3. Save to: {os.getcwd()}/Data/CREMA-D/
   4. Extract the ZIP file

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 FILE NAMING CONVENTION:

Each file is named: <ActorID>_<SentenceID>_<Emotion>_<IntensityLevel>.wav

Example: 1001_IEO_ANG_HI.wav
   1001     = Actor ID
   IEO      = Sentence ID
   ANG      = Anger emotion
   HI       = High intensity

Emotions codes:
   ANG = Anger
   DIS = Disgust
   FEA = Fear
   HAP = Happy
   NEU = Neutral
   SAD = Sad

Intensity:
   LO = Low
   MD = Medium
   HI = High
   XX = Unspecified

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ AFTER DOWNLOAD:

Run the test script to benchmark your system:
   $ python test_cremad.py

This will:
   ✓ Test your system on all 7,442 clips
   ✓ Calculate accuracy per emotion
   ✓ Analyze acoustic feature patterns
   ✓ Suggest optimal threshold values
   ✓ Generate calibration recommendations

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 QUICK START (Recommended):

# Install Kaggle CLI
pip install kaggle

# Download dataset
cd "{os.getcwd()}"
kaggle datasets download -d ejlok1/cremad

# Extract
unzip cremad.zip -d Data/CREMA-D/

# Run benchmark
python test_cremad.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏳ EXPECTED TIME:
   Download:  5-10 minutes (2.5 GB)
   Extract:   2-3 minutes
   Benchmark: 30-40 minutes (7,442 clips × 0.7s each)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    # Check if already downloaded
    cremad_path = Path("Data/CREMA-D")
    if cremad_path.exists():
        wav_files = list(cremad_path.glob("**/*.wav"))
        if len(wav_files) > 0:
            print(f"✅ Found {len(wav_files)} audio files in Data/CREMA-D/")
            print("\nReady to run benchmark!")
            print("\nNext step: python test_cremad.py")
            return
    
    print("\n📥 Waiting for you to download the dataset...")
    print("\nOnce downloaded, run this script again to verify!")

if __name__ == "__main__":
    main()

