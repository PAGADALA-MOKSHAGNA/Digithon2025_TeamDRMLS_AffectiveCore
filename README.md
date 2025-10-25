# Affective AI Bot - Smart Emotional Companion Robot

## Abstarct

The Affective AI BOT is a Smart Emotional Companion Robot designed to bridge the gap between artificial intelligence and human emotion. By integrating facial expression and voice tone analysis, the system detects a user’s emotional state and responds empathetically through motivational quotes, color cues, and movement.  

- Built using an ESP32-CAM, servo mechanisms, and a lightweight AI model, it transforms ordinary surveillance into meaningful interaction.
- Turning the phrase “Smile, the CCTV is filming you” into reality. The prototype emphasizes real-time emotion recognition, low-cost design, and social well-being enhancement through humanized technology.

## 1. Speech - Based Emotion Detection

While facial expressions provide strong cues about emotion, they often fail to capture subtler or internalized moods. Human speech, on the other hand, carries rich emotional information — not only through the words spoken but also through how they are spoken: **tone, pitch, energy, and rhythm.**  

---
**Statement** - Design and develop a Speech-Based Emotion Detection Module that can analyze a user’s spoken input and identify their current emotional state or mental mood.

1. Linguistic emotion cues — inferred from the content of the speech (text meaning),
2. Acoustic emotion cues — derived from vocal tone, prosody, pitch variation, and intensity.(Optional, can be in future enhancement).

### Functional Requirments

1. **Speech to Text Conversion** - Convert user speech into text using reliable ASR (Automatic Speech Recognition) tools such as Google Speech-to-Text API, Vosk, or Whisper.
2. **Text - Based Emotion Analysis (NLP)** - Apply NLP models (e.g., BERT-based Emotion Classifier, DistilRoBERTa, or simple sentiment lexicons) to interpret emotional polarity and specific categories such as joy, sadness, anger, fear, disgust, surprise, or neutral from the spoken words.
3. **Voice - Tone Analysis** - Extract features such as pitch, energy, MFCCs, spectral flux, and voice tremor using a toolkit like OpenSMILE, Librosa, or pyAudioAnalysis.
    - These features help detect stress, crying, trembling, or frustration even when the words are neutral.
4. **Emotion Fusion & Intensity Estimation** - Combine results from both text and tone analysis using a weighted fusion model (e.g., simple averaging or confidence-based fusion).
    - Map into three catregories 1. Low, 2. Medium, 3. High/Extreme
5. **Output Integration** - Pass the detected emotion label and intensity to the Response Generation Module to trigger suitable actions — motivational quote, soothing voice, color feedback, or alert response.
