"""
Unit tests for text_emotion module.
"""

import pytest
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from text_emotion import TextEmotionAnalyzer, SentimentAnalyzer


@pytest.fixture
def config():
    """Load test configuration."""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class TestTextEmotionAnalyzer:
    """Tests for TextEmotionAnalyzer class."""
    
    @pytest.fixture(scope="class")
    def analyzer(self, config):
        """Create analyzer instance (reuse for all tests)."""
        return TextEmotionAnalyzer(config)
    
    def test_initialization(self, analyzer, config):
        """Test analyzer initialization."""
        assert analyzer.model is not None
        assert analyzer.tokenizer is not None
        assert analyzer.emotions == config['nlp']['emotions']
    
    def test_analyze_happy_text(self, analyzer):
        """Test analysis of happy text."""
        text = "I am so happy and excited about this!"
        
        result = analyzer.analyze(text)
        
        assert 'emotions' in result
        assert 'top_emotion' in result
        assert 'confidence' in result
        
        # Should detect joy or positive emotion
        assert result['top_emotion'] in ['joy', 'surprise']
        assert result['confidence'] > 0.3
    
    def test_analyze_sad_text(self, analyzer):
        """Test analysis of sad text."""
        text = "I feel so sad and disappointed today."
        
        result = analyzer.analyze(text)
        
        # Should detect sadness
        assert result['top_emotion'] == 'sadness'
    
    def test_analyze_angry_text(self, analyzer):
        """Test analysis of angry text."""
        text = "This is absolutely infuriating and unacceptable!"
        
        result = analyzer.analyze(text)
        
        # Should detect anger
        assert result['top_emotion'] in ['anger', 'disgust']
    
    def test_analyze_neutral_text(self, analyzer):
        """Test analysis of neutral text."""
        text = "The meeting is scheduled for tomorrow at 3 PM."
        
        result = analyzer.analyze(text)
        
        # Should be neutral or low confidence
        assert result['top_emotion'] == 'neutral' or result['confidence'] < 0.6
    
    def test_empty_text(self, analyzer):
        """Test handling of empty text."""
        result = analyzer.analyze("")
        
        assert result['top_emotion'] == 'neutral'
        assert result['confidence'] == 0.0
        assert 'error' in result
    
    def test_short_text(self, analyzer):
        """Test handling of very short text."""
        result = analyzer.analyze("Hi")
        
        # Should return a result, possibly with low confidence
        assert 'top_emotion' in result
    
    def test_emotion_probabilities_sum(self, analyzer):
        """Test that emotion probabilities sum to ~1."""
        text = "This is a test."
        
        result = analyzer.analyze(text)
        
        total = sum(result['emotions'].values())
        assert abs(total - 1.0) < 0.01  # Should sum to ~1


class TestSentimentAnalyzer:
    """Tests for SentimentAnalyzer class."""
    
    def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        text = "This is great and wonderful!"
        
        result = SentimentAnalyzer.analyze_valence(text)
        
        assert 'positive' in result
        assert 'negative' in result
        assert 'neutral' in result
        assert result['positive'] > result['negative']
    
    def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        text = "This is terrible and awful!"
        
        result = SentimentAnalyzer.analyze_valence(text)
        
        assert result['negative'] > result['positive']
    
    def test_neutral_sentiment(self):
        """Test neutral sentiment."""
        text = "The sky is blue."
        
        result = SentimentAnalyzer.analyze_valence(text)
        
        # Should be mostly neutral
        assert result['neutral'] > 0.3

