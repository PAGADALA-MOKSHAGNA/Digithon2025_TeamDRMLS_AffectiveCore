#!/usr/bin/env python3
"""
Create a simple synthetic audio file for testing.
"""

import numpy as np
import soundfile as sf

def create_test_audio(filename='test_samples/test_audio.wav', duration=3.0, sample_rate=16000):
    """Create a simple synthetic audio with voice-like frequencies."""
    
    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a voice-like signal with varying pitch
    # Fundamental frequency around 180 Hz (typical male voice)
    f0 = 180
    
    # Add harmonics to simulate voice
    audio = 0.3 * np.sin(2 * np.pi * f0 * t)  # Fundamental
    audio += 0.15 * np.sin(2 * np.pi * 2 * f0 * t)  # 2nd harmonic
    audio += 0.08 * np.sin(2 * np.pi * 3 * f0 * t)  # 3rd harmonic
    
    # Add some amplitude modulation (like speech)
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)
    audio = audio * envelope
    
    # Add a bit of noise for realism
    audio += 0.01 * np.random.randn(len(audio))
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.7
    
    # Save as WAV file
    sf.write(filename, audio.astype(np.float32), sample_rate)
    print(f"✅ Created test audio: {filename}")
    print(f"   Duration: {duration}s, Sample rate: {sample_rate}Hz")
    
    return filename

if __name__ == '__main__':
    create_test_audio()

