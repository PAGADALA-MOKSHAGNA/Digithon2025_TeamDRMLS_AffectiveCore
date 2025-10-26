#!/usr/bin/env python3
"""
Easy script to test your custom voice dataset.
Supports directory structure or CSV metadata.
"""

import argparse
import json
import sys
from pathlib import Path
import pandas as pd
from emotion_detection import EmotionDetectionPipeline
from test_samples import EmotionBenchmark
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_directory_structure(directory: str, output_file: str = None):
    """
    Test dataset organized by emotion folders.
    
    Structure:
        dataset/
        ├── joy/
        │   ├── file1.wav
        │   └── file2.wav
        ├── sadness/
        └── ...
    """
    print("📁 Testing directory-structured dataset...")
    print(f"   Directory: {directory}\n")
    
    # Initialize pipeline and benchmark
    pipeline = EmotionDetectionPipeline('config.yaml')
    benchmark = EmotionBenchmark(pipeline)
    
    # Find audio files organized by emotion
    base_path = Path(directory)
    emotions = ['joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise', 'neutral']
    
    found_files = 0
    for emotion in emotions:
        emotion_dir = base_path / emotion
        if emotion_dir.exists():
            audio_files = list(emotion_dir.glob('*.wav')) + \
                         list(emotion_dir.glob('*.mp3')) + \
                         list(emotion_dir.glob('*.flac'))
            
            if audio_files:
                logger.info(f"Found {len(audio_files)} files for {emotion}")
                found_files += len(audio_files)
                
                for audio_file in audio_files:
                    benchmark.test_file(str(audio_file), ground_truth=emotion)
    
    if found_files == 0:
        print(f"\n❌ No audio files found in emotion subdirectories!")
        print(f"\n💡 Expected structure:")
        print(f"   {directory}/")
        print(f"   ├── joy/")
        print(f"   │   └── audio1.wav")
        print(f"   ├── sadness/")
        print(f"   │   └── audio2.wav")
        print(f"   └── ...")
        sys.exit(1)
    
    # Print report
    print(f"\n✅ Tested {found_files} audio files")
    benchmark.print_report()
    
    # Save results
    if output_file:
        benchmark.save_results(output_file)
        print(f"💾 Detailed results saved to: {output_file}")


def test_csv_metadata(csv_file: str, audio_dir: str, output_file: str = None):
    """
    Test dataset with CSV metadata.
    
    CSV format:
        filename,emotion,intensity,speaker,notes
        audio1.wav,joy,high,speaker1,Happy birthday
        audio2.wav,sadness,medium,speaker2,Bad news
    """
    print("📋 Testing CSV-based dataset...")
    print(f"   CSV: {csv_file}")
    print(f"   Audio directory: {audio_dir}\n")
    
    # Load CSV
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        sys.exit(1)
    
    # Validate columns
    if 'filename' not in df.columns or 'emotion' not in df.columns:
        print("❌ CSV must have 'filename' and 'emotion' columns")
        sys.exit(1)
    
    # Initialize pipeline and benchmark
    pipeline = EmotionDetectionPipeline('config.yaml')
    benchmark = EmotionBenchmark(pipeline)
    
    audio_base = Path(audio_dir)
    tested = 0
    
    # Test each file
    for idx, row in df.iterrows():
        filename = row['filename']
        emotion = row['emotion'].lower()
        
        audio_path = audio_base / filename
        
        if not audio_path.exists():
            logger.warning(f"⚠️  File not found: {audio_path}")
            continue
        
        benchmark.test_file(str(audio_path), ground_truth=emotion)
        tested += 1
    
    if tested == 0:
        print("❌ No valid audio files found!")
        sys.exit(1)
    
    # Print report
    print(f"\n✅ Tested {tested} audio files")
    benchmark.print_report()
    
    # Save results
    if output_file:
        benchmark.save_results(output_file)
        print(f"💾 Detailed results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Test your custom voice dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Test directory-structured dataset
  python test_your_dataset.py --dir test_samples/my_emotions/

  # Test with CSV metadata
  python test_your_dataset.py --csv metadata.csv --audio-dir audio_files/

  # Save results to file
  python test_your_dataset.py --dir test_samples/my_emotions/ --output results.json

Directory Structure:
  test_samples/my_emotions/
  ├── joy/
  │   ├── sample1.wav
  │   └── sample2.wav
  ├── sadness/
  ├── anger/
  └── ...

CSV Format:
  filename,emotion,intensity,speaker
  audio1.wav,joy,high,speaker1
  audio2.wav,sadness,medium,speaker2
        """
    )
    
    parser.add_argument('--dir', type=str, help='Directory with emotion subfolders')
    parser.add_argument('--csv', type=str, help='CSV file with metadata')
    parser.add_argument('--audio-dir', type=str, help='Audio directory (for CSV mode)')
    parser.add_argument('--output', type=str, help='Output JSON file for results')
    parser.add_argument('--config', type=str, default='config.yaml', help='Config file')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.dir and not args.csv:
        parser.error("Must specify either --dir or --csv")
    
    if args.csv and not args.audio_dir:
        parser.error("--csv requires --audio-dir")
    
    if args.dir and args.csv:
        parser.error("Cannot use both --dir and --csv")
    
    # Print header
    print("\n" + "="*70)
    print("🎤 CUSTOM DATASET TESTING")
    print("="*70 + "\n")
    
    # Run appropriate test
    if args.dir:
        test_directory_structure(args.dir, args.output)
    elif args.csv:
        test_csv_metadata(args.csv, args.audio_dir, args.output)
    
    print("\n" + "="*70)
    print("📊 Testing Complete!")
    print("="*70)
    
    if args.output:
        print(f"\n💡 View detailed results: cat {args.output} | python -m json.tool")
    
    print("\n💡 Next steps:")
    print("   • Adjust config.yaml based on results")
    print("   • Run analyze_acoustic_ranges.py for calibration")
    print("   • Re-test to see improvements")
    print("   • Use compare_results.py to track progress\n")


if __name__ == '__main__':
    main()

