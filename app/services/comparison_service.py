from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter
import re
from ..database import get_database


class ComparisonService:
    STOP_WORDS = set([
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
        "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会",
        "着", "没有", "看", "好", "自己", "这", "他", "她", "它", "们",
        "那", "些", "什么", "怎么", "真的", "就是", "还是", "可以",
        "really", "the", "a", "an", "is", "are", "was", "were", "to",
        "of", "in", "for", "on", "with", "at", "by", "this", "that",
        "it", "its", "as", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "will", "would", "could", "should", "may",
        "might", "must", "shall", "can", "need", "dare", "ought", "used",
    ])

    @classmethod
    def extract_keywords(cls, text: str, top_n: int = 10) -> List[tuple]:
        words = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}", text.lower())
        filtered = [w for w in words if w not in cls.STOP_WORDS]
        counter = Counter(filtered)
        return counter.most_common(top_n)

    @classmethod
    async def compare_keywords(cls, keywords: List[str], days: int = 7) -> Dict:
        db = get_database()
        start_time = datetime.utcnow() - timedelta(days=days)

        items = []
        for keyword in keywords:
            escaped_keyword = re.escape(keyword)
            pattern = re.compile(escaped_keyword, re.IGNORECASE)

            or_cond = [
                {"title": {"$regex": pattern}},
                {"content": {"$regex": pattern}},
            ]
            match_stage = {"$match": {"$or": or_cond, "collected_at": {"$gte": start_time}}}

            p_cond = {"$cond": [{"$eq": ["$sentiment_label", "positive"]}, 1, 0]}
            n_cond = {"$cond": [{"$eq": ["$sentiment_label", "negative"]}, 1, 0]}
            e_cond = {"$cond": [{"$eq": ["$sentiment_label", "neutral"]}, 1, 0]}
            concat_expr = {"$concat": ["$title", " ", "$content"]}

            group_stage = {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "positive_count": {"$sum": p_cond},
                    "negative_count": {"$sum": n_cond},
                    "neutral_count": {"$sum": e_cond},
                    "avg_sentiment": {"$avg": "$sentiment_score"},
                    "contents": {"$push": concat_expr},
                }
            }

            pipeline = [match_stage, group_stage]

            result = await db.collected_data.aggregate(pipeline).to_list(length=1)
            if result:
                r = result[0]
                all_text = " ".join(r["contents"][:100])
                top_keywords = [
                    {"word": w, "count": c}
                    for w, c in cls.extract_keywords(all_text, top_n=15)
                ]

                total = r["total"] or 1
                items.append({
                    "keyword": keyword,
                    "total_mentions": r["total"],
                    "positive_count": r["positive_count"],
                    "negative_count": r["negative_count"],
                    "neutral_count": r["neutral_count"],
                    "avg_sentiment": round(r["avg_sentiment"] or 0, 4),
                    "sentiment_distribution": {
                        "positive": round(r["positive_count"] / total * 100, 2),
                        "negative": round(r["negative_count"] / total * 100, 2),
                        "neutral": round(r["neutral_count"] / total * 100, 2),
                    },
                    "top_keywords": top_keywords,
                })
            else:
                items.append({
                    "keyword": keyword,
                    "total_mentions": 0,
                    "positive_count": 0,
                    "negative_count": 0,
                    "neutral_count": 0,
                    "avg_sentiment": 0,
                    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                    "top_keywords": [],
                })

        return {
            "items": items,
            "generated_at": datetime.utcnow(),
        }
