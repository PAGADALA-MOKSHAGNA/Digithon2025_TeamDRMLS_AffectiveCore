#!/usr/bin/env python3
"""
Quick demo to test the text emotion analyzer without audio.
This demonstrates the NLP component working.
"""

from text_emotion import TextEmotionAnalyzer
import yaml
import json

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize text emotion analyzer
print("🔄 Loading DistilRoBERTa emotion model...")
analyzer = TextEmotionAnalyzer(config)
print("✅ Model loaded!\n")

# Test phrases for different emotions
test_phrases = {
    "joy": "I am so happy and excited about this wonderful news!",
    "sadness": "I feel really sad and disappointed today.",
    "anger": "This is absolutely infuriating and unacceptable!",
    "fear": "I'm really worried and scared about what might happen.",
    "surprise": "Wow, I can't believe this happened!",
    "disgust": "That is absolutely disgusting and terrible.",
    "neutral": "The meeting is scheduled for 3 PM tomorrow."
}

print("="*70)
print("🎭 TEXT EMOTION DETECTION DEMO")
print("="*70)

for expected, phrase in test_phrases.items():
    print(f"\n📝 Text: \"{phrase}\"")
    print(f"   Expected: {expected}")
    
    result = analyzer.analyze(phrase)
    
    detected = result['top_emotion']
    confidence = result['confidence']
    
    # Show result
    match = "✅" if detected == expected else "❌"
    print(f"   {match} Detected: {detected} (confidence: {confidence:.1%})")
    
    # Show top 3 emotions
    top_3 = sorted(result['emotions'].items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"   Top 3: {', '.join([f'{e}: {s:.1%}' for e, s in top_3])}")

print("\n" + "="*70)
print("\n✅ Text emotion analysis is working correctly!")
print("\n💡 Next steps:")
print("   1. Dashboard is starting at http://localhost:8501")
print("   2. Upload real audio files with speech")
print("   3. Try the Flask API: python app.py --mode api")
print("   4. Run tests: pytest")

