"""
Voice tone (paralinguistic) analysis using acoustic features.
Extracts MFCC, pitch, energy, ZCR, spectral features and maps them to emotions.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
import librosa
from scipy.stats import variation
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class VoiceToneAnalyzer:
    """
    Acoustic feature extraction and emotion mapping from voice characteristics.
    Analyzes paralinguistic features: pitch, energy, rhythm, spectral properties.
    """
    
    def __init__(self, config: dict):
        """
        Initialize voice tone analyzer with configuration.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.sample_rate = config['acoustic']['sample_rate']
        self.n_mfcc = config['acoustic']['n_mfcc']
        self.include_delta = config['acoustic']['include_delta']
        self.hop_length = config['acoustic']['hop_length']
        self.n_fft = config['acoustic']['n_fft']
        
        # Feature normalization ranges
        self.pitch_ranges = config['acoustic']['pitch']
        self.energy_ranges = config['acoustic']['energy']
        self.speech_rate_ranges = config['acoustic']['speech_rate']
        
        # Emotion labels
        self.emotions = config['nlp']['emotions']
    
    def extract_features(self, audio: np.ndarray) -> Dict[str, any]:
        """
        Extract comprehensive acoustic features from audio.
        
        Args:
            audio: Audio array (mono, float32)
            
        Returns:
            Dictionary containing all acoustic features
        """
        try:
            features = {}
            
            # 1. MFCC features (spectral envelope)
            mfcc = self._extract_mfcc(audio)
            features['mfcc'] = mfcc
            
            # 2. Pitch/F0 features
            pitch_features = self._extract_pitch_features(audio)
            features.update(pitch_features)
            
            # 3. Energy features (RMS)
            energy_features = self._extract_energy_features(audio)
            features.update(energy_features)
            
            # 4. Zero Crossing Rate
            zcr_features = self._extract_zcr_features(audio)
            features.update(zcr_features)
            
            # 5. Spectral features
            spectral_features = self._extract_spectral_features(audio)
            features.update(spectral_features)
            
            # 6. Speech rate estimation
            from utils import estimate_speech_rate
            features['speech_rate'] = estimate_speech_rate(audio, self.sample_rate)
            
            logger.debug(f"Extracted {len(features)} acoustic feature groups")
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return self._empty_features()
    
    def _extract_mfcc(self, audio: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Extract MFCC and delta-MFCC features.
        
        Args:
            audio: Audio array
            
        Returns:
            Dictionary with MFCC statistics
        """
        try:
            # Compute MFCCs
            mfcc = librosa.feature.mfcc(
                y=audio,
                sr=self.sample_rate,
                n_mfcc=self.n_mfcc,
                hop_length=self.hop_length,
                n_fft=self.n_fft
            )
            
            result = {
                'mean': np.mean(mfcc, axis=1),
                'std': np.std(mfcc, axis=1),
                'median': np.median(mfcc, axis=1)
            }
            
            # Delta MFCCs (velocity)
            if self.include_delta:
                delta_mfcc = librosa.feature.delta(mfcc)
                result['delta_mean'] = np.mean(delta_mfcc, axis=1)
                result['delta_std'] = np.std(delta_mfcc, axis=1)
            
            return result
            
        except Exception as e:
            logger.warning(f"MFCC extraction failed: {e}")
            return {'mean': np.zeros(self.n_mfcc)}
    
    def _extract_pitch_features(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Extract pitch (F0) statistics using YIN algorithm.
        
        Args:
            audio: Audio array
            
        Returns:
            Dictionary with pitch statistics
        """
        try:
            # Extract F0 using pyin (probabilistic YIN)
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio,
                fmin=librosa.note_to_hz('C2'),  # ~65 Hz
                fmax=librosa.note_to_hz('C7'),  # ~2093 Hz
                sr=self.sample_rate,
                hop_length=self.hop_length
            )
            
            # Filter out unvoiced frames (NaN values)
            f0_voiced = f0[~np.isnan(f0)]
            
            if len(f0_voiced) == 0:
                logger.warning("No voiced frames detected")
                return {
                    'pitch_mean': 0.0,
                    'pitch_std': 0.0,
                    'pitch_min': 0.0,
                    'pitch_max': 0.0,
                    'pitch_range': 0.0,
                    'pitch_variation': 0.0,
                    'voiced_ratio': 0.0
                }
            
            # Calculate statistics
            pitch_mean = float(np.mean(f0_voiced))
            pitch_std = float(np.std(f0_voiced))
            pitch_min = float(np.min(f0_voiced))
            pitch_max = float(np.max(f0_voiced))
            pitch_range = pitch_max - pitch_min
            
            # Coefficient of variation (normalized std)
            pitch_variation = variation(f0_voiced) if len(f0_voiced) > 1 else 0.0
            
            # Voiced ratio
            voiced_ratio = len(f0_voiced) / len(f0)
            
            return {
                'pitch_mean': pitch_mean,
                'pitch_std': pitch_std,
                'pitch_min': pitch_min,
                'pitch_max': pitch_max,
                'pitch_range': pitch_range,
                'pitch_variation': float(pitch_variation),
                'voiced_ratio': float(voiced_ratio)
            }
            
        except Exception as e:
            logger.warning(f"Pitch extraction failed: {e}")
            return {
                'pitch_mean': 150.0,  # Default neutral pitch
                'pitch_std': 0.0,
                'pitch_min': 150.0,
                'pitch_max': 150.0,
                'pitch_range': 0.0,
                'pitch_variation': 0.0,
                'voiced_ratio': 0.5
            }
    
    def _extract_energy_features(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Extract RMS energy features.
        
        Args:
            audio: Audio array
            
        Returns:
            Dictionary with energy statistics
        """
        try:
            # Compute RMS energy
            rms = librosa.feature.rms(
                y=audio,
                hop_length=self.hop_length,
                frame_length=self.n_fft
            )[0]
            
            energy_mean = float(np.mean(rms))
            energy_std = float(np.std(rms))
            energy_max = float(np.max(rms))
            
            # Dynamic range
            energy_dynamic_range = energy_max / (energy_mean + 1e-8)
            
            return {
                'energy_mean': energy_mean,
                'energy_std': energy_std,
                'energy_max': energy_max,
                'energy_dynamic_range': float(energy_dynamic_range)
            }
            
        except Exception as e:
            logger.warning(f"Energy extraction failed: {e}")
            return {
                'energy_mean': 0.01,
                'energy_std': 0.0,
                'energy_max': 0.01,
                'energy_dynamic_range': 1.0
            }
    
    def _extract_zcr_features(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Extract Zero Crossing Rate features.
        
        Args:
            audio: Audio array
            
        Returns:
            Dictionary with ZCR statistics
        """
        try:
            zcr = librosa.feature.zero_crossing_rate(
                audio,
                hop_length=self.hop_length
            )[0]
            
            return {
                'zcr_mean': float(np.mean(zcr)),
                'zcr_std': float(np.std(zcr))
            }
            
        except Exception as e:
            logger.warning(f"ZCR extraction failed: {e}")
            return {'zcr_mean': 0.1, 'zcr_std': 0.0}
    
    def _extract_spectral_features(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Extract spectral features: centroid, rolloff, flux.
        
        Args:
            audio: Audio array
            
        Returns:
            Dictionary with spectral statistics
        """
        try:
            # Spectral centroid (brightness)
            centroid = librosa.feature.spectral_centroid(
                y=audio,
                sr=self.sample_rate,
                hop_length=self.hop_length,
                n_fft=self.n_fft
            )[0]
            
            # Spectral rolloff (frequency below which X% of energy is contained)
            rolloff = librosa.feature.spectral_rolloff(
                y=audio,
                sr=self.sample_rate,
                hop_length=self.hop_length,
                n_fft=self.n_fft
            )[0]
            
            # Spectral flux (rate of change in spectrum)
            spec = np.abs(librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length))
            flux = np.sqrt(np.sum(np.diff(spec, axis=1) ** 2, axis=0))
            
            return {
                'spectral_centroid_mean': float(np.mean(centroid)),
                'spectral_centroid_std': float(np.std(centroid)),
                'spectral_rolloff_mean': float(np.mean(rolloff)),
                'spectral_flux_mean': float(np.mean(flux))
            }
            
        except Exception as e:
            logger.warning(f"Spectral feature extraction failed: {e}")
            return {
                'spectral_centroid_mean': 1000.0,
                'spectral_centroid_std': 0.0,
                'spectral_rolloff_mean': 2000.0,
                'spectral_flux_mean': 0.0
            }
    
    def _empty_features(self) -> Dict[str, any]:
        """Return empty/default features."""
        return {
            'pitch_mean': 150.0,
            'pitch_std': 0.0,
            'energy_mean': 0.01,
            'speech_rate': 3.0,
            'zcr_mean': 0.1,
            'spectral_centroid_mean': 1000.0
        }
    
    def map_features_to_emotions(self, features: Dict[str, any]) -> Dict[str, float]:
        """
        Map acoustic features to emotion probabilities using rule-based system.
        
        Implementation of the emotion mapping rules specified in requirements:
        - High pitch + variance + energy → joy/anger
        - High pitch variance + fast rate + high RMS → anger
        - Low energy + slow rate + low centroid → sadness
        - Irregular pitch + high ZCR → fear
        - Low variance + neutral features → neutral
        
        Args:
            features: Extracted acoustic features
            
        Returns:
            Dictionary of emotion probabilities
        """
        try:
            # Initialize scores
            emotion_scores = {emotion: 0.0 for emotion in self.emotions}
            
            # Extract key features
            pitch_mean = features.get('pitch_mean', 150.0)
            pitch_std = features.get('pitch_std', 0.0)
            pitch_variation = features.get('pitch_variation', 0.0)
            energy = features.get('energy_mean', 0.01)
            speech_rate = features.get('speech_rate', 3.0)
            zcr = features.get('zcr_mean', 0.1)
            spectral_centroid = features.get('spectral_centroid_mean', 1000.0)
            
            # Normalize features to [0, 1] range for scoring
            pitch_norm = self._normalize(pitch_mean, self.pitch_ranges['low'], self.pitch_ranges['high'])
            energy_norm = self._normalize(energy, self.energy_ranges['low'], self.energy_ranges['high'])
            rate_norm = self._normalize(speech_rate, self.speech_rate_ranges['slow'], self.speech_rate_ranges['fast'])
            
            # Rule 1: JOY - High pitch, high energy, fast rate, high centroid
            joy_score = 0.0
            if pitch_norm > 0.6 and energy_norm > 0.6:
                joy_score += 0.4
            if rate_norm > 0.6:
                joy_score += 0.3
            if spectral_centroid > 2000:
                joy_score += 0.3
            emotion_scores['joy'] = np.clip(joy_score, 0, 1)
            
            # Rule 2: ANGER - High pitch variance, high energy, fast rate, high ZCR
            anger_score = 0.0
            if pitch_std > 30 and energy_norm > 0.7:
                anger_score += 0.4
            if rate_norm > 0.7:
                anger_score += 0.3
            if zcr > 0.15:
                anger_score += 0.3
            emotion_scores['anger'] = np.clip(anger_score, 0, 1)
            
            # Rule 3: SADNESS - Low energy, slow rate, low pitch, low centroid
            sadness_score = 0.0
            if energy_norm < 0.4:
                sadness_score += 0.4
            if rate_norm < 0.4:
                sadness_score += 0.3
            if spectral_centroid < 1500:
                sadness_score += 0.3
            emotion_scores['sadness'] = np.clip(sadness_score, 0, 1)
            
            # Rule 4: FEAR - Irregular pitch (high variation), high ZCR, moderate energy
            fear_score = 0.0
            if pitch_variation > 0.3:
                fear_score += 0.4
            if zcr > 0.15:
                fear_score += 0.3
            if 0.3 < energy_norm < 0.7:
                fear_score += 0.3
            emotion_scores['fear'] = np.clip(fear_score, 0, 1)
            
            # Rule 5: SURPRISE - High pitch, sudden energy changes, fast rate
            surprise_score = 0.0
            if pitch_norm > 0.7:
                surprise_score += 0.4
            energy_dynamic = features.get('energy_dynamic_range', 1.0)
            if energy_dynamic > 3.0:
                surprise_score += 0.3
            if rate_norm > 0.6:
                surprise_score += 0.3
            emotion_scores['surprise'] = np.clip(surprise_score, 0, 1)
            
            # Rule 6: DISGUST - Low energy, low pitch, slow rate
            disgust_score = 0.0
            if pitch_norm < 0.4 and energy_norm < 0.5:
                disgust_score += 0.4
            if rate_norm < 0.5:
                disgust_score += 0.3
            if spectral_centroid < 1800:
                disgust_score += 0.3
            emotion_scores['disgust'] = np.clip(disgust_score, 0, 1)
            
            # Rule 7: NEUTRAL - Moderate values across all features
            neutral_score = 0.0
            if 0.4 <= pitch_norm <= 0.6:
                neutral_score += 0.3
            if 0.4 <= energy_norm <= 0.6:
                neutral_score += 0.3
            if 0.4 <= rate_norm <= 0.6:
                neutral_score += 0.2
            if pitch_variation < 0.2:
                neutral_score += 0.2
            emotion_scores['neutral'] = np.clip(neutral_score, 0, 1)
            
            # Normalize to sum to 1.0 (probability distribution)
            total_score = sum(emotion_scores.values())
            if total_score > 0:
                emotion_scores = {
                    emotion: score / total_score 
                    for emotion, score in emotion_scores.items()
                }
            else:
                # If no rules triggered, default to neutral
                emotion_scores['neutral'] = 1.0
            
            logger.debug(f"Tone emotion mapping: {emotion_scores}")
            
            return emotion_scores
            
        except Exception as e:
            logger.error(f"Feature-to-emotion mapping failed: {e}")
            # Return neutral distribution
            return {emotion: 1.0/len(self.emotions) for emotion in self.emotions}
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize value to [0, 1] range.
        
        Args:
            value: Value to normalize
            min_val: Minimum of range
            max_val: Maximum of range
            
        Returns:
            Normalized value (0-1)
        """
        if max_val == min_val:
            return 0.5
        
        normalized = (value - min_val) / (max_val - min_val)
        return float(np.clip(normalized, 0.0, 1.0))
    
    def analyze(self, audio: np.ndarray) -> Dict[str, any]:
        """
        Full acoustic analysis pipeline: extract features and map to emotions.
        
        Args:
            audio: Audio array
            
        Returns:
            Dictionary containing:
                - features: Extracted acoustic features
                - emotions: Emotion probability distribution
                - top_emotion: Most likely emotion from tone
                - confidence: Confidence in top emotion
        """
        try:
            # Extract features
            features = self.extract_features(audio)
            
            # Map to emotions
            emotion_scores = self.map_features_to_emotions(features)
            
            # Get top emotion
            top_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[top_emotion]
            
            # Select key features for output (keep JSON small)
            key_features = {
                'pitch_mean': features.get('pitch_mean', 0),
                'pitch_std': features.get('pitch_std', 0),
                'energy_mean': features.get('energy_mean', 0),
                'speech_rate': features.get('speech_rate', 0),
                'zcr_mean': features.get('zcr_mean', 0),
                'spectral_centroid_mean': features.get('spectral_centroid_mean', 0)
            }
            
            return {
                'emotions': emotion_scores,
                'top_emotion': top_emotion,
                'confidence': confidence,
                'features': key_features,
                'full_features': features  # For debugging/logging
            }
            
        except Exception as e:
            logger.error(f"Voice tone analysis failed: {e}")
            return {
                'emotions': {emotion: 1.0/len(self.emotions) for emotion in self.emotions},
                'top_emotion': 'neutral',
                'confidence': 0.0,
                'features': {},
                'error': str(e)
            }

