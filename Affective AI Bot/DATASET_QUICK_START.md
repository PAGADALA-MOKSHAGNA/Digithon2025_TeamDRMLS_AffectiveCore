# 🎤 Voice Dataset Quick Start

## ✅ Yes! Your Voice Dataset Will Be Very Helpful!

A voice dataset will allow you to:
1. **Test the full multimodal system** (text + tone)
2. **Measure real performance** with metrics
3. **See improvements** after tuning
4. **Compare** before/after results

---

## 🚀 Three Ways to Use Your Dataset

### Option 1: Download RAVDESS (Recommended for Benchmarking)

**The gold standard for emotion detection:**

```bash
# 1. Visit and download (1.5 GB):
open https://zenodo.org/record/1188976

# 2. Download: "Audio_Speech_Actors_01-24.zip"

# 3. Extract to:
unzip Audio_Speech_Actors_01-24.zip -d test_samples/ravdess/

# 4. Run benchmark:
source venv/bin/activate
python test_samples.py --ravdess test_samples/ravdess/ --output ravdess_results.json
```

**You'll get:**
- ✅ Accuracy per emotion
- ✅ Precision/Recall/F1 scores
- ✅ Confusion matrix
- ✅ Latency stats

---

### Option 2: Use Your Own Dataset (Organized by Emotion)

**Best if you have labeled recordings:**

```bash
# 1. Organize your files:
test_samples/my_emotions/
├── joy/
│   ├── recording1.wav
│   └── recording2.wav
├── sadness/
│   ├── recording3.wav
│   └── recording4.wav
├── anger/
├── fear/
├── disgust/
├── surprise/
└── neutral/

# 2. Run test:
source venv/bin/activate
python test_your_dataset.py --dir test_samples/my_emotions/ --output my_results.json
```

**Example output:**
```
📊 EMOTION DETECTION BENCHMARK REPORT
══════════════════════════════════════

📈 Overall Statistics:
   Total Samples: 50
   Accuracy: 72.0%           ← Your baseline!
   Avg Confidence: 68.5%
   Avg Latency: 1.234s

📊 Per-Emotion Performance:
   Emotion      Samples  Precision  Recall    F1
   joy               10     82.4%    80.0%   81.2%  ← Strong!
   sadness           10     75.3%    70.0%   72.6%
   anger             10     68.5%    75.0%   71.6%
   fear              10     62.2%    55.0%   58.4%  ← Needs work
   ...
```

---

### Option 3: Single File Testing (Quick Check)

**Test individual recordings:**

```bash
source venv/bin/activate

# Record yourself or use any audio file
python demo.py --file my_recording.wav --mode single --verbose
```

**You'll see:**
- ✅ Transcription
- ✅ Detected emotion + confidence
- ✅ Text emotion breakdown
- ✅ Tone emotion breakdown
- ✅ Acoustic features (pitch, energy, speech rate)
- ✅ How the fusion worked

---

## 📈 How to See Improvements

### Step-by-Step Improvement Workflow

```bash
# 1. Run baseline
python test_your_dataset.py --dir test_samples/my_emotions/ --output v1_baseline.json
# Result: 68% accuracy

# 2. Edit config.yaml
# Adjust fusion weights, intensity thresholds, etc.

# 3. Test again
python test_your_dataset.py --dir test_samples/my_emotions/ --output v2_improved.json
# Result: 74% accuracy

# 4. Compare!
python compare_results.py v1_baseline.json v2_improved.json
```

**Compare output shows:**
```
📊 PERFORMANCE COMPARISON
══════════════════════════════════════

📈 Overall Performance:
   Accuracy:
      Baseline: 68.0%
      Improved: 74.0%
      Change:   ⬆️ +6.0%        ← Clear improvement!

   Avg Latency:
      Baseline: 1.456s
      Improved: 1.234s
      Change:   ⬇️ -0.222s      ← Faster too!

📊 Per-Emotion F1 Scores:
   Emotion      Baseline   Improved    Change
   joy            81.2%     83.5%    ⬆️ +2.3%
   sadness        72.6%     78.1%    ⬆️ +5.5%  ← Big improvement!
   anger          71.6%     75.2%    ⬆️ +3.6%
   ...

🎉 Significant improvement! (+6.0%)
```

---

## 🎯 What Improvements Look Like

### Example Improvements You Might See:

