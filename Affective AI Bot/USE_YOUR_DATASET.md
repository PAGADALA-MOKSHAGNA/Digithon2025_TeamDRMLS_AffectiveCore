# 🎤 Using Your Own Voice Dataset

This guide shows how to use your custom voice dataset to test, benchmark, and improve the emotion detection system.

---

## 📋 Dataset Requirements

### Minimum Requirements

**Audio Format:**
- `.wav`, `.mp3`, `.flac`, or `.ogg`
- 16kHz or higher sample rate (will auto-resample)
- Mono or stereo (will convert to mono)
- Contains actual speech (not just tones)

**Labeling:**
- Know the true emotion for each file
- One of: joy, sadness, anger, fear, disgust, surprise, neutral

---

## 🗂️ Option 1: Organized Directory Structure

**Best for: Large labeled datasets**

### Structure

```
test_samples/
└── my_dataset/
    ├── joy/
    │   ├── sample1.wav
    │   ├── sample2.wav
    │   └── ...
    ├── sadness/
    │   ├── sample1.wav
    │   └── ...
    ├── anger/
    │   ├── sample1.wav
    │   └── ...
    ├── fear/
    ├── disgust/
    ├── surprise/
    └── neutral/
```

### Run Benchmark

```bash
python test_your_dataset.py --dir test_samples/my_dataset/
```

---

## 📝 Option 2: CSV Metadata File

**Best for: Mixed organization or detailed metadata**

### Create metadata.csv

```csv
filename,emotion,intensity,speaker,notes
audio1.wav,joy,high,speaker1,Birthday celebration
audio2.wav,sadness,medium,speaker2,Bad news
audio3.wav,anger,high,speaker1,Frustrated
audio4.wav,neutral,low,speaker3,Weather report
```

### Run Benchmark

```bash
python test_your_dataset.py --csv metadata.csv --audio-dir test_samples/my_audio/
```

---

## 🚀 Quick Test: Single File

### Test One Audio File

```bash
# Activate environment
source venv/bin/activate

# Analyze with verbose output
python demo.py --file your_audio.wav --mode single --verbose
```

### Example Output

```
📝 Transcription: "I am so excited about this!"

😊 Detected Emotion: JOY
💪 Intensity: High
🎯 Confidence: 85.3%
⏱️  Latency: 1.234s

📊 Detailed Breakdown:
   Text Emotions:
      joy:      0.920 ████████████████████
      surprise: 0.050 ███
      neutral:  0.020 █

   Tone Emotions:
      joy:      0.780 ████████████████
      surprise: 0.120 ███████
      neutral:  0.080 █████

   Acoustic Features:
      Pitch (mean): 220.5 Hz    ← High pitch
      Pitch (std):  35.2 Hz     ← High variation
      Energy:       0.072        ← High energy
      Speech Rate:  4.8 syll/s  ← Fast speech
```

---

## 📊 Batch Testing & Metrics

### Run Full Benchmark

```bash
# Test entire dataset
python test_your_dataset.py --dir test_samples/my_dataset/ --output results.json

# Or with CSV
python test_your_dataset.py --csv metadata.csv --audio-dir test_samples/audio/ --output results.json
```

### What You'll Get

```
📊 EMOTION DETECTION BENCHMARK REPORT
══════════════════════════════════════════════════════════════

📈 Overall Statistics:
   Total Samples: 120
   Labeled Samples: 120
   Accuracy: 76.7%                    ← Overall performance
   Avg Confidence: 71.2%
   Avg Latency: 1.345s                ← Processing speed
   Fallback Rate: 3.3%                ← Times it used text-only

📊 Per-Emotion Performance:

   Emotion      Samples  Precision     Recall         F1
   ------------ -------- ---------- ---------- ----------
   joy               20      82.4%      85.0%      83.7%
   sadness           20      79.3%      75.0%      77.1%
   anger             20      73.5%      80.0%      76.6%
   fear              20      68.2%      65.0%      66.6%
   disgust           20      71.8%      70.0%      70.9%
   surprise          20      75.6%      73.0%      74.3%
   neutral           20      70.1%      72.0%      71.0%

🔀 Confusion Matrix:
                                 Predicted
   GT      joy    sad    anger  fear   disgust surprise neutral
   joy      17     1      0      0      0       2        0
   sadness   1    15      2      1      1       0        0
   anger     1     2     16      0      1       0        0
   fear      2     1      0     13      1       2        1
   ...

💡 Insights:
   • Best performing: Joy (83.7% F1)
   • Most confused: Fear ↔ Surprise (common)
   • Multimodal improvement: +12.3% vs text-only
```

---

## 📈 See Improvements: Before & After

### 1. Baseline Performance

```bash
# Run initial benchmark
python test_your_dataset.py --dir test_samples/my_dataset/ --output baseline.json
```

### 2. Tune the System

Edit `config.yaml` to adjust parameters:

```yaml
# Try different fusion weights
fusion:
  text_weight: 0.70  # Increase text weight (was 0.65)
  
  # Adjust intensity thresholds
  intensity:
    low: 0.45      # Lower threshold (was 0.5)
    medium: 0.70   # Lower threshold (was 0.75)

# Adjust acoustic feature ranges
acoustic:
  pitch:
    low: 75       # Adjust for your speakers
    neutral: 160
    high: 280
```

### 3. Re-run and Compare

