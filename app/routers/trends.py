from fastapi import APIRouter, HTTPException, Query, Depends
from bson import ObjectId
from ..database import get_database
from ..schemas import TrendsResponseSchema
from ..services.trend_service import TrendService

router = APIRouter(prefix="/monitors", tags=["趋势分析"])


@router.get(
    "/{monitor_id}/trends",
    response_model=TrendsResponseSchema,
    summary="获取关键词热度趋势",
    description="返回指定监控任务的关键词热度时间序列，支持按小时或天聚合",
)
async def get_monitor_trends(
    monitor_id: str,
    time_granularity: str = Query(
        "hour",
        pattern="^(hour|day)$",
        description="时间粒度：hour(按小时) 或 day(按天)",
    ),
    hours: int = Query(24, ge=1, le=8760, description="查询时间范围（小时）"),
    db=Depends(get_database),
):
    if not ObjectId.is_valid(monitor_id):
        raise HTTPException(status_code=400, detail="无效的监控任务ID")

    monitor = await db.monitors.find_one({"_id": ObjectId(monitor_id)})
    if not monitor:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    data_points, start_time, end_time = await TrendService.get_trends(
        ObjectId(monitor_id),
        time_granularity=time_granularity,
        hours=hours,
    )

    return {
        "monitor_id": monitor_id,
        "time_granularity": time_granularity,
        "start_time": start_time,
        "end_time": end_time,
        "data_points": data_points,
    }
