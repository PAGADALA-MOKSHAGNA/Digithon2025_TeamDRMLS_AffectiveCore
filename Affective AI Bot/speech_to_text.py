"""
Speech-to-Text module with support for Whisper and Vosk ASR engines.
Provides streaming capabilities and confidence scores.
"""

import logging
import numpy as np
from typing import Dict, Optional, Tuple
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)


class SpeechToText:
    """
    Unified interface for speech-to-text with multiple ASR backends.
    Supports both Whisper and Vosk with seamless switching.
    """
    
    def __init__(self, config: dict):
        """
        Initialize ASR engine based on configuration.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.engine_name = config['asr']['engine']
        self.sample_rate = config['asr']['sample_rate']
        self.model = None
        self.engine = None
        
        logger.info(f"Initializing ASR with engine: {self.engine_name}")
        
        if self.engine_name == "whisper":
            self._init_whisper()
        elif self.engine_name == "vosk":
            self._init_vosk()
        else:
            raise ValueError(f"Unsupported ASR engine: {self.engine_name}")
    
    def _init_whisper(self):
        """Initialize Whisper ASR model."""
        try:
            import whisper
            
            model_size = self.config['asr']['whisper']['model']
            device = self.config['asr']['whisper']['device']
            
            logger.info(f"Loading Whisper model: {model_size} on {device}")
            self.model = whisper.load_model(model_size, device=device)
            
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Whisper: {e}")
            raise
    
    def _init_vosk(self):
        """Initialize Vosk ASR model."""
        try:
            from vosk import Model, KaldiRecognizer
            import os
            
            model_path = self.config['asr']['vosk']['model_path']
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"Vosk model not found at {model_path}. "
                    "Please download from https://alphacephei.com/vosk/models"
                )
            
            logger.info(f"Loading Vosk model from: {model_path}")
            self.model = Model(model_path)
            
            logger.info("Vosk model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vosk: {e}")
            raise
    
    def transcribe(
        self, 
        audio: np.ndarray, 
        language: str = "en"
    ) -> Dict[str, any]:
        """
        Transcribe audio to text with confidence score.
        
        Args:
            audio: Audio array (float32, normalized to [-1, 1])
            language: Language code (default: "en")
            
        Returns:
            Dictionary containing:
                - text: Transcribed text
                - confidence: Confidence score (0-1)
                - segments: List of segments (if available)
        """
        if self.engine_name == "whisper":
            return self._transcribe_whisper(audio, language)
        elif self.engine_name == "vosk":
            return self._transcribe_vosk(audio)
        else:
            raise ValueError(f"Unknown engine: {self.engine_name}")
    
    def _transcribe_whisper(
        self, 
        audio: np.ndarray, 
        language: str
    ) -> Dict[str, any]:
        """
        Transcribe using Whisper model.
        
        Args:
            audio: Audio array
            language: Language code
            
        Returns:
            Transcription result dictionary
        """
        try:
            # Ensure audio is float32
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Whisper expects audio normalized to [-1, 1]
            if np.abs(audio).max() > 1.0:
                audio = audio / np.abs(audio).max()
            
            # Transcribe
            result = self.model.transcribe(
                audio,
                language=language,
                fp16=False,
                verbose=False
            )
            
            text = result['text'].strip()
            
            # Estimate confidence from log probability if available
            # Whisper doesn't provide direct confidence, so we estimate it
            confidence = self._estimate_whisper_confidence(result)
            
            logger.info(f"Whisper transcription: '{text}' (conf: {confidence:.2f})")
            
            return {
                'text': text,
                'confidence': confidence,
                'segments': result.get('segments', []),
                'language': result.get('language', language)
            }
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return {
                'text': "",
                'confidence': 0.0,
                'segments': [],
                'error': str(e)
            }
    
    def _estimate_whisper_confidence(self, result: dict) -> float:
        """
        Estimate confidence score from Whisper result.
        
        Whisper doesn't provide explicit confidence, so we use heuristics:
        - Average token probabilities from segments
        - Penalize very short transcriptions
        - Penalize "[BLANK_AUDIO]" or similar tokens
        
        Args:
            result: Whisper transcription result
            
        Returns:
            Estimated confidence (0-1)
        """
        text = result['text'].strip()
        
        # Empty or very short transcriptions get low confidence
        if len(text) == 0:
            return 0.0
        if len(text) < 5:
            return 0.3
        
        # Check for silence indicators
        silence_markers = ['[BLANK_AUDIO]', '[SILENCE]', '(silence)', '...']
        if any(marker in text.lower() for marker in silence_markers):
            return 0.1
        
        # Use segment probabilities if available
        segments = result.get('segments', [])
        if segments:
            # Average the no_speech_prob (inverted)
            confidences = []
            for seg in segments:
                # no_speech_prob is probability of silence
                # Higher no_speech_prob = lower confidence
                no_speech_prob = seg.get('no_speech_prob', 0.5)
                conf = 1.0 - no_speech_prob
                confidences.append(conf)
            
            if confidences:
                avg_confidence = np.mean(confidences)
                return float(np.clip(avg_confidence, 0.0, 1.0))
        
        # Default confidence based on text length
        # Longer texts generally mean more confident recognition
        if len(text) < 10:
            return 0.5
        elif len(text) < 30:
            return 0.7
        else:
            return 0.8
    
    def _transcribe_vosk(self, audio: np.ndarray) -> Dict[str, any]:
        """
        Transcribe using Vosk model.
        
        Args:
            audio: Audio array
            
        Returns:
            Transcription result dictionary
        """
        try:
            from vosk import KaldiRecognizer
            import json
            
            # Convert to int16 PCM
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Create recognizer
            recognizer = KaldiRecognizer(self.model, self.sample_rate)
            recognizer.SetWords(True)
            
            # Process audio
            recognizer.AcceptWaveform(audio_int16.tobytes())
            result_json = recognizer.FinalResult()
            result = json.loads(result_json)
            
            text = result.get('text', '').strip()
            
            # Vosk provides confidence per word, calculate average
            confidence = self._calculate_vosk_confidence(result)
            
            logger.info(f"Vosk transcription: '{text}' (conf: {confidence:.2f})")
            
            return {
                'text': text,
                'confidence': confidence,
                'segments': result.get('result', []),
                'language': 'en'
            }
            
        except Exception as e:
            logger.error(f"Vosk transcription failed: {e}")
            return {
                'text': "",
                'confidence': 0.0,
                'segments': [],
                'error': str(e)
            }
    
    def _calculate_vosk_confidence(self, result: dict) -> float:
        """
        Calculate average confidence from Vosk word-level confidences.
        
        Args:
            result: Vosk result dictionary
            
        Returns:
            Average confidence score (0-1)
        """
        words = result.get('result', [])
        
        if not words:
            text = result.get('text', '')
            return 0.5 if text else 0.0
        
        confidences = [word.get('conf', 0.5) for word in words]
        avg_confidence = np.mean(confidences)
        
        return float(np.clip(avg_confidence, 0.0, 1.0))
    
    def transcribe_stream(
        self, 
        audio_chunk: np.ndarray, 
        language: str = "en"
    ) -> Dict[str, any]:
        """
        Transcribe audio chunk in streaming mode.
        
        For Whisper: Same as regular transcription (Whisper doesn't have true streaming)
        For Vosk: Can accumulate partial results
        
        Args:
            audio_chunk: Audio chunk array
            language: Language code
            
        Returns:
            Transcription result dictionary with 'partial' flag
        """
        result = self.transcribe(audio_chunk, language)
        result['is_partial'] = False  # Can be extended for true streaming with Vosk
        return result
    
    def is_empty_transcription(self, transcription: str) -> bool:
        """
        Check if transcription is empty or contains only noise.
        
        Args:
            transcription: Transcribed text
            
        Returns:
            True if empty/noise, False otherwise
        """
        if not transcription or len(transcription.strip()) == 0:
            return True
        
        # Check for common noise patterns
        noise_patterns = [
            'blank_audio',
            'silence',
            'thank you',  # Sometimes Whisper hallucinates this
            'you',
            '...',
        ]
        
        text_lower = transcription.lower().strip()
        
        # Very short transcriptions
        if len(text_lower) < 3:
            return True
        
        # Only noise patterns
        if text_lower in noise_patterns:
            return True
        
        return False


class StreamingASR:
    """
    Streaming ASR handler for real-time audio processing.
    Manages buffering and chunk-based transcription.
    """
    
    def __init__(self, config: dict):
        """
        Initialize streaming ASR.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.asr = SpeechToText(config)
        self.buffer = np.array([], dtype=np.float32)
        self.chunk_duration = config['asr']['chunk_duration']
        self.overlap = config['asr']['overlap']
        self.sample_rate = config['asr']['sample_rate']
        self.chunk_size = int(self.chunk_duration * self.sample_rate)
        
    def add_audio(self, audio: np.ndarray) -> Optional[Dict]:
        """
        Add audio to buffer and transcribe if chunk is ready.
        
        Args:
            audio: Audio samples to add
            
        Returns:
            Transcription result if chunk is ready, None otherwise
        """
        self.buffer = np.concatenate([self.buffer, audio])
        
        if len(self.buffer) >= self.chunk_size:
            # Extract chunk
            chunk = self.buffer[:self.chunk_size]
            
            # Keep overlap for next chunk
            overlap_samples = int(self.overlap * self.sample_rate)
            self.buffer = self.buffer[-overlap_samples:] if overlap_samples > 0 else np.array([], dtype=np.float32)
            
            # Transcribe
            result = self.asr.transcribe(chunk)
            return result
        
        return None
    
    def flush(self) -> Optional[Dict]:
        """
        Process remaining buffer.
        
        Returns:
            Transcription result if buffer is not empty, None otherwise
        """
        if len(self.buffer) > self.sample_rate:  # At least 1 second
            result = self.asr.transcribe(self.buffer)
            self.buffer = np.array([], dtype=np.float32)
            return result
        
        return None
    
    def reset(self):
        """Reset buffer."""
        self.buffer = np.array([], dtype=np.float32)

