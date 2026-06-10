from typing import Tuple
import re

try:
    from snownlp import SnowNLP
    HAS_SNOWNLP = True
except ImportError:
    HAS_SNOWNLP = False


class SentimentService:
    @staticmethod
    def _contains_chinese(text: str) -> bool:
        return bool(re.search(r"[\u4e00-\u9fff]", text))

    @staticmethod
    def analyze(text: str) -> Tuple[float, str]:
        if not text:
            return (0.0, "neutral")

        polarity = 0.0

        if HAS_SNOWNLP and SentimentService._contains_chinese(text):
            try:
                s = SnowNLP(text)
                snow_score = s.sentiments
                polarity = (snow_score - 0.5) * 2
            except Exception:
                polarity = SentimentService._rule_based_zh(text)
        else:
            try:
                from textblob import TextBlob
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
            except Exception:
                polarity = SentimentService._rule_based_fallback(text)

        polarity = max(-1.0, min(1.0, polarity))

        if polarity > 0.15:
            label = "positive"
        elif polarity < -0.15:
            label = "negative"
        else:
            label = "neutral"

        return (round(polarity, 4), label)

    @staticmethod
    def _rule_based_zh(text: str) -> float:
        positive_words = [
            "好", "棒", "优秀", "推荐", "喜欢", "赞", "支持", "满意", "出色",
            "太棒了", "强烈推荐", "真的很好", "不错", "完美", "惊喜", "实用",
            "优质", "稳定", "流畅", "超值", "划算", "值得", "好评",
            "great", "good", "excellent", "amazing", "love", "best", "perfect",
        ]
        negative_words = [
            "差", "烂", "糟糕", "失望", "垃圾", "不好", "投诉", "退款",
            "差劲", "吐槽", "假的", "骗", "坑", "恶心", "难用", "卡顿",
            "崩溃", "失败", "问题", "故障", "退货", "差评", "太差",
            "terrible", "bad", "awful", "hate", "worst", "disappointing", "sucks",
        ]

        score = 0.0
        total_hits = 0

        for w in positive_words:
            count = text.count(w)
            if count > 0:
                score += 0.15 * count
                total_hits += count

        for w in negative_words:
            count = text.count(w)
            if count > 0:
                score -= 0.15 * count
                total_hits += count

        if total_hits > 0:
            score = score / (1 + total_hits * 0.2)

        return max(-1.0, min(1.0, score))

    @staticmethod
    def _rule_based_fallback(text: str) -> float:
        text_lower = text.lower()
        positive_words = [
            "good", "great", "excellent", "amazing", "wonderful", "perfect",
            "love", "best", "nice", "awesome", "fantastic", "superb", "recommend",
            "happy", "delighted", "satisfied", "impressive", "outstanding",
            "好", "棒", "优", "赞", "喜欢", "满意", "推荐",
        ]
        negative_words = [
            "bad", "terrible", "awful", "horrible", "worst", "hate", "disappointing",
            "sucks", "poor", "broken", "fail", "failed", "problem", "issue",
            "complaint", "refund", "dislike", "angry", "frustrating",
            "差", "烂", "坏", "失望", "糟", "垃圾", "投诉", "难用",
        ]

        pos = sum(text_lower.count(w) for w in positive_words)
        neg = sum(text_lower.count(w) for w in negative_words)
        total = pos + neg

        if total == 0:
            return 0.0
        return (pos - neg) / total
