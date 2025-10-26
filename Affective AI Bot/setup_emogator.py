#!/usr/bin/env python3
"""
Setup EmoGator dataset for non-speech emotion detection.
"""

import sys
from pathlib import Path
import json

print("""
╔════════════════════════════════════════════════════════════════╗
║         🎤 EmoGator Dataset Setup 🎤                           ║
╚════════════════════════════════════════════════════════════════╝

EmoGator contains 32,130 non-speech vocal bursts:
• Laughter, sighs, moans, groans, gasps
• 30 emotion categories
• 357 contributors
• Balanced dataset (90 samples per contributor)

""")

# Check if dataset exists
emogator_path = Path("Data/EmoGator-main")
if not emogator_path.exists():
    print(f"❌ EmoGator dataset not found at: {emogator_path}")
    sys.exit(1)

mp3_path = emogator_path / "data" / "mp3"
if not mp3_path.exists():
    print(f"❌ MP3 directory not found at: {mp3_path}")
    sys.exit(1)

# Count files
mp3_files = list(mp3_path.glob("*.mp3"))
print(f"✅ Found {len(mp3_files)} MP3 files\n")

# Load category names
category_file = emogator_path / "data" / "category_names.pt"
if category_file.exists():
    try:
        import torch
        categories = torch.load(category_file)
        print(f"📋 Emotion Categories ({len(categories)}):")
        for i, cat in enumerate(categories, 1):
            print(f"   {i:2d}. {cat}")
    except Exception as e:
        print(f"⚠️  Could not load categories: {e}")
        categories = [
            'Adoration', 'Amusement', 'Anger', 'Awe', 'Confusion', 
            'Contempt', 'Contentment', 'Desire', 'Disappointment', 
            'Disgust', 'Distress', 'Ecstasy', 'Elation', 'Embarrassment', 
            'Fear', 'Guilt', 'Interest', 'Neutral', 'Pain', 'Pride', 
            'Realization', 'Relief', 'Romantic Love', 'Sadness', 
            'Serenity', 'Shame', 'Surprise (Negative)', 
            'Surprise (Positive)', 'Sympathy', 'Triumph'
        ]
else:
    print("⚠️  Category file not found, using default list")
    categories = [
        'Adoration', 'Amusement', 'Anger', 'Awe', 'Confusion', 
        'Contempt', 'Contentment', 'Desire', 'Disappointment', 
        'Disgust', 'Distress', 'Ecstasy', 'Elation', 'Embarrassment', 
        'Fear', 'Guilt', 'Interest', 'Neutral', 'Pain', 'Pride', 
        'Realization', 'Relief', 'Romantic Love', 'Sadness', 
        'Serenity', 'Shame', 'Surprise (Negative)', 
        'Surprise (Positive)', 'Sympathy', 'Triumph'
    ]

# Map to 7 base emotions
print(f"\n🔀 Mapping 30 categories to 7 base emotions:")

emotion_mapping = {
    # Joy group
    'Amusement': 'joy',
    'Ecstasy': 'joy',
    'Elation': 'joy',
    'Pride': 'joy',
    'Triumph': 'joy',
    'Contentment': 'joy',
    'Serenity': 'joy',
    'Relief': 'joy',
    'Adoration': 'joy',
    'Romantic Love': 'joy',
    
    # Sadness group
    'Sadness': 'sadness',
    'Disappointment': 'sadness',
    'Distress': 'sadness',
    'Sympathy': 'sadness',
    'Guilt': 'sadness',
    'Shame': 'sadness',
    
    # Anger group
    'Anger': 'anger',
    'Contempt': 'anger',
    
    # Fear group
    'Fear': 'fear',
    'Confusion': 'fear',
    'Embarrassment': 'fear',
    
    # Disgust group
    'Disgust': 'disgust',
    'Pain': 'disgust',
    
    # Surprise group
    'Surprise (Negative)': 'surprise',
    'Surprise (Positive)': 'surprise',
    'Awe': 'surprise',
    'Realization': 'surprise',
    
    # Neutral group
    'Neutral': 'neutral',
    'Interest': 'neutral',
    'Desire': 'neutral',
}

for cat, mapped in emotion_mapping.items():
    print(f"   {cat:20s} → {mapped}")

# Save mapping
mapping_file = "emogator_emotion_mapping.json"
with open(mapping_file, 'w') as f:
    json.dump({
        'categories': categories,
        'mapping': emotion_mapping,
        'dataset_path': str(mp3_path),
        'total_files': len(mp3_files)
    }, f, indent=2)

print(f"\n💾 Mapping saved to: {mapping_file}")

print(f"\n✅ EmoGator setup complete!")
print(f"\n🎯 Next steps:")
print(f"   1. Test on EmoGator: python test_emogator.py")
print(f"   2. This will test non-speech sound detection")
print(f"   3. See performance on 30 emotion categories")

print("\n" + "="*70)

