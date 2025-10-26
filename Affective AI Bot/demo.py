#!/usr/bin/env python3
"""
Demo script for Speech Emotion Detection System.
Supports both single file analysis and real-time streaming mode.
"""

import argparse
import json
import sys
from pathlib import Path
import logging

try:
    import sounddevice as sd
    import numpy as np
    AUDIO_INPUT_AVAILABLE = True
except ImportError:
    AUDIO_INPUT_AVAILABLE = False
    print("Warning: sounddevice not installed. Streaming mode unavailable.")
    print("Install with: pip install sounddevice")

from emotion_detection import EmotionDetectionPipeline
from utils import AudioProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║       🎭 AffectiveCore: Speech Emotion Detection 🎭      ║
    ║                                                           ║
    ║     Multimodal Emotion Analysis from Speech Audio        ║
    ║        Text (Linguistic) + Tone (Paralinguistic)         ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_result(result: dict, verbose: bool = False):
    """
    Pretty print emotion detection result.
    
    Args:
        result: Emotion analysis result
        verbose: Whether to show detailed breakdown
    """
    print("\n" + "="*60)
    print("🎯 EMOTION DETECTION RESULT")
    print("="*60)
    
    # Check for errors
    if result['notes'].get('error'):
        print(f"❌ Error: {result['notes']['error']}")
        return
    
    # Main result
    print(f"\n📝 Transcription: \"{result['transcription']}\"")
    print(f"\n😊 Detected Emotion: {result['emotion'].upper()}")
    print(f"💪 Intensity: {result['intensity']}")
    print(f"🎯 Confidence: {result['confidence']:.1%}")
    
    if result.get('latency'):
        print(f"⏱️  Latency: {result['latency']:.3f}s")
    
    # Action triggers
    print(f"\n🎨 ESP32 Actions:")
    action = result['action_trigger']
    print(f"   • LED Color: {action['led_color']}")
    print(f"   • Quote Category: {action['quote_category']}")
    print(f"   • Servo Gesture: {action['servo_gesture']}")
    
    # Notes
    notes = result['notes']
    if notes.get('mixed_emotion'):
        print(f"\n⚠️  Mixed Emotion Detected!")
        if notes.get('mixed_emotion_details'):
            print(f"   {notes['mixed_emotion_details']}")
    
    if notes.get('fallback_mode'):
        print(f"\n⚠️  Fallback Mode: {notes.get('mode', 'unknown')}")
        print(f"   Reason: {notes.get('reason', 'unknown')}")
    
    # Verbose breakdown
    if verbose and 'breakdown' in result:
        print(f"\n📊 Detailed Breakdown:")
        
        breakdown = result['breakdown']
        
        # Text emotions
        if 'text_emotion' in breakdown:
            print(f"\n   Text Emotions:")
            for emotion, score in sorted(
                breakdown['text_emotion'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                bar = "█" * int(score * 20)
                print(f"      {emotion:10s}: {score:.3f} {bar}")
        
        # Tone emotions
        if 'tone_emotion' in breakdown:
            print(f"\n   Tone Emotions:")
            for emotion, score in sorted(
                breakdown['tone_emotion'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                bar = "█" * int(score * 20)
                print(f"      {emotion:10s}: {score:.3f} {bar}")
        
        # Acoustic features
        if 'acoustic_features' in breakdown:
            print(f"\n   Acoustic Features:")
            features = breakdown['acoustic_features']
            print(f"      Pitch (mean): {features.get('pitch_mean', 0):.1f} Hz")
            print(f"      Pitch (std):  {features.get('pitch_std', 0):.1f} Hz")
            print(f"      Energy:       {features.get('energy_mean', 0):.3f}")
            print(f"      Speech Rate:  {features.get('speech_rate', 0):.1f} syll/s")
            print(f"      ZCR:          {features.get('zcr_mean', 0):.3f}")
        
        # Fusion parameters
        if 'fusion_alpha' in notes:
            print(f"\n   Fusion Parameters:")
            print(f"      Alpha (text weight): {notes['fusion_alpha']:.3f}")
            print(f"      Beta (tone weight):  {1 - notes['fusion_alpha']:.3f}")
            if notes.get('smoothing_applied'):
                print(f"      Smoothing window:    {notes.get('smoothing_window', 0)}")
    
    print("\n" + "="*60 + "\n")


def analyze_single_file(args):
    """
    Analyze a single audio file.
    
    Args:
        args: Command-line arguments
    """
    print_banner()
    
    file_path = args.file
    if not Path(file_path).exists():
        print(f"❌ Error: File not found: {file_path}")
        sys.exit(1)
    
    print(f"📁 Loading file: {file_path}")
    print("🔄 Initializing pipeline...")
    
    # Initialize pipeline
    pipeline = EmotionDetectionPipeline(args.config)
    
    print("🎵 Analyzing audio...")
    
    # Analyze
    result = pipeline.analyze_audio_file(
        file_path,
        enable_smoothing=args.smooth
    )
    
    # Print result
    print_result(result, verbose=args.verbose)
    
    # Save to JSON if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Result saved to: {args.output}")
    
    # Print performance stats
    stats = pipeline.get_performance_stats()
    print(f"📈 Performance: {stats['avg_latency']:.3f}s average latency")


def stream_from_microphone(args):
    """
    Stream audio from microphone and analyze in real-time.
    
    Args:
        args: Command-line arguments
    """
    if not AUDIO_INPUT_AVAILABLE:
        print("❌ Error: sounddevice not installed. Cannot use streaming mode.")
        sys.exit(1)
    
    print_banner()
    print("🎤 Real-time Streaming Mode")
    print("="*60)
    
    # Initialize pipeline
    print("🔄 Initializing pipeline...")
    pipeline = EmotionDetectionPipeline(args.config)
    
    sample_rate = pipeline.config['asr']['sample_rate']
    chunk_duration = args.chunk
    
    print(f"\n✅ Pipeline ready!")
    print(f"   Sample rate: {sample_rate} Hz")
    print(f"   Chunk duration: {chunk_duration}s")
    print(f"   Device: {args.device}")
    print("\n🎙️  Listening... (Press Ctrl+C to stop)\n")
    
    # Audio buffer
    buffer = []
    chunk_samples = int(chunk_duration * sample_rate)
    
    def audio_callback(indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            print(f"⚠️  Audio status: {status}")
        
        # Add to buffer
        audio_data = indata[:, 0].copy()  # Take first channel
        buffer.extend(audio_data)
        
        # Process when buffer is full
        if len(buffer) >= chunk_samples:
            # Extract chunk
            chunk = np.array(buffer[:chunk_samples], dtype=np.float32)
            buffer.clear()
            
            # Process
            try:
                result = pipeline.analyze_audio_file(
                    chunk,  # Pass array directly (will need small modification)
                    enable_smoothing=True
                )
                
                # Print result
                print_result(result, verbose=args.verbose)
                
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    # Alternative: Manual streaming
    try:
        frame_size = int(0.1 * sample_rate)  # 100ms frames
        
        with sd.InputStream(
            device=args.device,
            channels=1,
            samplerate=sample_rate,
            blocksize=frame_size
        ) as stream:
            print("🎙️  Recording...")
            
            while True:
                # Read audio
                audio_chunk, overflowed = stream.read(frame_size)
                
                if overflowed:
                    print("⚠️  Audio buffer overflow")
                
                # Add to buffer
                buffer.extend(audio_chunk[:, 0])
                
                # Process when buffer is full
                if len(buffer) >= chunk_samples:
                    chunk = np.array(buffer[:chunk_samples], dtype=np.float32)
                    
                    # Keep overlap
                    overlap_samples = int(args.overlap * sample_rate)
                    buffer = buffer[chunk_samples - overlap_samples:]
                    
                    # Preprocess
                    chunk = pipeline.audio_processor.preprocess_audio(chunk)
                    
                    # Apply VAD
                    chunk, speech_ratio = pipeline.audio_processor.apply_vad(chunk)
                    
                    # Skip if insufficient speech
                    if speech_ratio < 0.1:
                        logger.debug("Skipping chunk with insufficient speech")
                        continue
                    
                    # Process
                    try:
                        import tempfile
                        import soundfile as sf
                        
                        # Save to temp file (workaround for file-based API)
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                            sf.write(tmp.name, chunk, sample_rate)
                            result = pipeline.analyze_audio_file(
                                tmp.name,
                                enable_smoothing=True
                            )
                            Path(tmp.name).unlink()  # Clean up
                        
                        # Print result
                        if args.verbose or result['confidence'] > 0.5:
                            print_result(result, verbose=args.verbose)
                        
                    except Exception as e:
                        logger.error(f"Processing error: {e}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Stopping...")
        
        # Print final stats
        stats = pipeline.get_performance_stats()
        print(f"\n📈 Session Statistics:")
        print(f"   Total samples: {stats['samples']}")
        print(f"   Average latency: {stats['avg_latency']:.3f}s")
        print(f"   Max latency: {stats['max_latency']:.3f}s")
        print(f"   Within target: {stats['within_target']:.1%}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Streaming error: {e}", exc_info=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AffectiveCore: Multimodal Speech Emotion Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single file
  python demo.py --file sample.wav --mode single
  
  # Analyze with verbose output
  python demo.py --file sample.wav --mode single --verbose
  
  # Save output to JSON
  python demo.py --file sample.wav --output result.json
  
  # Real-time streaming from microphone
  python demo.py --device 0 --mode stream --chunk 4
  
  # Streaming with 1s overlap
  python demo.py --device 0 --mode stream --chunk 3 --overlap 1
        """
    )
    
    # Mode
    parser.add_argument(
        '--mode',
        type=str,
        choices=['single', 'stream'],
        default='single',
        help='Operation mode: single file or streaming'
    )
    
    # File input (for single mode)
    parser.add_argument(
        '--file',
        type=str,
        help='Audio file path (for single mode)'
    )
    
    # Microphone input (for stream mode)
    parser.add_argument(
        '--device',
        type=int,
        default=None,
        help='Audio input device ID (for stream mode)'
    )
    
    # Processing options
    parser.add_argument(
        '--chunk',
        type=float,
        default=4.0,
        help='Audio chunk duration in seconds (default: 4.0)'
    )
    
    parser.add_argument(
        '--overlap',
        type=float,
        default=1.0,
        help='Overlap between chunks in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--smooth',
        action='store_true',
        help='Enable temporal smoothing'
    )
    
    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Save result to JSON file'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show detailed breakdown'
    )
    
    # Configuration
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode == 'single':
        if not args.file:
            parser.error("--file is required for single mode")
        analyze_single_file(args)
    
    elif args.mode == 'stream':
        stream_from_microphone(args)


if __name__ == '__main__':
    main()

