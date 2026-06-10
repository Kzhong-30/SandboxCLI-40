import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from bson import ObjectId
from .database import get_database
from .services.crawler_service import CrawlerService
from .services.sentiment_service import SentimentService
from .services.alert_service import AlertService


scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def scheduled_crawl():
    db = get_database()
    if not db:
        return

    active_monitors = await db.monitors.find({"is_active": True}).to_list(length=None)

    for monitor in active_monitors:
        try:
            monitor_id = monitor["_id"]
            collected = CrawlerService.crawl_monitor(
                keywords=monitor["keywords"],
                sources=monitor["sources"],
                per_keyword_count=2,
            )

            docs_to_insert = []
            alerts_triggered = 0

            for item in collected:
                score, label = SentimentService.analyze(item["content"])
                doc = {
                    "monitor_id": ObjectId(monitor_id),
                    "source_type": item["source_type"],
                    "title": item["title"],
                    "content": item["content"],
                    "author": item["author"],
                    "url": item["url"],
                    "raw_data": item["raw_data"],
                    "sentiment_score": score,
                    "sentiment_label": label,
                    "collected_at": datetime.utcnow(),
                }
                docs_to_insert.append(doc)

                if monitor["alert_enabled"]:
                    alert = await AlertService.check_sentiment_alert(
                        ObjectId(monitor_id),
                        score,
                        monitor["sentiment_threshold"],
                        doc,
                    )
                    if alert:
                        alerts_triggered += 1

            if docs_to_insert:
                await db.collected_data.insert_many(docs_to_insert)

            if monitor["alert_enabled"]:
                spike_alert = await AlertService.check_spike_alert(
                    ObjectId(monitor_id),
                    monitor["alert_spike_ratio"],
                )
                if spike_alert:
                    alerts_triggered += 1

            print(
                f"[{datetime.utcnow()}] 定时采集完成 - 监控任务: {monitor['name']}, "
                f"采集: {len(docs_to_insert)} 条, 告警: {alerts_triggered} 个"
            )

        except Exception as e:
            print(f"[{datetime.utcnow()}] 定时采集出错 - 监控任务 {monitor.get('_id')}: {str(e)}")


def start_scheduler():
    trigger = IntervalTrigger(minutes=5)
    scheduler.add_job(
        scheduled_crawl,
        trigger=trigger,
        id="periodic_crawl_job",
        name="周期性数据采集任务",
        replace_existing=True,
    )
    scheduler.start()
    print("定时任务调度器已启动 - 每5分钟执行一次数据采集")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("定时任务调度器已停止")
