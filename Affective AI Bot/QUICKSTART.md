# 🚀 Quick Start Guide

Get AffectiveCore running in 5 minutes!

---

## Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup.sh

# Activate the environment
source venv/bin/activate

# You're ready!
```

---

## Option 2: Manual Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Download Models

```bash
# Whisper model (automatic on first run, but you can pre-download)
python3 -c "import whisper; whisper.load_model('base')"
```

### 3. Create Directories

```bash
mkdir -p logs test_samples
```

---

## First Run: Analyze Sample Audio

### Create a Test Audio File

Record yourself saying: **"I am so happy today!"**

Save as `test.wav` in the project directory.

### Run Analysis

```bash
python demo.py --file test.wav --mode single --verbose
```

**Expected Output:**
```
🎯 EMOTION DETECTION RESULT
====================================

📝 Transcription: "I am so happy today!"

😊 Detected Emotion: JOY
💪 Intensity: Medium
🎯 Confidence: 78%
⏱️  Latency: 1.234s

🎨 ESP32 Actions:
   • LED Color: yellow
   • Quote Category: inspiring
   • Servo Gesture: wave
```

---

## Launch Dashboard

```bash
streamlit run app.py
```

Opens at: http://localhost:8501

**Features:**
- Upload audio files via drag-and-drop
- Real-time emotion visualization
- Acoustic feature display
- Batch processing
- Performance metrics

---

## Start API Server

```bash
python app.py --mode api --port 5000
```

**Test the API:**
```bash
curl -X POST http://localhost:5000/analyze \
  -F "file=@test.wav"
```

---

## Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html  # Mac
# OR
xdg-open htmlcov/index.html  # Linux
```

---

## Troubleshooting

### Issue: "No module named 'whisper'"

**Solution:**
```bash
pip install openai-whisper
```

### Issue: "CUDA out of memory"

**Solution:** Use CPU or smaller model
```yaml
# Edit config.yaml
asr:
  whisper:
    model: "tiny"  # Change from "base"
    device: "cpu"  # Change from "cuda"
```

### Issue: Slow performance

**Solutions:**
1. Use smaller model (tiny)
2. Disable noise reduction in config.yaml
3. Use Vosk instead of Whisper
4. Enable GPU if available

### Issue: "Permission denied" on setup.sh

**Solution:**
```bash
chmod +x setup.sh
```

---

## Next Steps

1. **Read the full documentation:** [README.md](README.md)
2. **Try the demo script:** [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
3. **Customize configuration:** Edit `config.yaml`
4. **Run benchmarks:** `python test_samples.py --setup`
5. **Integrate with ESP32:** See README.md → ESP32 Integration

---

## Configuration Quick Reference

### Switch to Vosk (faster, less accurate)

```yaml
# config.yaml
asr:
  engine: "vosk"  # Change from "whisper"
```

### Adjust Fusion Weights

```yaml
# config.yaml
fusion:
  text_weight: 0.7  # Increase to trust text more
  tone_weight: 0.3  # Decrease tone weight
```

### Enable MQTT for ESP32

```yaml
# config.yaml
mqtt:
  enabled: true
  broker: "192.168.1.100"  # Your ESP32 IP
  topic: "affective/emotion"
```

---

## Common Commands Cheatsheet

```bash
# Analyze single file
python demo.py --file audio.wav --mode single

# Verbose output
python demo.py --file audio.wav --verbose

# Save to JSON
python demo.py --file audio.wav --output result.json

# Stream from microphone
python demo.py --device 0 --mode stream

# Run benchmarks
python test_samples.py --dir test_samples/

# Start dashboard
streamlit run app.py

# Start API
python app.py --mode api

# Run tests
pytest

# Check code style
black .
flake8 .
```

---

## Example Output (JSON)

```json
{
  "timestamp": "2025-10-25T18:58:00Z",
  "transcription": "I am so happy today",
  "emotion": "joy",
  "intensity": "Medium",
  "confidence": 0.78,
  "breakdown": {
    "text_emotion": {
      "joy": 0.85,
      "neutral": 0.08,
      "surprise": 0.04
    },
    "tone_emotion": {
      "joy": 0.72,
      "neutral": 0.15,
      "surprise": 0.08
    },
    "acoustic_features": {
      "pitch_mean": 210.5,
      "pitch_std": 25.3,
      "energy": 0.065,
      "speech_rate": 4.2
    }
  },
  "action_trigger": {
    "led_color": "yellow",
    "quote_category": "inspiring",
    "servo_gesture": "wave"
  },
  "notes": {
    "fusion_alpha": 0.75,
    "fallback_mode": false,
    "mixed_emotion": false
  }
}
```

---

## Getting Help

- **Documentation:** README.md
- **Demo Guide:** DEMO_SCRIPT.md
- **Configuration:** config.yaml (with comments)
- **Examples:** Check `tests/` for usage examples

---

**Ready to detect emotions! 🎭**

