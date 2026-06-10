from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from bson import ObjectId
from ..database import get_database
from ..schemas import (
    MonitorCreateSchema,
    MonitorUpdateSchema,
    MonitorResponseSchema,
    CollectedDataResponseSchema,
    AlertResponseSchema,
    PaginatedResponse,
    MessageResponse,
)
from ..services.crawler_service import CrawlerService
from ..services.sentiment_service import SentimentService
from ..services.alert_service import AlertService

router = APIRouter(prefix="/monitors", tags=["监控配置管理"])


@router.post(
    "",
    response_model=MonitorResponseSchema,
    summary="创建监控任务",
    description="创建新的舆情监控任务，设置关键词、监控来源、情感阈值等参数",
)
async def create_monitor(
    data: MonitorCreateSchema,
    db=Depends(get_database),
):
    now = datetime.utcnow()
    document = data.model_dump()
    document["created_at"] = now
    document["updated_at"] = now

    result = await db.monitors.insert_one(document)
    document["_id"] = result.inserted_id

    return document


@router.get(
    "",
    response_model=PaginatedResponse[MonitorResponseSchema],
    summary="获取监控任务列表",
    description="分页获取所有监控任务",
)
async def list_monitors(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否只显示激活的任务"),
    db=Depends(get_database),
):
    query = {}
    if is_active is not None:
        query["is_active"] = is_active

    total = await db.monitors.count_documents(query)
    cursor = db.monitors.find(query).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    items = await cursor.to_list(length=page_size)

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/{monitor_id}",
    response_model=MonitorResponseSchema,
    summary="获取监控任务详情",
    description="根据ID获取单个监控任务的详细信息",
)
async def get_monitor(
    monitor_id: str,
    db=Depends(get_database),
):
    if not ObjectId.is_valid(monitor_id):
        raise HTTPException(status_code=400, detail="无效的监控任务ID")

    document = await db.monitors.find_one({"_id": ObjectId(monitor_id)})
    if not document:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    return document


@router.put(
    "/{monitor_id}",
    response_model=MonitorResponseSchema,
    summary="更新监控任务",
    description="更新监控任务的配置参数",
)
async def update_monitor(
    monitor_id: str,
    data: MonitorUpdateSchema,
    db=Depends(get_database),
):
    if not ObjectId.is_valid(monitor_id):
        raise HTTPException(status_code=400, detail="无效的监控任务ID")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    result = await db.monitors.update_one(
        {"_id": ObjectId(monitor_id)},
        {"$set": update_data},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    document = await db.monitors.find_one({"_id": ObjectId(monitor_id)})
    return document


@router.delete(
    "/{monitor_id}",
    response_model=MessageResponse,
    summary="删除监控任务",
    description="根据ID删除指定的监控任务",
)
async def delete_monitor(
    monitor_id: str,
    db=Depends(get_database),
):
    if not ObjectId.is_valid(monitor_id):
        raise HTTPException(status_code=400, detail="无效的监控任务ID")

    result = await db.monitors.delete_one({"_id": ObjectId(monitor_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    await db.collected_data.delete_many({"monitor_id": ObjectId(monitor_id)})
    await db.alerts.delete_many({"monitor_id": ObjectId(monitor_id)})

    return {"message": "监控任务删除成功"}


@router.post(
    "/{monitor_id}/collect",
    response_model=MessageResponse,
    summary="手动触发数据采集",
    description="立即执行一次数据采集，模拟抓取并分析数据",
)
async def trigger_collection(
    monitor_id: str,
    count: int = Query(3, ge=1, le=20, description="每个来源每次采集数量"),
    db=Depends(get_database),
):
    if not ObjectId.is_valid(monitor_id):
        raise HTTPException(status_code=400, detail="无效的监控任务ID")

    monitor = await db.monitors.find_one({"_id": ObjectId(monitor_id)})
    if not monitor:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    collected = CrawlerService.crawl_monitor(
        keywords=monitor["keywords"],
        sources=monitor["sources"],
        per_keyword_count=count,
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

    return {
        "message": f"采集完成！共采集 {len(docs_to_insert)} 条数据，触发 {alerts_triggered} 个告警"
    }


@router.get(
    "/{monitor_id}/data",
    response_model=PaginatedResponse[CollectedDataResponseSchema],
    summary="获取采集数据列表",
    description="分页获取该监控任务的采集数据",
)
async def list_collected_data(
    monitor_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量"),
    sentiment_label: Optional[str] = Query(None, description="情感标签过滤: positive/negative/neutral"),
    db=Depends(get_database),
):
    if not ObjectId.is_valid(monitor_id):
        raise HTTPException(status_code=400, detail="无效的监控任务ID")

    query = {"monitor_id": ObjectId(monitor_id)}
    if sentiment_label:
        query["sentiment_label"] = sentiment_label

    total = await db.collected_data.count_documents(query)
    cursor = (
        db.collected_data.find(query)
        .sort("collected_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    items = await cursor.to_list(length=page_size)

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/{monitor_id}/alerts",
    response_model=PaginatedResponse[AlertResponseSchema],
    summary="获取告警列表",
    description="分页获取该监控任务的告警记录",
)
async def list_alerts(
    monitor_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_read: Optional[bool] = Query(None, description="是否已读过滤"),
    db=Depends(get_database),
):
    if not ObjectId.is_valid(monitor_id):
        raise HTTPException(status_code=400, detail="无效的监控任务ID")

    query = {"monitor_id": ObjectId(monitor_id)}
    if is_read is not None:
        query["is_read"] = is_read

    total = await db.alerts.count_documents(query)
    cursor = (
        db.alerts.find(query)
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    items = await cursor.to_list(length=page_size)

    return {"items": items, "total": total, "page": page, "page_size": page_size}
