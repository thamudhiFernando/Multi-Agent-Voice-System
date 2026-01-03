from typing import Optional, Dict, Tuple

from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from app.core.config import settings
from app.core.logs import get_logger

logger = get_logger()

class SentimentService:
    """
    Service for analyzing sentiment in customer messages.
    Combines VADER and TextBlob for accurate sentiment detection.
    """

    def __init__(self):
        """Initialize sentiment analyzers"""
        self.vader_analyzer = SentimentIntensityAnalyzer()
        logger.info("Sentiment service initialized")

    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """
        Analyze sentiment of text using both VADER and TextBlob.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment scores and classification
        """
        if not text:
            return {
                "label": "neutral",
                "score": 0.0,
                "compound": 0.0,
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0
            }

        # VADER analysis (better for social media and short texts)
        vader_scores = self.vader_analyzer.polarity_scores(text)

        # TextBlob analysis (good for longer texts)
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity

        # Combine scores (weighted average, favor VADER for customer service)
        combined_score = (vader_scores['compound'] * 0.7) + (textblob_polarity * 0.3)

        # Classify sentiment
        label = self._classify_sentiment(combined_score)

        result = {
            "label": label,
            "score": round(combined_score, 3),
            "compound": round(vader_scores['compound'], 3),
            "positive": round(vader_scores['pos'], 3),
            "negative": round(vader_scores['neg'], 3),
            "neutral": round(vader_scores['neu'], 3),
            "subjectivity": round(textblob_subjectivity, 3),
            "is_negative": combined_score < settings.NEGATIVE_SENTIMENT_THRESHOLD
        }

        logger.debug(f"Sentiment analysis: {label} ({combined_score})")
        return result

    def _classify_sentiment(self, score: float) -> str:
        """
        Classify sentiment score into label.

        Args:
            score: Sentiment score (-1 to 1)

        Returns:
            Sentiment label (positive, negative, neutral)
        """
        if score >= 0.05:
            return "positive"
        elif score <= -0.05:
            return "negative"
        else:
            return "neutral"

    def detect_urgency(self, text: str) -> Tuple[bool, float]:
        """
        Detect if message indicates urgency or emergency.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (is_urgent, urgency_score)
        """
        urgent_keywords = [
            'urgent', 'emergency', 'immediately', 'asap', 'critical',
            'broken', 'not working', 'help', 'problem', 'issue',
            'can\'t', 'cannot', 'won\'t', 'doesn\'t work', 'failed',
            'error', 'crash', 'lost', 'missing'
        ]

        text_lower = text.lower()
        urgency_score = 0.0

        # Check for urgent keywords
        for keyword in urgent_keywords:
            if keyword in text_lower:
                urgency_score += 0.2

        # Check for exclamation marks
        exclamation_count = text.count('!')
        urgency_score += min(exclamation_count * 0.1, 0.3)

        # Check for all caps words (indicates shouting/urgency)
        words = text.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 2]
        urgency_score += min(len(caps_words) * 0.1, 0.3)

        # Check sentiment (very negative often indicates urgency)
        sentiment = self.analyze_sentiment(text)
        if sentiment['is_negative']:
            urgency_score += abs(sentiment['score']) * 0.3

        # Normalize score to 0-1 range
        urgency_score = min(urgency_score, 1.0)

        is_urgent = urgency_score >= 0.5

        logger.debug(f"Urgency detection: {is_urgent} (score: {urgency_score})")
        return is_urgent, round(urgency_score, 3)

    def detect_frustration(self, text: str) -> bool:
        """
        Detect if customer is frustrated or angry.

        Args:
            text: Text to analyze

        Returns:
            True if frustration detected
        """
        frustration_keywords = [
            'frustrated', 'angry', 'terrible', 'awful', 'worst',
            'ridiculous', 'unacceptable', 'disappointed', 'waste',
            'useless', 'horrible', 'pathetic', 'disgusting'
        ]

        text_lower = text.lower()

        # Check for frustration keywords
        has_frustration_words = any(keyword in text_lower for keyword in frustration_keywords)

        # Check sentiment
        sentiment = self.analyze_sentiment(text)
        is_very_negative = sentiment['score'] < -0.5

        frustrated = has_frustration_words or is_very_negative

        if frustrated:
            logger.warning(f"Frustration detected in message")

        return frustrated

    def analyze_customer_emotion(self, text: str) -> Dict[str, any]:
        """
        Comprehensive emotion analysis for customer service.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with all emotion metrics
        """
        sentiment = self.analyze_sentiment(text)
        is_urgent, urgency_score = self.detect_urgency(text)
        is_frustrated = self.detect_frustration(text)

        return {
            **sentiment,
            "is_urgent": is_urgent,
            "urgency_score": urgency_score,
            "is_frustrated": is_frustrated,
            "requires_human_escalation": is_frustrated or (is_urgent and sentiment['is_negative'])
        }


# Global sentiment service instance
_sentiment_service: Optional[SentimentService] = None


def get_sentiment_service() -> SentimentService:
    """
    Get or create the global sentiment service instance.

    Returns:
        SentimentService: Global sentiment service instance
    """
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service
