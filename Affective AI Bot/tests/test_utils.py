"""
Unit tests for utils module.
"""

import pytest
import numpy as np
import yaml
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import AudioProcessor, AudioValidator, estimate_speech_rate


@pytest.fixture
def config():
    """Load test configuration."""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@pytest.fixture
def sample_audio():
    """Generate sample audio signal."""
    duration = 2.0  # seconds
    sample_rate = 16000
    frequency = 440  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    return audio.astype(np.float32), sample_rate


class TestAudioProcessor:
    """Tests for AudioProcessor class."""
    
    def test_initialization(self, config):
        """Test AudioProcessor initialization."""
        processor = AudioProcessor(config)
        
        assert processor.sample_rate == config['asr']['sample_rate']
        assert processor.vad_enabled == config['vad']['enabled']
    
    def test_normalize_audio(self, config, sample_audio):
        """Test audio normalization."""
        audio, sr = sample_audio
        processor = AudioProcessor(config)
        
        normalized = processor.normalize_audio(audio, target_dbfs=-20.0)
        
        assert normalized.shape == audio.shape
        assert normalized.dtype == np.float32
        assert np.abs(normalized).max() <= 1.0
    
    def test_noise_reduction(self, config, sample_audio):
        """Test noise reduction."""
        audio, sr = sample_audio
        
        # Add noise
        noise = np.random.normal(0, 0.05, audio.shape)
        noisy_audio = audio + noise
        
        processor = AudioProcessor(config)
        reduced = processor.reduce_noise(noisy_audio)
        
        assert reduced.shape == noisy_audio.shape
    
    def test_preprocess_audio(self, config, sample_audio):
        """Test full preprocessing pipeline."""
        audio, sr = sample_audio
        processor = AudioProcessor(config)
        
        preprocessed = processor.preprocess_audio(audio)
        
        assert preprocessed.shape == audio.shape
        assert np.isfinite(preprocessed).all()
    
    def test_chunk_audio(self, config, sample_audio):
        """Test audio chunking."""
        audio, sr = sample_audio
        processor = AudioProcessor(config)
        
        chunk_duration = 0.5
        overlap = 0.1
        
        chunks = list(processor.chunk_audio(audio, chunk_duration, overlap))
        
        assert len(chunks) > 0
        
        for chunk, start_time, end_time in chunks:
            assert len(chunk) == int(chunk_duration * sr)
            assert end_time > start_time


class TestAudioValidator:
    """Tests for AudioValidator class."""
    
    def test_valid_audio(self, sample_audio):
        """Test valid audio detection."""
        audio, sr = sample_audio
        
        is_valid, reason = AudioValidator.is_valid_audio(audio)
        
        assert is_valid is True
        assert reason == "Valid"
    
    def test_empty_audio(self):
        """Test empty audio detection."""
        audio = np.array([])
        
        is_valid, reason = AudioValidator.is_valid_audio(audio)
        
        assert is_valid is False
        assert "Empty" in reason
    
    def test_silent_audio(self):
        """Test silent audio detection."""
        audio = np.zeros(16000)
        
        is_valid, reason = AudioValidator.is_valid_audio(audio)
        
        assert is_valid is False
        assert "Silent" in reason.lower() or "zeros" in reason.lower()
    
    def test_clipping_detection(self):
        """Test audio clipping detection."""
        audio = np.ones(16000) * 0.995  # Near clipping
        
        is_valid, reason = AudioValidator.is_valid_audio(audio)
        
        # Should still be valid (not quite clipping)
        assert is_valid is True


class TestSpeechRate:
    """Tests for speech rate estimation."""
    
    def test_speech_rate_estimation(self, sample_audio):
        """Test speech rate estimation."""
        audio, sr = sample_audio
        
        rate = estimate_speech_rate(audio, sr)
        
        assert rate > 0
        assert rate < 20  # Reasonable upper bound
    
    def test_speech_rate_silent(self):
        """Test speech rate on silent audio."""
        audio = np.random.normal(0, 0.001, 16000)  # Very quiet
        sr = 16000
        
        rate = estimate_speech_rate(audio, sr)
        
        # Should return low rate or default
        assert rate >= 0

