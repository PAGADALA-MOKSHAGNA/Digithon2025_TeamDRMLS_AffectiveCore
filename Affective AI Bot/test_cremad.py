"""
CREMA-D Benchmark and Calibration Script

Tests the emotion detection system on CREMA-D dataset
and analyzes acoustic features to find optimal thresholds.
"""

import os
import sys
import json
import time
from pathlib import Path
from collections import defaultdict
import numpy as np
from tqdm import tqdm

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from emotion_detection import EmotionDetectionPipeline


# CREMA-D emotion mapping
CREMAD_EMOTIONS = {
    'ANG': 'anger',
    'DIS': 'disgust',
    'FEA': 'fear',
    'HAP': 'joy',  # Map 'happy' to 'joy'
    'NEU': 'neutral',
    'SAD': 'sadness'
}


def parse_cremad_filename(filename):
    """
    Parse CREMA-D filename to extract metadata.
    
    Format: <ActorID>_<SentenceID>_<Emotion>_<Intensity>.wav
    Example: 1001_IEO_ANG_HI.wav
    
    Returns:
        dict with keys: actor_id, sentence_id, emotion, intensity
    """
    parts = filename.stem.split('_')
    if len(parts) >= 4:
        return {
            'actor_id': parts[0],
            'sentence_id': parts[1],
            'emotion_code': parts[2],
            'emotion': CREMAD_EMOTIONS.get(parts[2], 'unknown'),
            'intensity': parts[3]
        }
    return None


