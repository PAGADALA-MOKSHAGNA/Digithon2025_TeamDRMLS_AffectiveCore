"""
Unit tests for fusion module.
"""

import pytest
import numpy as np
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from fusion import EmotionFusion, compress_json_output


@pytest.fixture
def config():
    """Load test configuration."""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_emotions():
    """Sample emotion distributions."""
    text_emotions = {
        'joy': 0.7,
        'sadness': 0.1,
        'anger': 0.05,
        'fear': 0.05,
        'disgust': 0.05,
        'surprise': 0.03,
        'neutral': 0.02
    }
    
    tone_emotions = {
        'joy': 0.6,
        'sadness': 0.15,
        'anger': 0.1,
        'fear': 0.05,
        'disgust': 0.05,
        'surprise': 0.03,
        'neutral': 0.02
    }
    
    return text_emotions, tone_emotions


class TestEmotionFusion:
    """Tests for EmotionFusion class."""
    
    def test_initialization(self, config):
        """Test fusion module initialization."""
        fusion = EmotionFusion(config)
        
        assert fusion.base_text_weight == config['fusion']['text_weight']
        assert fusion.smoothing_enabled == config['fusion']['smoothing']['enabled']
    
    def test_dynamic_alpha_high_confidence(self, config):
        """Test dynamic alpha calculation with high confidence."""
        fusion = EmotionFusion(config)
        
        alpha = fusion.calculate_dynamic_alpha(0.9)
        
        # High confidence should give high alpha (trust text more)
        assert alpha > 0.8
    
    def test_dynamic_alpha_low_confidence(self, config):
        """Test dynamic alpha calculation with low confidence."""
        fusion = EmotionFusion(config)
        
        alpha = fusion.calculate_dynamic_alpha(0.3)
        
        # Low confidence should give low alpha (trust tone more)
        assert alpha < 0.5
    
    def test_fuse_emotions(self, config, sample_emotions):
        """Test emotion fusion."""
        fusion = EmotionFusion(config)
        text_emotions, tone_emotions = sample_emotions
        
        fused, confidence, metadata = fusion.fuse_emotions(
            text_emotions,
            tone_emotions,
            text_confidence=0.7,
            tone_confidence=0.6
        )
        
        # Check output
        assert isinstance(fused, dict)
        assert len(fused) == len(text_emotions)
        assert all(0 <= score <= 1 for score in fused.values())
        assert abs(sum(fused.values()) - 1.0) < 0.01  # Sum to 1
        
        # Check metadata
        assert 'alpha' in metadata
        assert 'beta' in metadata
        assert metadata['alpha'] + metadata['beta'] == pytest.approx(1.0)
    
    def test_detect_mixed_emotion(self, config):
        """Test mixed emotion detection."""
        fusion = EmotionFusion(config)
        
        # Disagreeing emotions with high confidence
        text_emotions = {'joy': 0.8, 'sadness': 0.1, 'anger': 0.05, 'fear': 0.03, 'disgust': 0.01, 'surprise': 0.005, 'neutral': 0.005}
        tone_emotions = {'sadness': 0.7, 'joy': 0.1, 'anger': 0.1, 'fear': 0.05, 'disgust': 0.03, 'surprise': 0.01, 'neutral': 0.01}
        
        mixed_info = fusion.detect_mixed_emotion(
            text_emotions,
            tone_emotions,
            text_confidence=0.8,
            tone_confidence=0.7
        )
        
        assert 'is_mixed' in mixed_info
        # Should detect disagreement
        assert mixed_info['is_mixed'] is True
    
    def test_temporal_smoothing(self, config, sample_emotions):
        """Test temporal smoothing."""
        fusion = EmotionFusion(config)
        text_emotions, _ = sample_emotions
        
        # Add multiple predictions
        for i in range(5):
            smoothed = fusion.apply_temporal_smoothing(text_emotions)
        
        # Smoothed should be dict with same keys
        assert isinstance(smoothed, dict)
        assert set(smoothed.keys()) == set(text_emotions.keys())
    
    def test_map_intensity(self, config):
        """Test intensity mapping."""
        fusion = EmotionFusion(config)
        
        # Test different score ranges
        assert fusion.map_intensity(0.3) == "Low"
        assert fusion.map_intensity(0.6) == "Medium"
        assert fusion.map_intensity(0.8) == "High"
    
    def test_get_action_trigger(self, config):
        """Test action trigger generation."""
        fusion = EmotionFusion(config)
        
        action = fusion.get_action_trigger('joy', 'High')
        
        assert 'led_color' in action
        assert 'quote_category' in action
        assert 'servo_gesture' in action
    
    def test_process_pipeline(self, config, sample_emotions):
        """Test complete fusion pipeline."""
        fusion = EmotionFusion(config)
        text_emotions, tone_emotions = sample_emotions
        
        result = fusion.process(
            text_emotions,
            tone_emotions,
            text_confidence=0.7,
            tone_confidence=0.6,
            transcription="Test transcription"
        )
        
        # Check result structure
        assert 'timestamp' in result
        assert 'emotion' in result
        assert 'intensity' in result
        assert 'confidence' in result
        assert 'breakdown' in result
        assert 'action_trigger' in result
        assert 'notes' in result
        
        # Check values
        assert result['emotion'] in text_emotions.keys()
        assert result['intensity'] in ['Low', 'Medium', 'High']
        assert 0 <= result['confidence'] <= 1


class TestJSONCompression:
    """Tests for JSON compression."""
    
    def test_compress_json_output(self):
        """Test JSON output compression."""
        # Sample full result
        result = {
            'timestamp': '2025-10-25T18:58:00.000000Z',
            'transcription': 'This is a test transcription for compression',
            'emotion': 'joy',
            'intensity': 'High',
            'confidence': 0.85,
            'breakdown': {
                'text_emotion': {'joy': 0.9, 'neutral': 0.05, 'surprise': 0.05},
                'tone_emotion': {'joy': 0.8, 'neutral': 0.1, 'surprise': 0.1},
                'fused_emotion': {'joy': 0.87, 'neutral': 0.07, 'surprise': 0.06}
            },
            'action_trigger': {
                'led_color': 'yellow',
                'quote_category': 'inspiring',
                'servo_gesture': 'wave'
            },
            'notes': {
                'fusion_alpha': 0.65,
                'mixed_emotion': False
            }
        }
        
        compressed = compress_json_output(result, max_size=1024)
        
        # Check compressed version
        assert 'emotion' in compressed
        assert 'intensity' in compressed
        assert 'conf' in compressed or 'confidence' in compressed
        assert 'action' in compressed
        
        # Check size
        import json
        size = len(json.dumps(compressed))
        assert size <= 1024

