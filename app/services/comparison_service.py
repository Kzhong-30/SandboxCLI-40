from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import Counter
from io import BytesIO
import base64
import re
from ..database import get_database

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

try:
    from wordcloud import WordCloud
    HAS_WORDCLOUD = True
except ImportError:
    HAS_WORDCLOUD = False


class ComparisonService:
    STOP_WORDS = set([
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都",
        "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会",
        "着", "没有", "看", "好", "自己", "这", "他", "她", "它", "们",
        "那", "些", "什么", "怎么", "真的", "就是", "还是", "可以",
        "我们", "你们", "他们", "大家", "自己", "这个", "那个", "这么",
        "那么", "这样", "那样", "但是", "因为", "所以", "如果", "虽然",
        "然后", "之后", "之前", "现在", "时候", "今天", "昨天", "明天",
        "已经", "还有", "一点", "一些", "一下", "一起", "一直", "其实",
        "really", "the", "a", "an", "is", "are", "was", "were", "to",
        "of", "in", "for", "on", "with", "at", "by", "this", "that",
        "it", "its", "as", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "will", "would", "could", "should", "may",
        "might", "must", "shall", "can", "need", "dare", "ought", "used",
        "and", "or", "but", "if", "then", "else", "when", "where", "how",
        "all", "any", "each", "every", "both", "few", "more", "most",
        "other", "some", "such", "no", "nor", "not", "only", "own", "same",
        "so", "than", "too", "very", "just", "about", "also", "into",
        "through", "during", "before", "after", "above", "below", "from",
        "up", "down", "out", "off", "over", "under", "again", "further",
        "once", "here", "there", "why", "what", "which", "who", "whom",
    ])

    @classmethod
    def _chinese_tokenize(cls, text: str) -> List[str]:
        if HAS_JIEBA:
            tokens = list(jieba.cut(text, cut_all=False))
        else:
            tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}", text.lower())
        return [
            t.strip() for t in tokens
            if t.strip()
            and len(t.strip()) >= 2
            and t.strip() not in cls.STOP_WORDS
            and not t.strip().isdigit()
        ]

    @classmethod
    def extract_keywords(cls, text: str, top_n: int = 10) -> List[tuple]:
        words = cls._chinese_tokenize(text)
        counter = Counter(words)
        return counter.most_common(top_n)

    @classmethod
    def generate_wordcloud_base64(
        cls,
        word_freq: Dict[str, int],
        width: int = 800,
        height: int = 400,
        font_path: Optional[str] = None,
    ) -> Optional[str]:
        if not HAS_WORDCLOUD or not word_freq:
            return None

        if font_path is None:
            font_path = "/System/Library/Fonts/PingFang.ttc"

        try:
            wc = WordCloud(
                font_path=font_path,
                width=width,
                height=height,
                background_color="white",
                colormap="viridis",
                max_words=100,
                prefer_horizontal=0.9,
                collocations=False,
                mode="RGB",
            )
            wc.generate_from_frequencies(word_freq)

            image = wc.to_image()
            buffer = BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            png_bytes = buffer.getvalue()
            return base64.b64encode(png_bytes).decode("utf-8")
        except Exception:
            fallback_fonts = [
                "/System/Library/Fonts/Supplemental/Songti.ttc",
                "/System/Library/Fonts/Supplemental/STHeiti Light.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
            ]
            for fp in fallback_fonts:
                try:
                    wc = WordCloud(
                        font_path=fp,
                        width=width,
                        height=height,
                        background_color="white",
                        max_words=100,
                    )
                    wc.generate_from_frequencies(word_freq)
                    image = wc.to_image()
                    buffer = BytesIO()
                    image.save(buffer, format="PNG")
                    return base64.b64encode(buffer.getvalue()).decode("utf-8")
                except Exception:
                    continue
            try:
                wc = WordCloud(
                    width=width,
                    height=height,
                    background_color="white",
                    max_words=100,
                )
                wc.generate_from_frequencies(word_freq)
                image = wc.to_image()
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode("utf-8")
            except Exception:
                return None

    @classmethod
    async def compare_keywords(
        cls,
        keywords: List[str],
        days: int = 7,
        generate_image: bool = True,
    ) -> Dict:
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
                all_text = " ".join(r["contents"][:200])
                extracted = cls.extract_keywords(all_text, top_n=50)
                top_keywords = [
                    {"word": w, "count": c}
                    for w, c in extracted[:15]
                ]

                word_freq = {w: c for w, c in extracted}
                wordcloud_image = None
                if generate_image:
                    wordcloud_image = cls.generate_wordcloud_base64(word_freq)

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
                    "wordcloud_image_base64": wordcloud_image,
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
                    "wordcloud_image_base64": None,
                })

        return {
            "items": items,
            "generated_at": datetime.utcnow(),
        }
