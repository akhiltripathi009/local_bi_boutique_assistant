import re
from typing import List, Dict, Any


class SentimentTrackingEngine:
    def __init__(self):
        # Lexicon-based keyword mapping for category assignment
        self.category_keywords = {
            "Service & Staff": ["unhelpful", "staff", "wait", "slow", "line", "rude", "service", "queue"],
            "Pricing & Value": ["expensive", "price", "cost", "cheap", "overpriced", "value"],
            "Product Quality": ["broken", "tore", "defective", "quality", "amazing", "excellent", "bad"],
            "Store Environment": ["clean", "dirty", "layout", "parking", "smell", "organized"]
        }

    def _calculate_simple_sentiment(self, text: str) -> float:
        """
        A lightweight rule engine calculating sentiment score between -1.0 and 1.0.
        In production, swap this with a HuggingFace Transformer model pipeline.
        """
        positive_words = {"great", "amazing", "excellent", "love", "helpful", "clean", "good", "fast"}
        negative_words = {"unhelpful", "slow", "rude", "expensive", "dirty", "bad", "broken", "wait"}

        tokens = re.findall(r'\b\w+\b', text.lower())
        pos_count = sum(1 for w in tokens if w in positive_words)
        neg_count = sum(1 for w in tokens if w in negative_words)

        total = pos_count + neg_count
        if total == 0:
            return 0.0
        return (pos_count - neg_count) / total

    def process_reviews(self, raw_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorizes reviews and highlights structural problems."""
        category_scores = {cat: [] for cat in self.category_keywords}
        flagged_complaints = []

        for review in raw_reviews:
            text = review["review_text"]
            score = self._calculate_simple_sentiment(text)

            # Map review to operational categories based on keywords
            assigned = False
            for category, keywords in self.category_keywords.items():
                if any(kw in text.lower() for kw in keywords):
                    category_scores[category].append(score)
                    assigned = True

            # If a review is highly negative, flag it immediately
            if score <= -0.3:
                flagged_complaints.append({
                    "date": review.get("date"),
                    "text": text,
                    "score": round(score, 2)
                })

        # Aggregate stats
        insights = {}
        for cat, scores in category_scores.items():
            insights[cat] = {
                "average_sentiment": round(sum(scores) / len(scores), 2) if scores else 0.0,
                "volume": len(scores)
            }

        return {
            "category_breakdown": insights,
            "critical_alerts": flagged_complaints
        }
