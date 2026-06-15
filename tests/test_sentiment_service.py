import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sentiment_service import SentimentService


class TestSentimentService:
    def test_empty_text(self):
        score, label = SentimentService.analyze("")
        assert score == 0.0
        assert label == "neutral"

    def test_score_range(self):
        cases = ["good", "bad", "hello world", "a" * 500, "!@#$%"]
        for text in cases:
            score, label = SentimentService.analyze(text)
            assert -1.0 <= score <= 1.0
            assert label in ("positive", "negative", "neutral")

    def test_english_positive(self):
        score, label = SentimentService.analyze("excellent product, highly recommend, amazing quality")
        assert score > 0.0
        assert label in ("positive", "neutral")

    def test_english_negative(self):
        score, label = SentimentService.analyze("terrible awful worst disappointing product ever")
        assert score < 0.0
        assert label in ("negative", "neutral")

    def test_contains_chinese(self):
        assert SentimentService._contains_chinese("你好 world") is True
        assert SentimentService._contains_chinese("hello") is False

    def test_rule_fallback(self):
        s1 = SentimentService._rule_based_fallback("good excellent")
        assert s1 > 0
        s2 = SentimentService._rule_based_fallback("bad terrible")
        assert s2 < 0
        s3 = SentimentService._rule_based_fallback("")
        assert s3 == 0.0

    def test_return_type(self):
        result = SentimentService.analyze("test")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], str)

    def test_whitespace_text(self):
        score, label = SentimentService.analyze("   ")
        assert isinstance(score, float)
        assert -1.0 <= score <= 1.0

    def test_very_long_text(self):
        text = "good product. " * 200
        score, label = SentimentService.analyze(text)
        assert -1.0 <= score <= 1.0
        assert isinstance(label, str)