def run_benchmark(
    cremad_dir="Data/CREMA-D",
    sample_size=None,
    save_results=True
):
    """
    Run benchmark on CREMA-D dataset.
    
    Args:
        cremad_dir: Path to CREMA-D directory
        sample_size: Number of files to test (None = all)
        save_results: Whether to save detailed results
    """
    print("\n" + "="*70)
    print("🎭 CREMA-D EMOTION DETECTION BENCHMARK")
    print("="*70)
    
    # Find audio files
    cremad_path = Path(cremad_dir)
    audio_files = list(cremad_path.glob("**/*.wav"))
    
    if len(audio_files) == 0:
        print(f"\n❌ No audio files found in {cremad_dir}")
        print("\nPlease download CREMA-D first:")
        print("  python download_cremad.py")
        return
    
    print(f"\n📁 Found {len(audio_files)} audio files")
    
    # Sample if requested
    if sample_size and sample_size < len(audio_files):
        import random
        audio_files = random.sample(audio_files, sample_size)
        print(f"🎲 Randomly selected {sample_size} files for testing")
    
    # Initialize pipeline
    print("\n🔧 Loading emotion detection pipeline...")
    pipeline = EmotionDetectionPipeline('config.yaml')
    print("✅ Pipeline loaded")
    
    # Test each file
    print(f"\n🚀 Processing {len(audio_files)} files...")
    print("This may take 30-40 minutes for full dataset...\n")
    
    results = []
    acoustic_by_emotion = defaultdict(lambda: {
        'pitch': [], 'energy': [], 'rate': [],
        'pitch_std': [], 'zcr': [], 'spectral_centroid': []
    })
    
    correct = 0
    total = 0
    confusion_matrix = defaultdict(lambda: defaultdict(int))
    
    start_time = time.time()
    
    for audio_file in tqdm(audio_files, desc="Processing"):
        # Parse filename
        metadata = parse_cremad_filename(audio_file)
        if not metadata or metadata['emotion'] == 'unknown':
            continue
        
        true_emotion = metadata['emotion']
        
        try:
            # Run detection
            result = pipeline.process_file(
                str(audio_file),
                enable_smoothing=False
            )
            
            if 'error' not in result:
                predicted_emotion = result['emotion']
                confidence = result['confidence']
                
                # Store result
                results.append({
                    'file': audio_file.name,
                    'true_emotion': true_emotion,
                    'predicted_emotion': predicted_emotion,
                    'confidence': confidence,
                    'correct': predicted_emotion == true_emotion,
                    'intensity': metadata['intensity'],
                    **metadata
                })
                
                # Update confusion matrix
                confusion_matrix[true_emotion][predicted_emotion] += 1
                
                # Collect acoustic features by true emotion
                if 'breakdown' in result and 'acoustic_features' in result['breakdown']:
                    features = result['breakdown']['acoustic_features']
                    acoustic_by_emotion[true_emotion]['pitch'].append(features.get('pitch_mean', 0))
                    acoustic_by_emotion[true_emotion]['energy'].append(features.get('energy', 0))
                    acoustic_by_emotion[true_emotion]['rate'].append(features.get('speech_rate', 0))
                    acoustic_by_emotion[true_emotion]['pitch_std'].append(features.get('pitch_std', 0))
                    acoustic_by_emotion[true_emotion]['zcr'].append(features.get('zcr', 0))
                    acoustic_by_emotion[true_emotion]['spectral_centroid'].append(features.get('spectral_centroid', 0))
                
                # Update accuracy
                if predicted_emotion == true_emotion:
                    correct += 1
                total += 1
        
        except Exception as e:
            print(f"\n❌ Error processing {audio_file.name}: {e}")
            continue
    
    elapsed_time = time.time() - start_time
    
    # Calculate metrics
    print("\n\n" + "="*70)
    print("📊 BENCHMARK RESULTS")
    print("="*70)
    
    if total > 0:
        overall_accuracy = (correct / total) * 100
        avg_latency = elapsed_time / total
        
        print(f"\n✅ Overall Accuracy: {overall_accuracy:.1f}% ({correct}/{total})")
        print(f"⚡ Average Latency: {avg_latency:.3f}s per file")
        print(f"⏱️  Total Time: {elapsed_time/60:.1f} minutes")
        
        # Per-emotion accuracy
        print("\n📈 Per-Emotion Accuracy:")
        print("-" * 70)
        
        emotion_stats = {}
        for emotion in sorted(CREMAD_EMOTIONS.values()):
            if emotion in confusion_matrix:
                total_emotion = sum(confusion_matrix[emotion].values())
                correct_emotion = confusion_matrix[emotion][emotion]
                accuracy = (correct_emotion / total_emotion * 100) if total_emotion > 0 else 0
                emotion_stats[emotion] = {
                    'accuracy': accuracy,
                    'total': total_emotion,
                    'correct': correct_emotion
                }
                print(f"  {emotion:12s}: {accuracy:5.1f}% ({correct_emotion}/{total_emotion})")
        
        # Confusion matrix
        print("\n🔀 Confusion Matrix:")
        print("-" * 70)
        emotions_list = sorted(CREMAD_EMOTIONS.values())
        
        # Header
        print(f"{'True \\ Pred':<12s}", end='')
        for e in emotions_list:
            print(f"{e[:8]:>10s}", end='')
        print()
        print("-" * 70)
        
        # Rows
        for true_e in emotions_list:
            print(f"{true_e:<12s}", end='')
            for pred_e in emotions_list:
                count = confusion_matrix[true_e][pred_e]
                print(f"{count:>10d}", end='')
            print()
        
        # Acoustic feature analysis
        print("\n\n" + "="*70)
        print("🎵 ACOUSTIC FEATURE ANALYSIS")
        print("="*70)
        print("\nMean values by emotion (for calibration):\n")
        
        feature_ranges = {}
        for emotion in sorted(acoustic_by_emotion.keys()):
            data = acoustic_by_emotion[emotion]
            if len(data['pitch']) > 0:
                print(f"📊 {emotion.upper()}:")
                
                pitch_mean = np.mean(data['pitch'])
                energy_mean = np.mean(data['energy'])
                rate_mean = np.mean(data['rate'])
                
                feature_ranges[emotion] = {
                    'pitch_mean': pitch_mean,
                    'pitch_std': np.std(data['pitch']),
                    'energy_mean': energy_mean,
                    'energy_std': np.std(data['energy']),
                    'rate_mean': rate_mean,
                    'rate_std': np.std(data['rate'])
                }
                
                print(f"  Pitch:  {pitch_mean:7.1f} Hz (±{np.std(data['pitch']):6.1f})")
                print(f"  Energy: {energy_mean:7.4f}   (±{np.std(data['energy']):6.4f})")
                print(f"  Rate:   {rate_mean:7.2f} syl/s (±{np.std(data['rate']):6.2f})")
                print()
        
        # Recommendations
        print("\n" + "="*70)
        print("💡 CALIBRATION RECOMMENDATIONS")
        print("="*70)
        
        print("\n📝 Based on CREMA-D analysis, consider updating config.yaml:\n")
        
        # Find distinguishing features
        if 'anger' in feature_ranges and 'sadness' in feature_ranges:
            anger_energy = feature_ranges['anger']['energy_mean']
            sadness_energy = feature_ranges['sadness']['energy_mean']
            anger_rate = feature_ranges['anger']['rate_mean']
            sadness_rate = feature_ranges['sadness']['rate_mean']
            
            print(f"acoustic_features:")
            print(f"  energy:")
            print(f"    high: {anger_energy * 0.8:.4f}  # Threshold for high energy (anger/joy)")
            print(f"    low: {sadness_energy * 1.2:.4f}  # Threshold for low energy (sadness)")
            print(f"  speech_rate:")
            print(f"    fast: {anger_rate * 0.9:.2f}  # Threshold for fast speech (anger)")
            print(f"    slow: {sadness_rate * 1.1:.2f}  # Threshold for slow speech (sadness)")
        
        # Save results
        if save_results:
            output_file = f"cremad_results_{int(time.time())}.json"
            with open(output_file, 'w') as f:
                json.dump({
                    'overall_accuracy': overall_accuracy,
                    'total_samples': total,
                    'correct_predictions': correct,
                    'avg_latency': avg_latency,
                    'emotion_stats': emotion_stats,
                    'feature_ranges': feature_ranges,
                    'detailed_results': results[:100]  # Save first 100 for inspection
                }, f, indent=2)
            print(f"\n💾 Detailed results saved to: {output_file}")
    
    else:
        print("\n❌ No valid results to report")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark emotion detection on CREMA-D")
    parser.add_argument('--dir', type=str, default='Data/CREMA-D',
                        help='Path to CREMA-D directory')
    parser.add_argument('--sample', type=int, default=None,
                        help='Number of files to test (default: all)')
    parser.add_argument('--no-save', action='store_true',
                        help='Do not save results to file')
    
    args = parser.parse_args()
    
    run_benchmark(
        cremad_dir=args.dir,
        sample_size=args.sample,
        save_results=not args.no_save
    )

