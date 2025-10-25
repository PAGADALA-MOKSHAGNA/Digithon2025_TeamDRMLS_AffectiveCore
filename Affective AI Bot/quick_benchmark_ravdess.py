#!/usr/bin/env python3
"""
Quick benchmark on RAVDESS dataset.
This will test your system on 1,440 professional recordings!
"""

import sys
from pathlib import Path

print("""
╔════════════════════════════════════════════════════════════════╗
║             🎭 RAVDESS BENCHMARK STARTING 🎭                   ║
╚════════════════════════════════════════════════════════════════╝

📊 Testing on RAVDESS dataset:
   • 1,440 professional emotional speech recordings
   • 24 actors (12 male, 12 female)
   • 7 emotions: neutral, calm, happy, sad, angry, fearful, disgust
   • Gold standard for emotion recognition

⏱️  This will take approximately 30-60 minutes...

""")

# Check if dataset exists
ravdess_path = Path("test_samples/ravdess")
if not ravdess_path.exists():
    print(f"❌ RAVDESS dataset not found at: {ravdess_path}")
    print(f"\n💡 Run this first:")
    print(f"   ln -s '../Data/Audio_Speech_Actors_01-24' test_samples/ravdess")
    sys.exit(1)

# Check number of actors
actors = list(ravdess_path.glob("Actor_*"))
print(f"✅ Found {len(actors)} actors")

if len(actors) == 0:
    print(f"❌ No actors found in {ravdess_path}")
    sys.exit(1)

# Count files
total_files = sum(1 for actor in actors for _ in actor.glob("*.wav"))
print(f"✅ Found {total_files} audio files\n")

print("="*70)
print("🚀 Starting benchmark...")
print("="*70 + "\n")

# Run the actual benchmark
from test_samples import EmotionBenchmark, logger
from emotion_detection import EmotionDetectionPipeline

# Initialize
pipeline = EmotionDetectionPipeline('config.yaml')
benchmark = EmotionBenchmark(pipeline)

# Test all files
print(f"Processing {total_files} files...")
print(f"This may take a while. Progress will be shown below.\n")

processed = 0
for actor_dir in sorted(actors):
    actor_name = actor_dir.name
    audio_files = sorted(actor_dir.glob("*.wav"))
    
    print(f"\n📁 {actor_name}: {len(audio_files)} files")
    
    for audio_file in audio_files:
        # Extract emotion from filename
        # Format: 03-01-EM-01-01-01-01.wav
        parts = audio_file.stem.split('-')
        emotion_code = parts[2]
        
        # Map RAVDESS emotion codes
        emotion_map = {
            '01': 'neutral',
            '02': 'neutral',  # calm -> neutral
            '03': 'joy',      # happy -> joy
            '04': 'sadness',
            '05': 'anger',
            '06': 'fear',
            '07': 'disgust',
            '08': 'surprise'
        }
        
        ground_truth = emotion_map.get(emotion_code, 'unknown')
        
        # Test file
        try:
            benchmark.test_file(str(audio_file), ground_truth=ground_truth)
            processed += 1
            
            # Progress indicator
            if processed % 10 == 0:
                progress = (processed / total_files) * 100
                print(f"   Progress: {processed}/{total_files} ({progress:.1f}%)")
                
        except Exception as e:
            print(f"   ⚠️  Error processing {audio_file.name}: {e}")

print("\n" + "="*70)
print("✅ Benchmark Complete!")
print("="*70 + "\n")

# Print report
benchmark.print_report()

# Save results
output_file = "ravdess_benchmark_results.json"
benchmark.save_results(output_file)

print(f"\n💾 Detailed results saved to: {output_file}")
print(f"\n📊 View results:")
print(f"   cat {output_file} | python -m json.tool | less")

print(f"\n🎯 Next steps:")
print(f"   1. Review the confusion matrix to see which emotions are confused")
print(f"   2. Tune config.yaml based on weak areas")
print(f"   3. Re-run to measure improvement")
print(f"   4. Compare with: python compare_results.py baseline.json improved.json")

print("\n" + "="*70)

