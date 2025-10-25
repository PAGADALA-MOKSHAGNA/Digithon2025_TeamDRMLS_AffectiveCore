"""
Main Emotion Detection Pipeline
Orchestrates multimodal emotion analysis from speech audio.
"""

import logging
import time
import numpy as np
from typing import Dict, Optional, Callable, List
import yaml
from pathlib import Path

# Import custom modules
from speech_to_text import SpeechToText
from text_emotion import TextEmotionAnalyzer
from voice_tone import VoiceToneAnalyzer
from fusion import EmotionFusion, compress_json_output
from utils import AudioProcessor, AudioValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmotionDetectionPipeline:
    """
    End-to-end pipeline for multimodal speech emotion detection.
    
    Features:
    - Offline-first ASR (Whisper/Vosk)
    - Text emotion analysis (DistilRoBERTa)
    - Acoustic emotion analysis (librosa)
    - Decision-level fusion with dynamic weighting
    - Temporal smoothing
    - Real-time callback support
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the emotion detection pipeline.
        
        Args:
            config_path: Path to configuration YAML file
        """
        logger.info("Initializing Emotion Detection Pipeline")
        
        # Load configuration
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        # Initialize components
        self.audio_processor = AudioProcessor(self.config)
        self.speech_to_text = SpeechToText(self.config)
        self.text_emotion = TextEmotionAnalyzer(self.config)
        self.voice_tone = VoiceToneAnalyzer(self.config)
        self.fusion = EmotionFusion(self.config)
        
        # Performance tracking
        self.latency_history = []
        self.max_latency = self.config['performance']['max_latency']
        
        # Callback for real-time results
        self.result_callback: Optional[Callable] = None
        
        logger.info("Pipeline initialized successfully")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise
    
    def _setup_logging(self):
        """Setup logging based on configuration."""
        log_level = self.config['logging']['level']
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        # File logging
        log_file = self.config['logging'].get('file')
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter(self.config['logging']['format'])
            )
            logging.getLogger().addHandler(file_handler)
    
    def analyze_audio_file(
        self,
        audio_path: str,
        enable_smoothing: bool = False
    ) -> Dict[str, any]:
        """
        Analyze emotion from an audio file.
        
        Args:
            audio_path: Path to audio file
            enable_smoothing: Whether to apply temporal smoothing
            
        Returns:
            Emotion analysis result dictionary
        """
        logger.info(f"Analyzing audio file: {audio_path}")
        start_time = time.time()
        
        try:
            # 1. Load and preprocess audio
            audio, sr = self.audio_processor.load_audio(audio_path)
            
            # Validate audio
            is_valid, reason = AudioValidator.is_valid_audio(audio)
            if not is_valid:
                logger.warning(f"Invalid audio: {reason}")
                return self._error_result(f"Invalid audio: {reason}")
            
            # Detect non-speech (disabled for RAVDESS/dataset testing)
            # is_non_speech, signal_type = AudioValidator.detect_non_speech(audio, sr)
            # if is_non_speech:
            #     logger.warning(f"Non-speech audio detected: {signal_type}")
            #     return self._error_result(f"Non-speech audio: {signal_type}")
            
            # Preprocess
            audio = self.audio_processor.preprocess_audio(audio)
            
            # Apply VAD
            audio, speech_ratio = self.audio_processor.apply_vad(audio)
            if speech_ratio < 0.1:
                logger.warning("Insufficient speech detected")
                return self._error_result("Insufficient speech content")
            
            # 2. Process through pipeline
            result = self._process_audio_chunk(audio, enable_smoothing)
            
            # 3. Track latency
            latency = time.time() - start_time
            result['latency'] = round(latency, 3)
            self.latency_history.append(latency)
            
            if latency > self.max_latency:
                logger.warning(f"Latency {latency:.2f}s exceeds target {self.max_latency}s")
            else:
                logger.info(f"Analysis completed in {latency:.2f}s")
            
            # 4. Call callback if registered
            if self.result_callback:
                self.result_callback(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            return self._error_result(str(e))
    
    def _process_audio_chunk(
        self,
        audio: np.ndarray,
        enable_smoothing: bool = True
    ) -> Dict[str, any]:
        """
        Process a single audio chunk through the full pipeline.
        
        Args:
            audio: Preprocessed audio array
            enable_smoothing: Whether to apply temporal smoothing
            
        Returns:
            Emotion analysis result
        """
        try:
            # Step 1: Speech-to-Text
            logger.debug("Running ASR...")
            asr_result = self.speech_to_text.transcribe(audio)
            
            transcription = asr_result['text']
            asr_confidence = asr_result['confidence']
            
            # Check if transcription is empty (non-speech audio like laughs, cries)
            use_tone_only = False
            if self.speech_to_text.is_empty_transcription(transcription):
                logger.warning("Empty transcription - falling back to tone-only analysis (non-speech audio)")
                use_tone_only = True
                # Set neutral text emotions for non-speech audio
                text_emotions = {emotion: 0.142857 for emotion in self.emotion_labels}  # Equal distribution
                text_emotions['neutral'] = 0.7  # Bias towards neutral for non-speech
                text_confidence = 0.1  # Low confidence
                text_emotion = 'neutral'
                transcription = "[Non-speech audio detected]"
                logger.info("Using tone-only mode for non-speech audio (vocal burst/music/noise)")
            else:
                logger.info(f"Transcription: '{transcription}' (conf: {asr_confidence:.2f})")
                
                # Step 2: Text Emotion Analysis
                logger.debug("Analyzing text emotion...")
                text_result = self.text_emotion.analyze(transcription)
                
                text_emotions = text_result['emotions']
                text_confidence = text_result['confidence']
                text_emotion = text_result['top_emotion']
                
                logger.info(
                    f"Text emotion: {text_emotion} "
                    f"(conf: {text_confidence:.2f})"
                )
            
            # Step 3: Voice Tone Analysis
            logger.debug("Analyzing voice tone...")
            tone_result = self.voice_tone.analyze(audio)
            
            tone_emotions = tone_result['emotions']
            tone_confidence = tone_result['confidence']
            tone_emotion = tone_result['top_emotion']
            acoustic_features = tone_result['features']
            
            # Check if tone analysis failed
            fallback_mode = 'error' in tone_result
            
            if fallback_mode:
                logger.warning("Tone analysis failed, using text-only mode")
                # Use text-only
                return self._text_only_result(
                    transcription,
                    text_emotions,
                    text_confidence,
                    acoustic_features
                )
            
            logger.info(
                f"Tone emotion: {tone_emotion} "
                f"(conf: {tone_confidence:.2f})"
            )
            
            # If using tone-only mode (non-speech audio), prioritize tone
            if use_tone_only:
                logger.info("Processing non-speech audio with tone-only mode")
                return self._tone_only_result(
                    transcription,
                    tone_emotions,
                    tone_confidence,
                    acoustic_features
                )
            
            # Step 4: Fusion
            logger.debug("Fusing text and tone emotions...")
            fused_result = self.fusion.process(
                text_emotions=text_emotions,
                tone_emotions=tone_emotions,
                text_confidence=text_confidence,
                tone_confidence=tone_confidence,
                transcription=transcription,
                apply_smoothing=enable_smoothing
            )
            
            # Add acoustic features to breakdown
            fused_result['breakdown']['acoustic_features'] = acoustic_features
            
            return fused_result
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}", exc_info=True)
            return self._error_result(str(e))
    
    def _text_only_result(
        self,
        transcription: str,
        text_emotions: Dict[str, float],
        text_confidence: float,
        acoustic_features: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Generate result using text-only (graceful degradation).
        
        Args:
            transcription: Transcribed text
            text_emotions: Text emotion scores
            text_confidence: Text confidence
            acoustic_features: Acoustic features (may be empty)
            
        Returns:
            Text-only emotion result
        """
        from datetime import datetime
        import pytz
        
        top_emotion = max(text_emotions, key=text_emotions.get)
        confidence = text_emotions[top_emotion]
        
        # Map intensity
        intensity = self.fusion.map_intensity(confidence)
        
        # Get action trigger
        action_trigger = self.fusion.get_action_trigger(top_emotion, intensity)
        
        result = {
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'transcription': transcription,
            'emotion': top_emotion,
            'intensity': intensity,
            'confidence': round(confidence, 3),
            'breakdown': {
                'text_emotion': {
                    k: round(v, 3) for k, v in text_emotions.items() if v > 0.01
                },
                'acoustic_features': acoustic_features
            },
            'action_trigger': action_trigger,
            'notes': {
                'fallback_mode': True,
                'mode': 'text_only',
                'reason': 'Acoustic analysis unavailable'
            }
        }
        
        logger.warning("Using text-only mode (fallback)")
        return result
    
    def _tone_only_result(
        self,
        transcription: str,
        tone_emotions: Dict[str, float],
        tone_confidence: float,
        acoustic_features: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Generate result using tone-only (for non-speech audio).
        
        Args:
            transcription: Placeholder text (e.g., "[Non-speech audio detected]")
            tone_emotions: Tone emotion scores
            tone_confidence: Tone confidence
            acoustic_features: Acoustic features
            
        Returns:
            Tone-only emotion result
        """
        from datetime import datetime
        import pytz
        
        top_emotion = max(tone_emotions, key=tone_emotions.get)
        confidence = tone_emotions[top_emotion]
        
        # Map intensity
        intensity = self.fusion.map_intensity(confidence)
        
        # Get action trigger
        action_trigger = self.fusion.get_action_trigger(top_emotion, intensity)
        
        result = {
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'transcription': transcription,
            'emotion': top_emotion,
            'intensity': intensity,
            'confidence': round(confidence, 3),
            'breakdown': {
                'tone_emotion': {
                    k: round(v, 3) for k, v in tone_emotions.items() if v > 0.01
                },
                'acoustic_features': acoustic_features
            },
            'action_trigger': action_trigger,
            'notes': {
                'fallback_mode': True,
                'mode': 'tone_only',
                'reason': 'Non-speech audio (vocal burst/laugh/cry/music)'
            }
        }
        
        logger.info(f"Using tone-only mode for non-speech audio: {top_emotion} (conf: {confidence:.3f})")
        return result
    
    def _error_result(self, error_message: str) -> Dict[str, any]:
        """
        Generate error result.
        
        Args:
            error_message: Error description
            
        Returns:
            Error result dictionary
        """
        from datetime import datetime
        import pytz
        
        return {
            'timestamp': datetime.now(pytz.UTC).isoformat(),
            'transcription': "",
            'emotion': 'neutral',
            'intensity': 'Low',
            'confidence': 0.0,
            'breakdown': {},
            'action_trigger': {
                'led_color': 'white',
                'quote_category': 'neutral',
                'servo_gesture': 'idle'
            },
            'notes': {
                'error': error_message,
                'fallback_mode': True
            }
        }
    
    def analyze_stream(
        self,
        audio_generator,
        chunk_duration: Optional[float] = None,
        overlap: Optional[float] = None
    ):
        """
        Analyze emotion from streaming audio.
        
        Args:
            audio_generator: Generator yielding audio chunks
            chunk_duration: Duration of each chunk (default from config)
            overlap: Overlap between chunks (default from config)
            
        Yields:
            Emotion analysis results
        """
        chunk_duration = chunk_duration or self.config['asr']['chunk_duration']
        overlap = overlap or self.config['asr']['overlap']
        
        logger.info("Starting streaming analysis")
        
        buffer = np.array([], dtype=np.float32)
        chunk_samples = int(chunk_duration * self.audio_processor.sample_rate)
        overlap_samples = int(overlap * self.audio_processor.sample_rate)
        step = chunk_samples - overlap_samples
        
        for audio_chunk in audio_generator:
            # Add to buffer
            buffer = np.concatenate([buffer, audio_chunk])
            
            # Process when buffer is full
            while len(buffer) >= chunk_samples:
                # Extract chunk
                chunk = buffer[:chunk_samples]
                
                # Keep overlap
                buffer = buffer[step:]
                
                # Preprocess
                chunk = self.audio_processor.preprocess_audio(chunk)
                
                # Apply VAD
                chunk, speech_ratio = self.audio_processor.apply_vad(chunk)
                
                # Skip if insufficient speech
                if speech_ratio < 0.1:
                    logger.debug("Skipping chunk with insufficient speech")
                    continue
                
                # Process chunk
                start_time = time.time()
                result = self._process_audio_chunk(chunk, enable_smoothing=True)
                latency = time.time() - start_time
                result['latency'] = round(latency, 3)
                
                # Callback
                if self.result_callback:
                    self.result_callback(result)
                
                yield result
    
    def register_callback(self, callback: Callable[[Dict], None]):
        """
        Register callback function for real-time results.
        
        Args:
            callback: Function to call with each result
        """
        self.result_callback = callback
        logger.info("Result callback registered")
    
    def get_compressed_output(self, result: Dict[str, any]) -> Dict[str, any]:
        """
        Get compressed JSON output for ESP32.
        
        Args:
            result: Full analysis result
            
        Returns:
            Compressed result (<1KB)
        """
        max_size = self.config['output']['max_json_size']
        return compress_json_output(result, max_size)
    
    def reset(self):
        """Reset pipeline state (clear temporal history)."""
        self.fusion.reset_history()
        self.latency_history.clear()
        logger.info("Pipeline reset")
    
    def get_performance_stats(self) -> Dict[str, any]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.latency_history:
            return {
                'samples': 0,
                'avg_latency': 0.0,
                'max_latency': 0.0,
                'min_latency': 0.0
            }
        
        return {
            'samples': len(self.latency_history),
            'avg_latency': round(np.mean(self.latency_history), 3),
            'max_latency': round(np.max(self.latency_history), 3),
            'min_latency': round(np.min(self.latency_history), 3),
            'target_latency': self.max_latency,
            'within_target': sum(
                1 for l in self.latency_history if l <= self.max_latency
            ) / len(self.latency_history)
        }
    
    def batch_analyze(
        self,
        audio_paths: List[str],
        enable_smoothing: bool = False
    ) -> List[Dict[str, any]]:
        """
        Analyze multiple audio files in batch.
        
        Args:
            audio_paths: List of audio file paths
            enable_smoothing: Whether to apply temporal smoothing
            
        Returns:
            List of emotion analysis results
        """
        logger.info(f"Batch analyzing {len(audio_paths)} files")
        
        results = []
        for path in audio_paths:
            result = self.analyze_audio_file(path, enable_smoothing)
            results.append(result)
        
        logger.info(f"Batch analysis complete: {len(results)} results")
        return results


# Convenience function for quick single-file analysis
def analyze_file(audio_path: str, config_path: str = "config.yaml") -> Dict[str, any]:
    """
    Quick function to analyze a single audio file.
    
    Args:
        audio_path: Path to audio file
        config_path: Path to config file
        
    Returns:
        Emotion analysis result
    """
    pipeline = EmotionDetectionPipeline(config_path)
    return pipeline.analyze_audio_file(audio_path)

