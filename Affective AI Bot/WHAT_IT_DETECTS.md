# 🎭 What Your AffectiveCore Project Detects

## 🎯 Core Capabilities

### **7 Emotions Detected:**
1. **😊 JOY** - Happiness, excitement, pleasure
2. **😢 SADNESS** - Sorrow, grief, disappointment
3. **😠 ANGER** - Rage, frustration, irritation
4. **😨 FEAR** - Anxiety, worry, terror
5. **🤢 DISGUST** - Revulsion, aversion, dislike
6. **😲 SURPRISE** - Shock, amazement, astonishment
7. **😐 NEUTRAL** - Calm, no strong emotion

---

## 📊 What Else It Detects

### **Intensity (3 Levels):**
- **LOW** (0-40%) - Subtle, mild emotion
- **MEDIUM** (40-70%) - Moderate, clear emotion
- **HIGH** (70-100%) - Strong, intense emotion

### **Confidence Score:**
- **0-100%** - How certain the system is about the detection
- Based on multimodal fusion of text + tone

### **Emotional Breakdown:**
- Text emotion scores (what you SAY)
- Tone emotion scores (how you SAY it)
- Fused emotion scores (combined)

---

## 🎙️ Audio Types Supported

### **1. Speech Audio (Multimodal Mode)**
- Voice recordings with words
- Phone calls, interviews, conversations
- **Analyzes:**
  - ✅ Words/phrases (linguistic)
  - ✅ Voice tone (paralinguistic)
  - ✅ Fusion of both

### **2. Non-Speech Audio (Tone-Only Mode)**
- Vocal bursts: laughs, cries, sighs, screams
- Humming, singing (wordless)
- Emotional vocalizations
- **Analyzes:**
  - ✅ Voice tone only (acoustic features)

### **3. File Formats:**
- WAV, MP3, FLAC, OGG, M4A
- Any sample rate (auto-converted)
- Mono or stereo (auto-converted)

---

## 🔬 Analysis Methods

### **📝 Linguistic Analysis (Text Emotion)**
Uses AI to understand **what is said**:
- **Whisper AI** - Transcribes speech to text
- **DistilRoBERTa** - NLP model analyzes emotion from words

**Examples:**
- "I'm so happy!" → **JOY** (high confidence)
- "This is terrible!" → **DISGUST/ANGER**
- "I'm scared" → **FEAR**

### **🎵 Paralinguistic Analysis (Tone Emotion)**
Analyzes **how it's said** using acoustic features:
- **Pitch/F0** - High → Joy/Fear, Low → Sadness
- **Energy/Volume** - High → Anger/Joy, Low → Sadness
- **Speech Rate** - Fast → Anger/Fear, Slow → Sadness
- **Voice Quality** - Tremor, roughness, breathiness
- **Spectral Features** - Frequency distribution patterns

### **🔀 Multimodal Fusion**
Combines both for best accuracy:
- Text Weight: **65%** (what you say)
- Tone Weight: **35%** (how you say it)
- Dynamic adjustment based on confidence
- Temporal smoothing (averages last 3 predictions)

---

## 🎬 Output Format

### **JSON Response:**
```json
{
  "emotion": "joy",
  "intensity": "High",
  "confidence": 0.872,
  "transcription": "I'm so excited about this!",
  "breakdown": {
    "text_emotion": {"joy": 0.91, "surprise": 0.06},
    "tone_emotion": {"joy": 0.78, "neutral": 0.15},
    "fused_emotion": {"joy": 0.87, "surprise": 0.08}
  },
  "action_trigger": {
    "led_color": "#FFD700",
    "quote_category": "joy",
    "servo_gesture": "wave"
  }
}
```

