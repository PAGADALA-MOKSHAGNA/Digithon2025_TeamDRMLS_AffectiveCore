"""
Text-based emotion analysis using DistilRoBERTa transformer model.
Returns emotion probabilities and confidence scores.
"""

import logging
import numpy as np
from typing import Dict, List, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)


class TextEmotionAnalyzer:
    """
    NLP-based emotion classifier using DistilRoBERTa.
    Model: j-hartmann/emotion-english-distilroberta-base
    """
    
    def __init__(self, config: dict):
        """
        Initialize the text emotion analyzer with DistilRoBERTa model.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.model_name = config['nlp']['model']
        self.device = config['nlp']['device']
        self.min_confidence = config['nlp']['min_confidence']
        self.emotions = config['nlp']['emotions']
        
        self.tokenizer = None
        self.model = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the DistilRoBERTa emotion classification model."""
        try:
            logger.info(f"Loading text emotion model: {self.model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            
            # Move to appropriate device
            if self.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.to("cuda")
                logger.info("Model loaded on CUDA")
            else:
                self.model = self.model.to("cpu")
                logger.info("Model loaded on CPU")
            
            self.model.eval()
            
            logger.info("Text emotion model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load text emotion model: {e}")
            raise
    
    def analyze(self, text: str) -> Dict[str, any]:
        """
        Analyze emotion from text using DistilRoBERTa.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing:
                - emotions: Dict of emotion probabilities
                - top_emotion: Emotion with highest probability
                - confidence: Confidence score (0-1)
                - is_confident: Whether confidence exceeds threshold
                - text_length: Length of analyzed text
        """
        # Validate input
        if not text or len(text.strip()) == 0:
            return self._empty_result("Empty text")
        
        text = text.strip()
        
        # Check for very short text
        if len(text) < 3:
            return self._empty_result("Text too short")
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Move to device
            if self.device == "cuda" and torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            
            # Convert to probabilities
            probs = torch.softmax(logits, dim=-1)
            probs_np = probs.cpu().numpy()[0]
            
            # Map to emotion labels using the model's id2label mapping
            # The model has its own label order, use it directly
            emotion_scores = {
                self.model.config.id2label[i]: float(probs_np[i])
                for i in range(len(probs_np))
            }
            
            # Get top emotion
            top_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[top_emotion]
            
            # Check confidence threshold
            is_confident = confidence >= self.min_confidence
            
            logger.debug(
                f"Text emotion: {top_emotion} "
                f"(conf: {confidence:.3f}, "
                f"confident: {is_confident})"
            )
            
            return {
                'emotions': emotion_scores,
                'top_emotion': top_emotion,
                'confidence': confidence,
                'is_confident': is_confident,
                'text_length': len(text),
                'analyzed_text': text[:100]  # First 100 chars for debugging
            }
            
        except Exception as e:
            logger.error(f"Text emotion analysis failed: {e}")
            return self._empty_result(f"Analysis error: {str(e)}")
    
    def _empty_result(self, reason: str) -> Dict[str, any]:
        """
        Return empty/neutral result when analysis cannot proceed.
        
        Args:
            reason: Reason for empty result
            
        Returns:
            Neutral emotion result dictionary
        """
        logger.warning(f"Returning empty result: {reason}")
        
        # Return neutral with low confidence
        emotion_scores = {emotion: 0.0 for emotion in self.emotions}
        emotion_scores['neutral'] = 1.0
        
        return {
            'emotions': emotion_scores,
            'top_emotion': 'neutral',
            'confidence': 0.0,
            'is_confident': False,
            'text_length': 0,
            'error': reason
        }
    
    def batch_analyze(self, texts: List[str]) -> List[Dict[str, any]]:
        """
        Analyze multiple texts in batch for efficiency.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of emotion analysis results
        """
        results = []
        
        # Filter empty texts
        valid_texts = [(i, text) for i, text in enumerate(texts) if text and len(text.strip()) > 0]
        
        if not valid_texts:
            return [self._empty_result("Empty text") for _ in texts]
        
        try:
            # Prepare batch
            indices, text_list = zip(*valid_texts)
            
            inputs = self.tokenizer(
                list(text_list),
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            # Move to device
            if self.device == "cuda" and torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
            
            # Convert to probabilities
            probs = torch.softmax(logits, dim=-1)
            probs_np = probs.cpu().numpy()
            
            # Process each result
            batch_results = [None] * len(texts)
            
            for idx, (orig_idx, text) in enumerate(valid_texts):
                emotion_scores = {
                    emotion: float(probs_np[idx][i]) 
                    for i, emotion in enumerate(self.emotions)
                }
                
                top_emotion = max(emotion_scores, key=emotion_scores.get)
                confidence = emotion_scores[top_emotion]
                is_confident = confidence >= self.min_confidence
                
                batch_results[orig_idx] = {
                    'emotions': emotion_scores,
                    'top_emotion': top_emotion,
                    'confidence': confidence,
                    'is_confident': is_confident,
                    'text_length': len(text),
                    'analyzed_text': text[:100]
                }
            
            # Fill in empty results for invalid texts
            for i, result in enumerate(batch_results):
                if result is None:
                    batch_results[i] = self._empty_result("Empty text")
            
            return batch_results
            
        except Exception as e:
            logger.error(f"Batch text emotion analysis failed: {e}")
            return [self._empty_result(f"Batch error: {str(e)}") for _ in texts]
    
    def get_emotion_intensity(self, emotion_scores: Dict[str, float]) -> str:
        """
        Calculate emotion intensity based on scores.
        This is a simple version; the main intensity calculation is in fusion.py
        
        Args:
            emotion_scores: Dictionary of emotion probabilities
            
        Returns:
            Intensity level: "Low", "Medium", or "High"
        """
        max_score = max(emotion_scores.values())
        
        if max_score < 0.5:
            return "Low"
        elif max_score < 0.75:
            return "Medium"
        else:
            return "High"
    
    def detect_sarcasm_or_mixed(
        self, 
        text: str, 
        emotion_scores: Dict[str, float]
    ) -> Dict[str, any]:
        """
        Detect potential sarcasm or mixed emotions using heuristics.
        
        Args:
            text: Input text
            emotion_scores: Emotion probability distribution
            
        Returns:
            Dictionary with sarcasm/mixed emotion flags and reasoning
        """
        # Get top 2 emotions
        sorted_emotions = sorted(
            emotion_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        top1_emotion, top1_score = sorted_emotions[0]
        top2_emotion, top2_score = sorted_emotions[1] if len(sorted_emotions) > 1 else ("", 0.0)
        
        # Check for mixed emotions (top 2 are close)
        is_mixed = (top1_score - top2_score) < 0.15 and top2_score > 0.25
        
        # Sarcasm indicators (simple heuristics)
        sarcasm_indicators = [
            'great',
            'wonderful',
            'perfect',
            'exactly',
            'just what i',
            'oh yeah',
            'sure',
            'right',
        ]
        
        text_lower = text.lower()
        has_sarcasm_words = any(indicator in text_lower for indicator in sarcasm_indicators)
        
        # Sarcasm often pairs positive words with negative context
        positive_emotions = ['joy', 'surprise']
        has_positive_word = any(word in text_lower for word in ['great', 'wonderful', 'perfect', 'amazing'])
        
        # If high joy score but sarcasm indicators present
        is_sarcasm = (
            top1_emotion in positive_emotions and 
            has_sarcasm_words and 
            has_positive_word and
            '!' not in text  # Genuine excitement often has exclamation
        )
        
        result = {
            'is_mixed': is_mixed,
            'is_sarcasm': is_sarcasm,
            'top_emotions': [top1_emotion, top2_emotion] if is_mixed else [top1_emotion],
            'confidence': top1_score,
            'note': ""
        }
        
        if is_sarcasm:
            result['note'] = "Potential sarcasm detected - manual review recommended"
        elif is_mixed:
            result['note'] = f"Mixed emotions: {top1_emotion} and {top2_emotion}"
        
        return result


class SentimentAnalyzer:
    """
    Additional sentiment analysis for detecting valence (positive/negative).
    Can be used to augment emotion detection.
    """
    
    @staticmethod
    def analyze_valence(text: str) -> Dict[str, float]:
        """
        Analyze sentiment valence (positive/negative/neutral).
        Simple keyword-based approach for offline operation.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with valence scores
        """
        text_lower = text.lower()
        
        # Simple keyword lists
        positive_words = [
            'good', 'great', 'happy', 'love', 'excellent', 'wonderful',
            'amazing', 'fantastic', 'joy', 'excited', 'pleased', 'glad'
        ]
        
        negative_words = [
            'bad', 'terrible', 'hate', 'awful', 'horrible', 'worst',
            'sad', 'angry', 'upset', 'disappointed', 'frustrated', 'annoyed'
        ]
        
        # Count occurrences
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        total = pos_count + neg_count
        
        if total == 0:
            return {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
        
        # Calculate scores
        pos_score = pos_count / total if total > 0 else 0
        neg_score = neg_count / total if total > 0 else 0
        neutral_score = 1.0 - (pos_score + neg_score)
        
        return {
            'positive': pos_score,
            'negative': neg_score,
            'neutral': neutral_score
        }

