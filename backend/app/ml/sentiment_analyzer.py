"""
Real NLP Sentiment Analysis using Transformers
Uses FinBERT (financial domain-specific BERT) for accurate sentiment on financial news.
"""
from typing import Dict, List
import logging
import os

logger = logging.getLogger(__name__)

class FinancialSentimentAnalyzer:
    """
    Real sentiment analysis using pre-trained FinBERT model.
    Falls back to rule-based if model unavailable.
    """

    def __init__(self):
        self.model = None
        self.attempted = False
        # Model will be initialized on first use to speed up startup

    def _initialize_model(self):
        """Load FinBERT model. Gracefully fallback if unavailable."""
        if self.model is not None or self.attempted:
            return
        self.attempted = True
        if os.getenv("VERTIGE_ENABLE_FINBERT") != "1":
            return

        try:
            from transformers import pipeline
            # FinBERT is specifically trained on financial text
            self.model = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=-1  # CPU (use 0 for GPU)
            )
            logger.info("FinBERT model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load FinBERT: {e}. Using fallback.")
            self.model = None

    def analyze(self, text: str) -> Dict[str, any]:
        """
        Analyze sentiment of financial text.
        """
        if self.model is None:
            self._initialize_model()

        if self.model:
            return self._analyze_with_model(text)
        else:
            return self._analyze_rule_based(text)

    def _analyze_with_model(self, text: str) -> Dict[str, any]:
        """Use FinBERT for analysis"""
        try:
            result = self.model(text[:512])[0]  # FinBERT has 512 token limit

            # Map FinBERT labels to our format
            label_map = {
                "positive": "Positive",
                "negative": "Negative",
                "neutral": "Neutral"
            }

            sentiment = label_map.get(result['label'].lower(), "Neutral")
            confidence = result['score']

            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "method": "finbert"
            }
        except Exception as e:
            logger.error(f"FinBERT analysis failed: {e}")
            return self._analyze_rule_based(text)

    def _analyze_rule_based(self, text: str) -> Dict[str, any]:
        """Fallback rule-based sentiment (simple keyword matching)"""
        text_lower = text.lower()

        positive_keywords = [
            "profit", "gain", "surge", "rally", "beat", "exceed",
            "growth", "strong", "recover", "upgrade", "bullish"
        ]
        negative_keywords = [
            "loss", "decline", "fall", "miss", "weak", "downgrade",
            "bearish", "concern", "risk", "plunge", "struggle"
        ]

        pos_count = sum(1 for word in positive_keywords if word in text_lower)
        neg_count = sum(1 for word in negative_keywords if word in text_lower)

        if pos_count > neg_count:
            sentiment = "Positive"
            confidence = min(0.6 + (pos_count * 0.05), 0.85)
        elif neg_count > pos_count:
            sentiment = "Negative"
            confidence = min(0.6 + (neg_count * 0.05), 0.85)
        else:
            sentiment = "Neutral"
            confidence = 0.5

        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "method": "rule-based"
        }

    def batch_analyze(self, texts: List[str]) -> List[Dict[str, any]]:
        """Analyze multiple texts efficiently"""
        return [self.analyze(text) for text in texts]

# Singleton instance
_analyzer = None

def get_sentiment_analyzer() -> FinancialSentimentAnalyzer:
    """Get or create sentiment analyzer singleton"""
    global _analyzer
    if _analyzer is None:
        _analyzer = FinancialSentimentAnalyzer()
    return _analyzer