### **ESP32 Action Triggers (for IoT):**
- **LED Color** - Changes based on emotion
  - Joy → Gold (#FFD700)
  - Anger → Red (#FF0000)
  - Sadness → Blue (#0000FF)
  - Fear → Purple (#800080)
  - Disgust → Green (#228B22)
  - Surprise → Orange (#FFA500)
  - Neutral → White (#FFFFFF)
- **Quote Category** - Emotion-appropriate message
- **Servo Gesture** - Physical movement (nod, wave, recoil)
- **Buzzer Pattern** - Alert sound

---

## ⚡ Performance Specifications

| Metric | Value |
|--------|-------|
| **Latency** | <2 seconds (avg 0.685s) |
| **Mode** | Offline-first (no internet) |
| **Streaming** | Real-time with chunking |
| **Accuracy** | 60-90% (audio dependent) |
| **Robustness** | Handles noise, silence, non-speech |

---

## 📊 Example Detections

### **Example 1: Angry Speech**
**Input:** "I can't believe you did this to me!" (angry tone)

**Output:**
- Emotion: **ANGER**
- Intensity: **High**
- Confidence: **87%**
- Text says: Anger (confrontational words)
- Tone says: Anger (loud, fast, high pitch)

### **Example 2: Mixed Signals**
**Input:** "Kids are talking by the door" (happy tone)

**Output:**
- Emotion: **JOY**
- Intensity: **Medium**
- Confidence: **65%**
- Text says: Neutral (neutral words)
- Tone says: Joy (cheerful, upbeat voice)
- **System detects emotion from tone!**

### **Example 3: Non-Speech**
**Input:** [Crying sound - no words]

**Output:**
- Emotion: **SADNESS**
- Intensity: **High**
- Confidence: **72%**
- Mode: **Tone-only** (non-speech audio)
- Tone says: Sadness (low pitch, low energy)

---

## 🎯 Real-World Use Cases

### **1. Customer Service** 💬
- Detect frustrated/angry customers
- Alert supervisors for intervention
- Track satisfaction trends
- Real-time agent coaching

### **2. Mental Health** 🏥
- Monitor emotional states over time
- Detect depression/anxiety indicators
- Track therapy progress
- Early intervention alerts

### **3. Gaming/VR** 🎮
- Adaptive game difficulty based on emotion
- NPC reactions to player emotion
- Immersive emotional feedback
- Player engagement tracking

### **4. Social Robotics** 🤖
- Empathetic robot responses
- Emotion-aware interactions
- LED/gesture feedback
- Natural human-robot communication

### **5. Education** 🎓
- Student engagement tracking
- Detect confusion/frustration
- Adaptive learning pace
- Teacher assistance alerts

### **6. Call Centers** 📞
- Real-time agent assistance
- Quality monitoring
- Escalation triggers
- Customer sentiment analysis

---

## 🎓 Technical Features

- ✅ **Multimodal** - Text + Acoustic fusion
- ✅ **Offline-first** - No internet required
- ✅ **Real-time** - Streaming with <2s latency
- ✅ **Graceful degradation** - Falls back to tone-only
- ✅ **Production-ready** - REST API + Web UI
- ✅ **Configurable** - Tune weights, thresholds via YAML
- ✅ **Extensible** - Add new emotions/features
- ✅ **Benchmarked** - Tested on RAVDESS (33K+ samples)

---

## 🚀 Quick Start

**1. Open Dashboard:**
```
http://localhost:8501
```

**2. Test Files:**
- **Speech:** `Data/Audio_Speech_Actors_01-24/Actor_01/*.wav`
- **Non-Speech:** `Data/EmoGator/*.mp3`

**3. Upload & Analyze:**
- Drag & drop files
- Click "Analyze Emotion"
- See results instantly!

---

## 📚 Summary

Your **AffectiveCore** project is a complete **Multimodal Speech Emotion Detection System** that:

1. **Detects** 7 emotions from audio
2. **Measures** intensity and confidence
3. **Analyzes** both what you say AND how you say it
4. **Works** with speech and non-speech audio
5. **Outputs** JSON + IoT action triggers
6. **Processes** in real-time (<2s latency)
7. **Runs** offline (no internet needed)

**It's production-ready and ready to demo!** 🎭

