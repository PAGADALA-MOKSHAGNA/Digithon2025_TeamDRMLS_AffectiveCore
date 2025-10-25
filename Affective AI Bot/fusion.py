"""
Emotion fusion module for combining text and tone emotions.
Implements dynamic alpha weighting, temporal smoothing, and intensity mapping.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)


class EmotionFusion:
    """
    Fuse text-based and tone-based emotion predictions.
    
    Features:
    - Dynamic alpha weighting based on text confidence
    - Temporal smoothing over multiple predictions
    - Intensity mapping (Low/Medium/High)
    - Mixed emotion detection
    """
    
    def __init__(self, config: dict):
        """
        Initialize emotion fusion module.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.fusion_config = config['fusion']
        self.emotions = config['nlp']['emotions']
        
        # Base weights
        self.base_text_weight = self.fusion_config['text_weight']
        self.base_tone_weight = self.fusion_config['tone_weight']
        
        # Dynamic alpha configuration
        self.dynamic_alpha_enabled = self.fusion_config['dynamic_alpha']['enabled']
        self.high_conf_threshold = self.fusion_config['dynamic_alpha']['high_confidence_threshold']
        self.high_conf_alpha = self.fusion_config['dynamic_alpha']['high_confidence_alpha']
        self.low_conf_threshold = self.fusion_config['dynamic_alpha']['low_confidence_threshold']
        self.low_conf_alpha = self.fusion_config['dynamic_alpha']['low_confidence_alpha']
        
        # Temporal smoothing
        self.smoothing_enabled = self.fusion_config['smoothing']['enabled']
        self.smoothing_window = self.fusion_config['smoothing']['window_size']
        self.prediction_history = deque(maxlen=self.smoothing_window)
        
        # Intensity thresholds
        self.intensity_low = self.fusion_config['intensity']['low']
        self.intensity_medium = self.fusion_config['intensity']['medium']
        
        # Mixed emotion detection
        self.mixed_emotion_enabled = self.fusion_config['mixed_emotion']['enabled']
        self.mixed_conf_threshold = self.fusion_config['mixed_emotion']['confidence_threshold']
        
        logger.info("Emotion fusion module initialized")
    
    def calculate_dynamic_alpha(self, text_confidence: float) -> float:
        """
        Calculate dynamic alpha (text weight) based on text confidence.
        
        Rule: 
        - High text confidence (>0.8) → α = 0.85 (trust text more)
        - Low text confidence (<0.4) → α = 0.40 (trust tone more)
        - Linear interpolation in between
        
        Args:
            text_confidence: Confidence score from text analysis (0-1)
            
        Returns:
            Dynamic alpha value (0-1)
        """
        if not self.dynamic_alpha_enabled:
            return self.base_text_weight
        
        # Clamp confidence
        text_confidence = np.clip(text_confidence, 0.0, 1.0)
        
        # High confidence region
        if text_confidence >= self.high_conf_threshold:
            alpha = self.high_conf_alpha
        
        # Low confidence region
        elif text_confidence <= self.low_conf_threshold:
            alpha = self.low_conf_alpha
        
        # Linear interpolation
        else:
            # Map confidence from [low_threshold, high_threshold] to [low_alpha, high_alpha]
            conf_range = self.high_conf_threshold - self.low_conf_threshold
            alpha_range = self.high_conf_alpha - self.low_conf_alpha
            
            normalized_conf = (text_confidence - self.low_conf_threshold) / conf_range
            alpha = self.low_conf_alpha + (normalized_conf * alpha_range)
        
        alpha = float(np.clip(alpha, 0.0, 1.0))
        logger.debug(f"Dynamic alpha: {alpha:.3f} (text_conf: {text_confidence:.3f})")
        
        return alpha
    
    def fuse_emotions(
        self,
        text_emotions: Dict[str, float],
        tone_emotions: Dict[str, float],
        text_confidence: float,
        tone_confidence: float
    ) -> Tuple[Dict[str, float], float, Dict[str, any]]:
        """
        Fuse text and tone emotion predictions using weighted fusion.
        
        Formula: final_score(e) = α * text_score(e) + (1-α) * tone_score(e)
        
        Args:
            text_emotions: Text emotion probability distribution
            tone_emotions: Tone emotion probability distribution
            text_confidence: Overall text confidence
            tone_confidence: Overall tone confidence
            
        Returns:
            Tuple of (fused_emotions, fusion_confidence, metadata)
        """
        try:
            # Calculate dynamic alpha
            alpha = self.calculate_dynamic_alpha(text_confidence)
            beta = 1.0 - alpha
            
            # Fuse emotion scores
            fused_emotions = {}
            for emotion in self.emotions:
                text_score = text_emotions.get(emotion, 0.0)
                tone_score = tone_emotions.get(emotion, 0.0)
                
                fused_score = alpha * text_score + beta * tone_score
                fused_emotions[emotion] = float(fused_score)
            
            # Normalize (should already sum to ~1, but ensure it)
            total = sum(fused_emotions.values())
            if total > 0:
                fused_emotions = {
                    emotion: score / total 
                    for emotion, score in fused_emotions.items()
                }
            
            # Calculate fusion confidence (weighted average)
            fusion_confidence = alpha * text_confidence + beta * tone_confidence
            
            # Metadata
            metadata = {
                'alpha': alpha,
                'beta': beta,
                'text_confidence': text_confidence,
                'tone_confidence': tone_confidence,
                'fusion_confidence': fusion_confidence
            }
            
            logger.debug(
                f"Fused emotions with α={alpha:.3f}: "
                f"{max(fused_emotions, key=fused_emotions.get)}"
            )
            
            return fused_emotions, fusion_confidence, metadata
            
        except Exception as e:
            logger.error(f"Emotion fusion failed: {e}")
            # Fallback to text-only
            return text_emotions, text_confidence, {'error': str(e), 'fallback': True}
    
    def detect_mixed_emotion(
        self,
        text_emotions: Dict[str, float],
        tone_emotions: Dict[str, float],
        text_confidence: float,
        tone_confidence: float
    ) -> Dict[str, any]:
        """
        Detect if text and tone disagree (mixed emotion or sarcasm).
        
        Rule: If top text emotion != top tone emotion AND both confidences > 0.6,
        flag as mixed emotion.
        
        Args:
            text_emotions: Text emotion scores
            tone_emotions: Tone emotion scores
            text_confidence: Text confidence
            tone_confidence: Tone confidence
            
        Returns:
            Dictionary with mixed emotion information
        """
        if not self.mixed_emotion_enabled:
            return {'is_mixed': False}
        
        try:
            # Get top emotions
            top_text = max(text_emotions, key=text_emotions.get)
            top_tone = max(tone_emotions, key=tone_emotions.get)
            
            # Check if they disagree and both are confident
            is_mixed = (
                top_text != top_tone and
                text_confidence > self.mixed_conf_threshold and
                tone_confidence > self.mixed_conf_threshold
            )
            
            result = {
                'is_mixed': is_mixed,
                'text_emotion': top_text,
                'tone_emotion': top_tone,
                'note': ""
            }
            
            if is_mixed:
                result['note'] = (
                    f"Mixed emotion detected: text suggests {top_text}, "
                    f"tone suggests {top_tone}. Possible sarcasm or conflicting emotions."
                )
                logger.info(result['note'])
            
            return result
            
        except Exception as e:
            logger.warning(f"Mixed emotion detection failed: {e}")
            return {'is_mixed': False, 'error': str(e)}
    
    def apply_temporal_smoothing(
        self,
        current_emotions: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Apply temporal smoothing by averaging over recent predictions.
        
        This reduces jitter in real-time predictions.
        
        Args:
            current_emotions: Current emotion scores
            
        Returns:
            Smoothed emotion scores
        """
        if not self.smoothing_enabled:
            return current_emotions
        
        try:
            # Add current prediction to history
            self.prediction_history.append(current_emotions)
            
            # Not enough history yet
            if len(self.prediction_history) < 2:
                return current_emotions
            
            # Average over history
            smoothed_emotions = {emotion: 0.0 for emotion in self.emotions}
            
            for past_emotions in self.prediction_history:
                for emotion in self.emotions:
                    smoothed_emotions[emotion] += past_emotions.get(emotion, 0.0)
            
            # Normalize by window size
            window_size = len(self.prediction_history)
            smoothed_emotions = {
                emotion: score / window_size 
                for emotion, score in smoothed_emotions.items()
            }
            
            logger.debug(f"Applied temporal smoothing (window={window_size})")
            
            return smoothed_emotions
            
        except Exception as e:
            logger.warning(f"Temporal smoothing failed: {e}")
            return current_emotions
    
    def map_intensity(self, emotion_score: float) -> str:
        """
        Map emotion score to intensity level.
        
        Rules:
        - Low: score < 0.5
        - Medium: 0.5 ≤ score < 0.75
        - High: score ≥ 0.75
        
        Args:
            emotion_score: Maximum emotion score (0-1)
            
        Returns:
            Intensity level: "Low", "Medium", or "High"
        """
        if emotion_score < self.intensity_low:
            return "Low"
        elif emotion_score < self.intensity_medium:
            return "Medium"
        else:
            return "High"
    
    def get_action_trigger(
        self,
        emotion: str,
        intensity: str
    ) -> Dict[str, str]:
        """
        Get ESP32 action triggers for given emotion and intensity.
        
        Args:
            emotion: Detected emotion
            intensity: Intensity level
            
        Returns:
            Dictionary with LED color, quote category, and servo gesture
        """
        actions = self.config['output']['actions'].get(
            emotion,
            {
                'led_color': 'white',
                'quote_category': 'neutral',
                'servo_gesture': 'idle'
            }
        )
        
        # Modify gesture intensity
        gesture = actions['servo_gesture']
        if intensity == "High":
            gesture = f"{gesture}_intense"
        elif intensity == "Low":
            gesture = f"{gesture}_gentle"
        
        return {
            'led_color': actions['led_color'],
            'quote_category': actions['quote_category'],
            'servo_gesture': gesture
        }
    
    def reset_history(self):
        """Reset temporal smoothing history."""
        self.prediction_history.clear()
        logger.info("Prediction history cleared")
    
    def process(
        self,
        text_emotions: Dict[str, float],
        tone_emotions: Dict[str, float],
        text_confidence: float,
        tone_confidence: float,
        transcription: str = "",
        apply_smoothing: bool = True
    ) -> Dict[str, any]:
        """
        Complete fusion processing pipeline.
        
        Args:
            text_emotions: Text emotion probability distribution
            tone_emotions: Tone emotion probability distribution
            text_confidence: Text confidence score
            tone_confidence: Tone confidence score
            transcription: Original transcription text
            apply_smoothing: Whether to apply temporal smoothing
            
        Returns:
            Complete emotion analysis result with all metadata
        """
        try:
            # 1. Detect mixed emotions
            mixed_info = self.detect_mixed_emotion(
                text_emotions,
                tone_emotions,
                text_confidence,
                tone_confidence
            )
            
            # 2. Fuse emotions
            fused_emotions, fusion_confidence, fusion_metadata = self.fuse_emotions(
                text_emotions,
                tone_emotions,
                text_confidence,
                tone_confidence
            )
            
            # 3. Apply temporal smoothing (if enabled)
            if apply_smoothing:
                smoothed_emotions = self.apply_temporal_smoothing(fused_emotions)
            else:
                smoothed_emotions = fused_emotions
            
            # 4. Get final emotion and confidence
            final_emotion = max(smoothed_emotions, key=smoothed_emotions.get)
            final_confidence = smoothed_emotions[final_emotion]
            
            # 5. Adjust confidence if mixed emotion detected
            if mixed_info.get('is_mixed', False):
                final_confidence *= 0.7  # Reduce confidence for mixed emotions
            
            # 6. Map intensity
            intensity = self.map_intensity(final_confidence)
            
            # 7. Get action triggers
            action_trigger = self.get_action_trigger(final_emotion, intensity)
            
            # 8. Build result
            result = {
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'transcription': transcription,
                'emotion': final_emotion,
                'intensity': intensity,
                'confidence': round(final_confidence, 3),
                'breakdown': {
                    'text_emotion': {
                        k: round(v, 3) for k, v in text_emotions.items()
                        if v > 0.01  # Only include significant scores
                    },
                    'tone_emotion': {
                        k: round(v, 3) for k, v in tone_emotions.items()
                        if v > 0.01
                    },
                    'fused_emotion': {
                        k: round(v, 3) for k, v in smoothed_emotions.items()
                        if v > 0.01
                    }
                },
                'action_trigger': action_trigger,
                'notes': {
                    'fusion_alpha': round(fusion_metadata.get('alpha', self.base_text_weight), 3),
                    'fallback_mode': fusion_metadata.get('fallback', False),
                    'mixed_emotion': mixed_info.get('is_mixed', False),
                    'smoothing_applied': apply_smoothing,
                    'smoothing_window': len(self.prediction_history) if apply_smoothing else 0
                }
            }
            
            # Add mixed emotion note if present
            if mixed_info.get('note'):
                result['notes']['mixed_emotion_details'] = mixed_info['note']
            
            logger.info(
                f"Final emotion: {final_emotion} "
                f"(intensity: {intensity}, confidence: {final_confidence:.3f})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Fusion processing failed: {e}")
            # Return error result
            return {
                'timestamp': datetime.now(pytz.UTC).isoformat(),
                'transcription': transcription,
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
                    'error': str(e),
                    'fallback_mode': True,
                    'mixed_emotion': False
                }
            }


def compress_json_output(result: Dict[str, any], max_size: int = 1024) -> Dict[str, any]:
    """
    Compress JSON output to fit within size limit for ESP32.
    
    Args:
        result: Full emotion analysis result
        max_size: Maximum JSON size in bytes
        
    Returns:
        Compressed result dictionary
    """
    import json
    
    # Start with minimal output
    compressed = {
        'ts': result['timestamp'][:19],  # Remove timezone for brevity
        'text': result['transcription'][:50],  # Truncate long transcriptions
        'emotion': result['emotion'],
        'intensity': result['intensity'][0],  # L/M/H
        'conf': result['confidence'],
        'action': result['action_trigger']
    }
    
    # Check size
    size = len(json.dumps(compressed))
    
    # If room, add breakdown with top 3 emotions only
    if size < max_size * 0.7:
        fused = result['breakdown'].get('fused_emotion', {})
        top3 = dict(sorted(fused.items(), key=lambda x: x[1], reverse=True)[:3])
        compressed['emotions'] = top3
    
    # If still room, add notes
    if size < max_size * 0.85:
        compressed['notes'] = {
            'alpha': result['notes'].get('fusion_alpha'),
            'mixed': result['notes'].get('mixed_emotion', False)
        }
    
    logger.debug(f"Compressed JSON size: {len(json.dumps(compressed))} bytes")
    
    return compressed

