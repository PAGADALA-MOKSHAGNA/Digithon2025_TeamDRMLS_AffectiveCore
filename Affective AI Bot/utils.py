"""
Utility functions for audio processing, VAD, chunking, and normalization.
"""

import logging
import numpy as np
import librosa
import soundfile as sf
from typing import Tuple, List, Optional, Generator
import webrtcvad
import noisereduce as nr
from pydub import AudioSegment
import io

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Audio preprocessing utilities including VAD, noise reduction, and normalization."""
    
    def __init__(self, config: dict):
        """
        Initialize audio processor with configuration.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.sample_rate = config['asr']['sample_rate']
        self.vad_enabled = config['vad']['enabled']
        self.noise_reduction = config['preprocessing']['noise_reduction']['enabled']
        self.normalization = config['preprocessing']['normalization']['enabled']
        
        if self.vad_enabled:
            self.vad = webrtcvad.Vad(config['vad']['aggressiveness'])
            self.frame_duration = config['vad']['frame_duration']
            self.min_speech_duration = config['vad']['min_speech_duration']
        
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file and resample to target sample rate.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            audio, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            logger.info(f"Loaded audio from {file_path}: {len(audio)} samples at {sr}Hz")
            return audio, sr
        except Exception as e:
            logger.error(f"Failed to load audio file {file_path}: {e}")
            raise
    
    def normalize_audio(self, audio: np.ndarray, target_dbfs: float = -20.0) -> np.ndarray:
        """
        Normalize audio to target dBFS level.
        
        Args:
            audio: Input audio array
            target_dbfs: Target loudness in dBFS
            
        Returns:
            Normalized audio array
        """
        if not self.normalization:
            return audio
        
        try:
            # Convert to AudioSegment for dBFS calculation
            audio_int16 = (audio * 32767).astype(np.int16)
            audio_segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=self.sample_rate,
                sample_width=2,
                channels=1
            )
            
            # Calculate gain needed
            change_in_dbfs = target_dbfs - audio_segment.dBFS
            normalized = audio_segment.apply_gain(change_in_dbfs)
            
            # Convert back to numpy array
            samples = np.array(normalized.get_array_of_samples())
            normalized_audio = samples.astype(np.float32) / 32767.0
            
            logger.debug(f"Normalized audio: {audio_segment.dBFS:.2f} -> {target_dbfs:.2f} dBFS")
            return normalized_audio
            
        except Exception as e:
            logger.warning(f"Normalization failed: {e}. Returning original audio.")
            return audio
    
    def reduce_noise(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply noise reduction to audio signal.
        
        Args:
            audio: Input audio array
            
        Returns:
            Noise-reduced audio array
        """
        if not self.noise_reduction:
            return audio
        
        try:
            reduced = nr.reduce_noise(
                y=audio,
                sr=self.sample_rate,
                stationary=self.config['preprocessing']['noise_reduction']['stationary']
            )
            logger.debug("Applied noise reduction")
            return reduced
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}. Returning original audio.")
            return audio
    
    def preprocess_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply full preprocessing pipeline: noise reduction + normalization.
        
        Args:
            audio: Raw audio array
            
        Returns:
            Preprocessed audio array
        """
        audio = self.reduce_noise(audio)
        audio = self.normalize_audio(
            audio, 
            self.config['preprocessing']['normalization'].get('target_dbfs', -20.0)
        )
        return audio
    
    def apply_vad(self, audio: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Apply Voice Activity Detection to filter out silence.
        
        Args:
            audio: Input audio array
            
        Returns:
            Tuple of (filtered_audio, speech_ratio)
        """
        if not self.vad_enabled:
            return audio, 1.0
        
        try:
            # Convert to 16-bit PCM
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Frame size in samples
            frame_size = int(self.sample_rate * self.frame_duration / 1000)
            
            # Process frames
            speech_frames = []
            total_frames = 0
            speech_frame_count = 0
            
            for i in range(0, len(audio_int16) - frame_size, frame_size):
                frame = audio_int16[i:i + frame_size].tobytes()
                total_frames += 1
                
                # VAD returns True if speech is detected
                is_speech = self.vad.is_speech(frame, self.sample_rate)
                
                if is_speech:
                    speech_frames.append(audio[i:i + frame_size])
                    speech_frame_count += 1
            
            if not speech_frames:
                logger.warning("No speech detected in audio")
                return audio, 0.0
            
            # Concatenate speech frames
            filtered_audio = np.concatenate(speech_frames)
            speech_ratio = speech_frame_count / total_frames if total_frames > 0 else 0.0
            
            # Check minimum speech duration
            speech_duration = len(filtered_audio) / self.sample_rate
            if speech_duration < self.min_speech_duration:
                logger.warning(f"Speech duration {speech_duration:.2f}s below minimum")
                return audio, speech_ratio
            
            logger.debug(f"VAD: {speech_ratio:.2%} speech detected")
            return filtered_audio, speech_ratio
            
        except Exception as e:
            logger.error(f"VAD failed: {e}. Returning original audio.")
            return audio, 1.0
    
    def chunk_audio(
        self, 
        audio: np.ndarray, 
        chunk_duration: float, 
        overlap: float
    ) -> Generator[Tuple[np.ndarray, float, float], None, None]:
        """
        Split audio into overlapping chunks for streaming processing.
        
        Args:
            audio: Input audio array
            chunk_duration: Duration of each chunk in seconds
            overlap: Overlap duration in seconds
            
        Yields:
            Tuples of (chunk_audio, start_time, end_time)
        """
        chunk_samples = int(chunk_duration * self.sample_rate)
        overlap_samples = int(overlap * self.sample_rate)
        step = chunk_samples - overlap_samples
        
        if step <= 0:
            raise ValueError("Overlap must be less than chunk duration")
        
        total_duration = len(audio) / self.sample_rate
        
        for start_idx in range(0, len(audio) - chunk_samples + 1, step):
            end_idx = start_idx + chunk_samples
            chunk = audio[start_idx:end_idx]
            
            start_time = start_idx / self.sample_rate
            end_time = end_idx / self.sample_rate
            
            logger.debug(f"Chunk: {start_time:.2f}s - {end_time:.2f}s")
            yield chunk, start_time, end_time
        
        # Handle remaining audio if any
        if len(audio) % step != 0:
            remaining = audio[-(chunk_samples):]
            if len(remaining) >= self.sample_rate:  # At least 1 second
                start_time = (len(audio) - len(remaining)) / self.sample_rate
                end_time = len(audio) / self.sample_rate
                logger.debug(f"Final chunk: {start_time:.2f}s - {end_time:.2f}s")
                yield remaining, start_time, end_time


class AudioValidator:
    """Validate audio input and detect non-speech signals."""
    
    @staticmethod
    def is_valid_audio(audio: np.ndarray, min_duration: float = 0.5) -> Tuple[bool, str]:
        """
        Check if audio is valid for processing.
        
        Args:
            audio: Input audio array
            min_duration: Minimum required duration in seconds
            
        Returns:
            Tuple of (is_valid, reason)
        """
        if audio is None or len(audio) == 0:
            return False, "Empty audio"
        
        if np.all(audio == 0):
            return False, "Silent audio (all zeros)"
        
        # Check RMS energy
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.001:
            return False, "Audio too quiet (low RMS)"
        
        # Check for clipping
        clipping_ratio = np.sum(np.abs(audio) > 0.99) / len(audio)
        if clipping_ratio > 0.1:
            return False, f"Audio clipping detected ({clipping_ratio:.1%})"
        
        return True, "Valid"
    
    @staticmethod
    def detect_non_speech(audio: np.ndarray, sr: int) -> Tuple[bool, str]:
        """
        Detect if audio contains non-speech signals (music, noise, etc.).
        
        Args:
            audio: Input audio array
            sr: Sample rate
            
        Returns:
            Tuple of (is_non_speech, signal_type)
        """
        try:
            # Extract features for classification
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            
            # High ZCR throughout might indicate noise
            if np.mean(zcr) > 0.3:
                return True, "noise"
            
            # Very regular spectral patterns might indicate music
            centroid_std = np.std(spectral_centroid)
            if centroid_std < 200:
                return True, "music_or_tone"
            
            return False, "speech"
            
        except Exception as e:
            logger.warning(f"Non-speech detection failed: {e}")
            return False, "unknown"


def estimate_speech_rate(audio: np.ndarray, sr: int) -> float:
    """
    Estimate speech rate in syllables per second using energy-based approach.
    
    Args:
        audio: Input audio array
        sr: Sample rate
        
    Returns:
        Estimated speech rate (syllables/second)
    """
    try:
        # Calculate RMS energy in frames
        frame_length = int(0.02 * sr)  # 20ms frames
        hop_length = int(0.01 * sr)    # 10ms hop
        
        rms = librosa.feature.rms(
            y=audio,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        # Find peaks in energy (potential syllable nuclei)
        from scipy.signal import find_peaks
        
        # Normalize RMS
        rms_norm = (rms - np.min(rms)) / (np.max(rms) - np.min(rms) + 1e-8)
        
        # Find peaks with minimum distance and height
        peaks, _ = find_peaks(
            rms_norm,
            distance=int(0.1 * sr / hop_length),  # Min 100ms between syllables
            height=0.3
        )
        
        # Calculate rate
        duration = len(audio) / sr
        syllable_count = len(peaks)
        speech_rate = syllable_count / duration if duration > 0 else 0.0
        
        logger.debug(f"Estimated speech rate: {speech_rate:.2f} syllables/sec")
        return speech_rate
        
    except Exception as e:
        logger.error(f"Speech rate estimation failed: {e}")
        return 3.0  # Return default average rate