**1. After Adjusting Fusion Weights:**
```
Before: 68% accuracy (too much weight on noisy tone)
After:  74% accuracy (balanced text/tone)
Change: +6% improvement ✅
```

**2. After Calibrating Acoustic Ranges:**
```
Before: Fear often misclassified as surprise
After:  Fear detection improved from 58% → 72%
Change: +14% F1 for fear ✅
```

**3. After Tuning Intensity Thresholds:**
```
Before: Many emotions marked as "Low" intensity
After:  Better distribution across Low/Medium/High
Change: More nuanced output ✅
```

**4. Multimodal vs Text-Only:**
```
Text-only:   65% accuracy
Multimodal:  74% accuracy
Improvement: +9% from adding tone analysis ✅
```

---

## 📊 Metrics You'll Track

### Automatically Generated Metrics:

1. **Overall Accuracy** - % of correct predictions
2. **Per-Emotion Metrics:**
   - Precision (when it says X, how often is it correct?)
   - Recall (when truth is X, how often does it detect it?)
   - F1 Score (balanced measure)
3. **Confusion Matrix** - Which emotions get confused?
4. **Confidence Distribution** - How sure is the system?
5. **Latency Stats** - Processing speed
6. **Fallback Rate** - How often it falls back to text-only

---

## 🎤 Creating Your Own Test Dataset

### Quick Recording Guide:

**Record 5-10 samples per emotion:**

**Joy:**
- "I'm so excited about this!"
- "This is the best news ever!"
- "I can't believe we did it!"

**Sadness:**
- "I'm feeling really down today."
- "This is so disappointing."
- "I can't help but feel sad."

**Anger:**
- "This is absolutely unacceptable!"
- "I can't believe they did this!"
- "This is making me furious!"

**Fear:**
- "I'm really worried about this."
- "This is making me nervous."
- "I'm scared of what might happen."

**Neutral:**
- "The meeting is at 3 PM."
- "I need to finish this report."
- "The weather is cloudy today."

**Tips:**
- Use different speakers (friends, family)
- Natural expression (don't overact)
- Clear audio (minimize background noise)
- 3-10 seconds per recording
- Save as .wav or .mp3

---

## 🔧 Tuning Parameters for Better Results

### Key Config Settings:

```yaml
# config.yaml

# 1. Fusion weights (how much to trust text vs tone)
fusion:
  text_weight: 0.70  # Increase if text is more reliable
  tone_weight: 0.30  # Or increase if tone captures emotion better

# 2. Intensity thresholds
fusion:
  intensity:
    low: 0.45      # Lower = more classified as medium/high
    medium: 0.70   # Adjust based on your data

# 3. Acoustic ranges (calibrate for your speakers)
acoustic:
  pitch:
    low: 80
    neutral: 150
    high: 250    # Increase if your speakers are higher-pitched

  energy:
    low: 0.01
    neutral: 0.03
    high: 0.08   # Adjust based on recording volume

# 4. Confidence threshold
nlp:
  min_confidence: 0.35  # Lower = accept more predictions
```

---

## 💡 Expected Performance

### Realistic Expectations:

**With Good Dataset (clear audio, natural emotions):**
- Overall accuracy: **70-80%**
- Easy emotions (joy, sadness): **75-85%**
- Harder emotions (fear, disgust): **60-75%**
- Multimodal improvement: **+8-15%** vs text-only

**With RAVDESS (professional actors):**
- Overall accuracy: **72-78%**
- Best: Joy, Anger, Sadness
- Challenging: Fear/Surprise confusion

**With Real-world Data (spontaneous speech):**
- Overall accuracy: **65-75%**
- Higher variation due to naturalistic expression
- Mixed emotions more common

---

## 🚀 Ready to Start?

### Quick Commands:

```bash
# Activate environment
cd "/Users/DK19/Downloads/Affective AI Bot"
source venv/bin/activate

# Test single file
python demo.py --file your_audio.wav --mode single --verbose

# Test full dataset
python test_your_dataset.py --dir test_samples/my_emotions/ --output results.json

# Compare improvements
python compare_results.py baseline.json improved.json

# View documentation
cat USE_YOUR_DATASET.md
```

---

## 📞 Next Steps

1. **Get a dataset** (RAVDESS or record your own)
2. **Run baseline test** to see starting performance
3. **Tune config.yaml** based on results
4. **Re-test** and compare improvements
5. **Iterate** until satisfied

**Questions? Check the documentation or ask!** 🎭

