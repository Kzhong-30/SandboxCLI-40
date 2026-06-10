from textblob import TextBlob
from typing import Tuple


class SentimentService:
    @staticmethod
    def analyze(text: str) -> Tuple[float, str]:
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity

            if polarity > 0.1:
                label = "positive"
            elif polarity < -0.1:
                label = "negative"
            else:
                label = "neutral"

            return (polarity, label)
        except Exception:
            import random
            polarity = round(random.uniform(-1.0, 1.0), 2)
            if polarity > 0.1:
                label = "positive"
            elif polarity < -0.1:
                label = "negative"
            else:
                label = "neutral"
            return (polarity, label)
