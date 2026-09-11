import re
import logging
from typing import List, Dict, Any
try:
    from src.core.logger import setup_logging
except ImportError:
    from logger_config import setup_logging

logger = setup_logging("sentiment_tracker")

class SentimentTrackingEngine:
    """
    Analyzes customer salon reviews, feedback, and social sentiment to extract operational pain points.
    
    Working:
    - Tokenizes review text and scores sentiment based on luxury lexicon polarities (-1.0 to +1.0).
    - Categorizes feedback across four core operational pillars:
        - Service & Staff (wait times, attentiveness, queue management)
        - Pricing & Value (perceived value, price fairness)
        - Product Quality (craftsmanship, fabric integrity, defects)
        - Store Environment (cleanliness, salon ambiance, fitting room layout)
    - Automatically flags critical negative complaints (score <= -0.3) for concierge resolution.
    
    Why Required:
    - Luxury boutique retention depends on white-glove service standards; early detection of staff
      friction or quality defects prevents patron churn.
    """
    def __init__(self):
        """Initializes the engine with category-specific keywords."""
        self.category_keywords = {
            "Service & Staff": ["unhelpful", "staff", "wait", "slow", "line", "rude", "service", "queue"],
            "Pricing & Value": ["expensive", "price", "cost", "cheap", "overpriced", "value"],
            "Product Quality": ["broken", "tore", "defective", "quality", "amazing", "excellent", "bad"],
            "Store Environment": ["clean", "dirty", "layout", "parking", "smell", "organized"]
        }

    def _calculate_simple_sentiment(self, text: str) -> float:
        """
        Calculates a sentiment score between -1.0 (negative) and 1.0 (positive).
        
        Args:
            text (str): The review text to analyze.
            
        Returns:
            float: Computed sentiment score.
        """
        try:
            positive_words = {"great", "amazing", "excellent", "love", "helpful", "clean", "good", "fast"}
            negative_words = {"unhelpful", "slow", "rude", "expensive", "dirty", "bad", "broken", "wait"}

            tokens = re.findall(r'\b\w+\b', text.lower())
            pos_count = sum(1 for w in tokens if w in positive_words)
            neg_count = sum(1 for w in tokens if w in negative_words)

            total = pos_count + neg_count
            return (pos_count - neg_count) / total if total > 0 else 0.0
        except Exception as e:
            logger.error(f"Error calculating sentiment: {e}")
            return 0.0

    def process_reviews(self, raw_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Categorizes reviews and highlights critical complaints.
        
        Args:
            raw_reviews (List[Dict]): List of raw review dictionaries.
            
        Returns:
            Dict: Analysis summary including category breakdown and alerts.
        """
        try:
            category_scores = {cat: [] for cat in self.category_keywords}
            flagged_complaints = []

            for review in raw_reviews:
                text = review.get("review_text", "")
                score = self._calculate_simple_sentiment(text)

                for category, keywords in self.category_keywords.items():
                    if any(kw in text.lower() for kw in keywords):
                        category_scores[category].append(score)

                if score <= -0.3:
                    flagged_complaints.append({
                        "date": review.get("date"),
                        "text": text,
                        "score": round(score, 2)
                    })

            insights = {}
            for cat, scores in category_scores.items():
                insights[cat] = {
                    "average_sentiment": round(sum(scores) / len(scores), 2) if scores else 0.0,
                    "volume": len(scores)
                }

            logger.info(f"Processed {len(raw_reviews)} reviews.")
            return {
                "category_breakdown": insights,
                "critical_alerts": flagged_complaints
            }
        except Exception as e:
            logger.error(f"Error processing reviews: {e}")
            return {"category_breakdown": {}, "critical_alerts": []}
