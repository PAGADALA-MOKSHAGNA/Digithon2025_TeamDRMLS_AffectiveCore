"""
Test script for validating the emotion detection system on sample audio files.
Includes benchmarking support for RAVDESS dataset.
"""

import sys
import os
from pathlib import Path
import json
import argparse
import pandas as pd
import numpy as np
from typing import List, Dict
import logging

from emotion_detection import EmotionDetectionPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmotionBenchmark:
    """Benchmarking system for emotion detection."""
    
    def __init__(self, pipeline: EmotionDetectionPipeline):
        """
        Initialize benchmark.
        
        Args:
            pipeline: Emotion detection pipeline
        """
        self.pipeline = pipeline
        self.results = []
        
        # Emotion label mapping for RAVDESS
        # RAVDESS format: 03-01-XX-01-01-01-01.wav
        # Where XX is emotion: 01=neutral, 02=calm, 03=happy, 04=sad, 05=angry, 06=fearful, 07=disgust, 08=surprised
        self.ravdess_mapping = {
            '01': 'neutral',
            '02': 'neutral',  # calm -> neutral
            '03': 'joy',       # happy -> joy
            '04': 'sadness',
            '05': 'anger',
            '06': 'fear',
            '07': 'disgust',
            '08': 'surprise'
        }
    
    def extract_ravdess_label(self, filename: str) -> str:
        """
        Extract ground truth emotion from RAVDESS filename.
        
        Args:
            filename: RAVDESS filename
            
        Returns:
            Emotion label
        """
        try:
            # Format: XX-XX-EM-XX-XX-XX-XX.wav
            parts = Path(filename).stem.split('-')
            emotion_code = parts[2]
            return self.ravdess_mapping.get(emotion_code, 'unknown')
        except Exception as e:
            logger.warning(f"Could not parse RAVDESS filename: {filename}")
            return 'unknown'
    
    def test_file(
        self,
        audio_path: str,
        ground_truth: str = None
    ) -> Dict[str, any]:
        """
        Test a single audio file.
        
        Args:
            audio_path: Path to audio file
            ground_truth: Expected emotion (optional)
            
        Returns:
            Test result dictionary
        """
        logger.info(f"Testing: {audio_path}")
        
        try:
            # Analyze
            result = self.pipeline.analyze_audio_file(audio_path)
            
            # Extract key info
            test_result = {
                'file': Path(audio_path).name,
                'ground_truth': ground_truth,
                'predicted': result['emotion'],
                'confidence': result['confidence'],
                'intensity': result['intensity'],
                'latency': result.get('latency', 0),
                'correct': ground_truth == result['emotion'] if ground_truth else None,
                'transcription': result['transcription'],
                'fallback': result['notes'].get('fallback_mode', False),
                'mixed': result['notes'].get('mixed_emotion', False),
                'full_result': result
            }
            
            self.results.append(test_result)
            
            return test_result
            
        except Exception as e:
            logger.error(f"Test failed for {audio_path}: {e}")
            return {
                'file': Path(audio_path).name,
                'ground_truth': ground_truth,
                'predicted': 'error',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def test_directory(
        self,
        directory: str,
        is_ravdess: bool = False,
        file_pattern: str = "*.wav"
    ) -> List[Dict]:
        """
        Test all audio files in a directory.
        
        Args:
            directory: Directory containing audio files
            is_ravdess: Whether files follow RAVDESS naming convention
            file_pattern: Glob pattern for audio files
            
        Returns:
            List of test results
        """
        audio_files = list(Path(directory).glob(file_pattern))
        
        if not audio_files:
            logger.warning(f"No audio files found in {directory}")
            return []
        
        logger.info(f"Found {len(audio_files)} audio files")
        
        for audio_file in audio_files:
            # Extract ground truth if RAVDESS
            ground_truth = None
            if is_ravdess:
                ground_truth = self.extract_ravdess_label(audio_file.name)
            
            self.test_file(str(audio_file), ground_truth)
        
        return self.results
    
    def calculate_metrics(self) -> Dict[str, any]:
        """
        Calculate performance metrics.
        
        Returns:
            Dictionary with accuracy, precision, recall, F1, etc.
        """
        if not self.results:
            return {}
        
        df = pd.DataFrame(self.results)
        
        # Filter out results without ground truth
        df_labeled = df[df['ground_truth'].notna() & (df['ground_truth'] != 'unknown')]
        
        if df_labeled.empty:
            return {
                'total_samples': len(df),
                'labeled_samples': 0,
                'avg_latency': df['latency'].mean(),
                'avg_confidence': df['confidence'].mean(),
                'fallback_rate': df['fallback'].mean() if 'fallback' in df else 0,
                'note': 'No labeled samples for accuracy calculation'
            }
        
        # Overall accuracy
        accuracy = df_labeled['correct'].mean()
        
        # Per-emotion metrics
        emotions = df_labeled['ground_truth'].unique()
        per_emotion_metrics = {}
        
        for emotion in emotions:
            emotion_samples = df_labeled[df_labeled['ground_truth'] == emotion]
            
            if len(emotion_samples) > 0:
                # True positives
                tp = len(emotion_samples[emotion_samples['predicted'] == emotion])
                
                # False positives (predicted this emotion but was something else)
                fp = len(df_labeled[
                    (df_labeled['predicted'] == emotion) &
                    (df_labeled['ground_truth'] != emotion)
                ])
                
                # False negatives (ground truth is this emotion but predicted something else)
                fn = len(emotion_samples) - tp
                
                # Precision and recall
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                
                per_emotion_metrics[emotion] = {
                    'samples': len(emotion_samples),
                    'correct': tp,
                    'precision': precision,
                    'recall': recall,
                    'f1': f1
                }
        
        # Confusion matrix
        confusion_matrix = {}
        for _, row in df_labeled.iterrows():
            gt = row['ground_truth']
            pred = row['predicted']
            
            if gt not in confusion_matrix:
                confusion_matrix[gt] = {}
            
            confusion_matrix[gt][pred] = confusion_matrix[gt].get(pred, 0) + 1
        
        # Aggregate metrics
        metrics = {
            'total_samples': len(df),
            'labeled_samples': len(df_labeled),
            'accuracy': accuracy,
            'avg_latency': df['latency'].mean(),
            'max_latency': df['latency'].max(),
            'avg_confidence': df['confidence'].mean(),
            'fallback_rate': df['fallback'].mean() if 'fallback' in df else 0,
            'mixed_emotion_rate': df['mixed'].mean() if 'mixed' in df else 0,
            'per_emotion': per_emotion_metrics,
            'confusion_matrix': confusion_matrix
        }
        
        return metrics
    
    def print_report(self):
        """Print benchmark report."""
        metrics = self.calculate_metrics()
        
        print("\n" + "="*70)
        print("📊 EMOTION DETECTION BENCHMARK REPORT")
        print("="*70)
        
        if not metrics:
            print("No results to report.")
            return
        
        # Overall stats
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Samples: {metrics['total_samples']}")
        print(f"   Labeled Samples: {metrics.get('labeled_samples', 0)}")
        
        if metrics.get('accuracy') is not None:
            print(f"   Accuracy: {metrics['accuracy']:.1%}")
        
        print(f"   Avg Confidence: {metrics['avg_confidence']:.1%}")
        print(f"   Avg Latency: {metrics['avg_latency']:.3f}s")
        print(f"   Max Latency: {metrics['max_latency']:.3f}s")
        print(f"   Fallback Rate: {metrics['fallback_rate']:.1%}")
        
        if metrics.get('mixed_emotion_rate'):
            print(f"   Mixed Emotion Rate: {metrics['mixed_emotion_rate']:.1%}")
        
        # Per-emotion metrics
        if 'per_emotion' in metrics and metrics['per_emotion']:
            print(f"\n📊 Per-Emotion Performance:")
            print(f"\n   {'Emotion':<12} {'Samples':>8} {'Precision':>10} {'Recall':>10} {'F1':>10}")
            print(f"   {'-'*12} {'-'*8} {'-'*10} {'-'*10} {'-'*10}")
            
            for emotion, em_metrics in sorted(metrics['per_emotion'].items()):
                print(
                    f"   {emotion:<12} "
                    f"{em_metrics['samples']:>8} "
                    f"{em_metrics['precision']:>9.1%} "
                    f"{em_metrics['recall']:>9.1%} "
                    f"{em_metrics['f1']:>9.1%}"
                )
        
        # Confusion matrix
        if 'confusion_matrix' in metrics and metrics['confusion_matrix']:
            print(f"\n🔀 Confusion Matrix:")
            
            all_emotions = sorted(set(
                list(metrics['confusion_matrix'].keys()) +
                [pred for gt_dict in metrics['confusion_matrix'].values() for pred in gt_dict.keys()]
            ))
            
            # Header
            print(f"\n   {'GT \\ Pred':<12}", end="")
            for emotion in all_emotions:
                print(f"{emotion[:8]:>10}", end="")
            print()
            
            print(f"   {'-'*12}", end="")
            for _ in all_emotions:
                print(f"{'-'*10}", end="")
            print()
            
            # Rows
            for gt in all_emotions:
                print(f"   {gt:<12}", end="")
                for pred in all_emotions:
                    count = metrics['confusion_matrix'].get(gt, {}).get(pred, 0)
                    print(f"{count:>10}", end="")
                print()
        
        print("\n" + "="*70 + "\n")
    
    def save_results(self, output_path: str):
        """
        Save detailed results to JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        output = {
            'results': self.results,
            'metrics': self.calculate_metrics()
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")


def create_sample_test_files():
    """Create sample test file structure."""
    test_dir = Path("test_samples")
    test_dir.mkdir(exist_ok=True)
    
    # Create README
    readme = test_dir / "README.md"
    readme.write_text("""# Test Samples

Place your test audio files here for benchmarking.

## Structure

### For general testing:
- Place any `.wav`, `.mp3`, or `.flac` files in this directory

### For RAVDESS benchmarking:
1. Download RAVDESS dataset from: https://zenodo.org/record/1188976
2. Place files in `test_samples/ravdess/` directory
3. Run: `python test_samples.py --ravdess test_samples/ravdess/`

## Sample Files for Demo

Create or record short audio samples for each emotion:
- `joy.wav` - "I got great news today!"
- `anger.wav` - "This project is driving me nuts!"
- `sadness.wav` - "I had a really tough day at work."
- `fear.wav` - "I'm really worried about this."
- `surprise.wav` - "Wow, I didn't expect that!"
- `disgust.wav` - "That's absolutely terrible."
- `neutral.wav` - "I'm finished now."
- `sarcasm.wav` - "Great, another meeting. Just what I needed."
""")
    
    logger.info(f"Created test samples directory: {test_dir}")
    return test_dir


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test and benchmark emotion detection system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test single file
  python test_samples.py --file sample.wav
  
  # Test all files in directory
  python test_samples.py --dir test_samples/
  
  # Benchmark on RAVDESS dataset
  python test_samples.py --ravdess test_samples/ravdess/ --output results.json
  
  # Create sample test structure
  python test_samples.py --setup
        """
    )
    
    parser.add_argument('--file', type=str, help='Test single audio file')
    parser.add_argument('--dir', type=str, help='Test all files in directory')
    parser.add_argument('--ravdess', type=str, help='Test RAVDESS dataset directory')
    parser.add_argument('--setup', action='store_true', help='Create test samples directory structure')
    parser.add_argument('--output', type=str, help='Save results to JSON file')
    parser.add_argument('--config', type=str, default='config.yaml', help='Config file path')
    parser.add_argument('--pattern', type=str, default='*.wav', help='File pattern for directory scan')
    
    args = parser.parse_args()
    
    # Setup mode
    if args.setup:
        create_sample_test_files()
        return
    
    # Initialize pipeline
    logger.info("Initializing pipeline...")
    pipeline = EmotionDetectionPipeline(args.config)
    
    # Initialize benchmark
    benchmark = EmotionBenchmark(pipeline)
    
    # Single file test
    if args.file:
        result = benchmark.test_file(args.file)
        print(json.dumps(result, indent=2))
    
    # Directory test
    elif args.dir:
        benchmark.test_directory(args.dir, is_ravdess=False, file_pattern=args.pattern)
        benchmark.print_report()
    
    # RAVDESS test
    elif args.ravdess:
        logger.info("Running RAVDESS benchmark...")
        benchmark.test_directory(args.ravdess, is_ravdess=True, file_pattern=args.pattern)
        benchmark.print_report()
    
    else:
        parser.print_help()
        return
    
    # Save results
    if args.output:
        benchmark.save_results(args.output)


if __name__ == '__main__':
    main()

