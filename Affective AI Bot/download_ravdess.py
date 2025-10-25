#!/usr/bin/env python3
"""
Script to help download and organize RAVDESS dataset.
"""

print("""
╔════════════════════════════════════════════════════════════════╗
║         RAVDESS Dataset Download Instructions                  ║
╚════════════════════════════════════════════════════════════════╝

The RAVDESS (Ryerson Audio-Visual Database of Emotional Speech) 
is the recommended dataset for benchmarking this system.

📊 Dataset Info:
   • 1,440 emotional speech files
   • 7 emotions (neutral, calm, happy, sad, angry, fearful, disgust, surprised)
   • 24 professional actors
   • High quality audio (48kHz)

📥 Download Steps:

1. Visit: https://zenodo.org/record/1188976

2. Download: "Audio_Speech_Actors_01-24.zip" (about 1.5 GB)

3. Extract to: test_samples/ravdess/

4. Your structure should look like:
   test_samples/
   └── ravdess/
       ├── Actor_01/
       │   ├── 03-01-01-01-01-01-01.wav
       │   ├── 03-01-02-01-01-01-01.wav
       │   └── ...
       ├── Actor_02/
       └── ...

📋 Filename Format (Important!):
   03-01-EM-01-01-01-01.wav
         ^^
         └─ Emotion code:
            01 = neutral
            02 = calm
            03 = happy    → maps to JOY
            04 = sad      → maps to SADNESS
            05 = angry    → maps to ANGER
            06 = fearful  → maps to FEAR
            07 = disgust  → maps to DISGUST
            08 = surprised → maps to SURPRISE

🚀 After Download, Run Benchmark:
   python test_samples.py --ravdess test_samples/ravdess/ --output results.json

This will give you:
   • Overall accuracy
   • Per-emotion precision/recall/F1
   • Confusion matrix
   • Text-only vs Multimodal comparison
   • Latency statistics

═══════════════════════════════════════════════════════════════════
""")

import os
from pathlib import Path

# Create directory structure
ravdess_dir = Path("test_samples/ravdess")
ravdess_dir.mkdir(parents=True, exist_ok=True)

readme_path = ravdess_dir / "README.md"
readme_path.write_text("""# RAVDESS Dataset

Download from: https://zenodo.org/record/1188976

Extract "Audio_Speech_Actors_01-24.zip" here.

After extraction, run:
```bash
python test_samples.py --ravdess test_samples/ravdess/ --output results.json
```

## Expected Structure

```
ravdess/
├── Actor_01/
│   ├── 03-01-01-01-01-01-01.wav
│   ├── 03-01-02-01-01-01-01.wav
│   └── ...
├── Actor_02/
└── ...
```

## Filename Format

`03-01-EM-IN-ST-RE-AC.wav`

Where:
- EM = Emotion (01=neutral, 02=calm, 03=happy, 04=sad, 05=angry, 06=fear, 07=disgust, 08=surprised)
- IN = Intensity (01=normal, 02=strong)
- ST = Statement (01="Kids are talking by the door", 02="Dogs are sitting by the door")
- RE = Repetition (01=1st, 02=2nd)
- AC = Actor (01-24)
""")

print(f"\n✅ Created directory structure at: {ravdess_dir}")
print(f"✅ Created README with instructions")
print(f"\n📥 Next: Download the dataset and extract it to {ravdess_dir}/")

