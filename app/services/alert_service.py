from datetime import datetime, timedelta
from bson import ObjectId
from .websocket_manager import manager
from ..database import get_database


class AlertService:
    @staticmethod
    async def check_sentiment_alert(
        monitor_id: ObjectId,
        sentiment_score: float,
        sentiment_threshold: float,
        data: dict
    ):
        if sentiment_score < sentiment_threshold:
            db = get_database()
            alert = {
                "monitor_id": monitor_id,
                "alert_type": "sentiment_threshold",
                "message": f"检测到负面舆情，情感得分 {sentiment_score:.2f} 低于阈值 {sentiment_threshold:.2f}",
                "details": {
                    "sentiment_score": sentiment_score,
                    "threshold": sentiment_threshold,
                    "data_title": data.get("title"),
                    "data_content": data.get("content", "")[:200],
                    "source_type": data.get("source_type"),
                    "url": data.get("url"),
                },
                "is_read": False,
                "created_at": datetime.utcnow(),
            }
            result = await db.alerts.insert_one(alert)
            alert["_id"] = str(result.inserted_id)
            alert["monitor_id"] = str(alert["monitor_id"])

            await manager.send_alert(str(monitor_id), {
                "type": "ALERT",
                "data": alert,
                "timestamp": datetime.utcnow().isoformat(),
            })
            return alert
        return None

    @staticmethod
    async def check_spike_alert(
        monitor_id: ObjectId,
        spike_ratio: float
    ):
        db = get_database()
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        two_hours_ago = now - timedelta(hours=2)

        current_negative = await db.collected_data.count_documents({
            "monitor_id": monitor_id,
            "sentiment_label": "negative",
            "collected_at": {"$gte": one_hour_ago, "$lt": now},
        })

        previous_negative = await db.collected_data.count_documents({
            "monitor_id": monitor_id,
            "sentiment_label": "negative",
            "collected_at": {"$gte": two_hours_ago, "$lt": one_hour_ago},
        })

        if previous_negative > 0 and current_negative > 0:
            ratio = current_negative / previous_negative
            if ratio >= spike_ratio:
                alert = {
                    "monitor_id": monitor_id,
                    "alert_type": "spike",
                    "message": f"负面舆情数量突增！当前小时 {current_negative} 条，前一小时 {previous_negative} 条，增长 {ratio:.1f} 倍",
                    "details": {
                        "current_count": current_negative,
                        "previous_count": previous_negative,
                        "ratio": ratio,
                        "threshold": spike_ratio,
                    },
                    "is_read": False,
                    "created_at": datetime.utcnow(),
                }
                result = await db.alerts.insert_one(alert)
                alert["_id"] = str(result.inserted_id)
                alert["monitor_id"] = str(alert["monitor_id"])

                await manager.send_alert(str(monitor_id), {
                    "type": "ALERT",
                    "data": alert,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                return alert

        return None