```bash
# Run again with new settings
python test_your_dataset.py --dir test_samples/my_dataset/ --output improved.json

# Compare results
python compare_results.py baseline.json improved.json
```

---

## 🎯 Improvement Strategies

### Strategy 1: Adjust Fusion Weights

**When to use:**
- Text is very accurate but tone is noisy → Increase text_weight
- Tone captures emotion better → Decrease text_weight

**How:**
```yaml
fusion:
  text_weight: 0.75  # Range: 0.4 - 0.9
```

### Strategy 2: Calibrate Acoustic Ranges

**When to use:**
- Your speakers have different pitch ranges
- Recording quality differs

**How:**
```bash
# Analyze your dataset's acoustic properties
python analyze_acoustic_ranges.py --dir test_samples/my_dataset/

# It will suggest optimal ranges for config.yaml
```

### Strategy 3: Fine-tune Emotion Mapping

**When to use:**
- Specific emotions consistently misclassified

**Edit:** `voice_tone.py` lines 250-350 (acoustic → emotion rules)

### Strategy 4: Adjust Confidence Thresholds

**When to use:**
- Too many low-confidence predictions
- Or too many overconfident wrong predictions

**How:**
```yaml
nlp:
  min_confidence: 0.35  # Lower to accept more (was 0.4)

# Or adjust per-emotion in voice_tone.py
```

---

## 📊 Visualization & Analysis

### Generate Visualizations

```bash
# Creates charts and graphs
python visualize_results.py results.json

# Outputs:
# - confusion_matrix.png
# - emotion_distribution.png
# - confidence_histogram.png
# - latency_over_time.png
```

### Launch Dashboard for Interactive Analysis

```bash
streamlit run app.py

# Upload your files via drag-and-drop
# See real-time analysis
# Compare multiple files
```

---

## 🔬 Advanced: Compare Modalities

### Test Text-Only vs Multimodal

```python
from emotion_detection import EmotionDetectionPipeline

pipeline = EmotionDetectionPipeline('config.yaml')

# Temporarily disable acoustic features
pipeline.config['fusion']['text_weight'] = 1.0  # 100% text

result_text_only = pipeline.analyze_audio_file('audio.wav')

# Re-enable fusion
pipeline.config['fusion']['text_weight'] = 0.65

result_multimodal = pipeline.analyze_audio_file('audio.wav')

# Compare
print(f"Text-only: {result_text_only['emotion']}")
print(f"Multimodal: {result_multimodal['emotion']}")
```

---

## 💡 Example: Real Improvement Workflow

### Step-by-Step

```bash
# 1. Organize your dataset
mkdir -p test_samples/my_emotions/{joy,sadness,anger,fear,disgust,surprise,neutral}
# Copy your labeled audio files to respective folders

# 2. Initial benchmark
python test_your_dataset.py --dir test_samples/my_emotions/ --output v1_baseline.json
# Result: 68% accuracy

# 3. Analyze acoustic ranges
python analyze_acoustic_ranges.py --dir test_samples/my_emotions/
# Suggests: pitch_high: 290 (instead of 250)

# 4. Update config.yaml with suggestions

# 5. Test again
python test_your_dataset.py --dir test_samples/my_emotions/ --output v2_tuned.json
# Result: 74% accuracy (+6% improvement!)

# 6. Compare
python compare_results.py v1_baseline.json v2_tuned.json
# Shows which emotions improved most
```

---

## 🎤 Creating Your Own Dataset

### Recording Tips

**Good Recordings:**
- Clear speech (not too far from mic)
- Minimal background noise
- Natural emotional expression
- 3-10 seconds duration
- Multiple speakers (diversity)

**Emotion Recording Scripts:**

```
Joy:
- "I'm so excited about this amazing news!"
- "This is the best day of my life!"
- "I can't believe we actually did it!"

Sadness:
- "I'm feeling really down today."
- "This is so disappointing."
- "I can't help but feel sad about this."

Anger:
- "This is absolutely unacceptable!"
- "I can't believe they did this to me!"
- "This is making me so frustrated!"

Fear:
- "I'm really worried about what might happen."
- "This is making me nervous."
- "I'm scared something bad will occur."

... (See demo script for more)
```

---

## 📞 Troubleshooting

### Low Accuracy?

1. **Check transcription quality:**
   - Run with `--verbose` to see what Whisper transcribes
   - If transcription is wrong, the text emotion will be wrong

2. **Check audio quality:**
   - Is there too much background noise?
   - Is the speech clear?

3. **Check label accuracy:**
   - Are your emotion labels correct?
   - Is the emotion subjective/ambiguous?

### High Latency?

1. Use smaller Whisper model: `model: "tiny"` in config.yaml
2. Or switch to Vosk: `engine: "vosk"`
3. Use GPU if available: `device: "cuda"`

### Mixed Results?

- Some emotions are harder (fear/surprise often confused)
- Sarcasm is inherently difficult
- Neutral can be subjective

---

## 🎯 Success Metrics

**Good Performance:**
- Overall accuracy > 70%
- Per-emotion F1 > 0.65
- Latency < 2s
- Multimodal improves over text-only

**Excellent Performance:**
- Overall accuracy > 80%
- Per-emotion F1 > 0.75
- Latency < 1.5s
- Clear emotion separation in confusion matrix

---

**Ready to test? Let me know if you have a dataset and I'll help you get started!** 🚀

