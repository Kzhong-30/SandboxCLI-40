from datetime import datetime, timedelta
from typing import List, Dict
from bson import ObjectId
from ..database import get_database


class TrendService:
    @staticmethod
    async def get_trends(
        monitor_id: ObjectId,
        time_granularity: str = "hour",
        hours: int = 24
    ) -> List[Dict]:
        db = get_database()

        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours)

        if time_granularity == "day":
            start_time = now - timedelta(days=hours if hours < 365 else 30)

        match_stage = {
            "$match": {
                "monitor_id": monitor_id,
                "collected_at": {"$gte": start_time, "$lte": now}
            }
        }

        group_id = {
            "year": {"$year": "$collected_at"},
            "month": {"$month": "$collected_at"},
        }
        if time_granularity == "hour":
            group_id["day"] = {"$dayOfMonth": "$collected_at"}
            group_id["hour"] = {"$hour": "$collected_at"}

        pos_cond = {"$cond": [{"$eq": ["$sentiment_label", "positive"]}, 1, 0]}
        neg_cond = {"$cond": [{"$eq": ["$sentiment_label", "negative"]}, 1, 0]}
        neu_cond = {"$cond": [{"$eq": ["$sentiment_label", "neutral"]}, 1, 0]}

        group_stage = {
            "$group": {
                "_id": group_id,
                "count": {"$sum": 1},
                "positive_count": {"$sum": pos_cond},
                "negative_count": {"$sum": neg_cond},
                "neutral_count": {"$sum": neu_cond},
                "avg_sentiment": {"$avg": "$sentiment_score"},
            }
        }

        sort_stage = {"$sort": {"_id": 1}}

        pipeline = [match_stage, group_stage, sort_stage]

        results = await db.collected_data.aggregate(pipeline).to_list(length=None)

        data_points = []
        for r in results:
            _id = r["_id"]
            if time_granularity == "hour":
                ts = datetime(
                    _id["year"], _id["month"], _id["day"], _id["hour"], 0, 0
                )
            else:
                ts = datetime(_id["year"], _id["month"], 1, 0, 0, 0)

            data_points.append({
                "timestamp": ts,
                "count": r["count"],
                "positive_count": r["positive_count"],
                "negative_count": r["negative_count"],
                "neutral_count": r["neutral_count"],
                "avg_sentiment": round(r["avg_sentiment"] or 0, 4),
            })

        return data_points, start_time, now
