from typing import List
from fastapi import APIRouter, HTTPException, Query
from ..schemas import ComparisonResponseSchema
from ..services.comparison_service import ComparisonService

router = APIRouter(prefix="/compare", tags=["竞品对比分析"])


@router.get(
    "",
    response_model=ComparisonResponseSchema,
    summary="多品牌竞品对比分析",
    description="输入多个品牌关键词，返回对比分析报告，包括声量、情感分布和关键词云",
)
async def compare_keywords(
    keywords: List[str] = Query(
        ...,
        min_length=2,
        description="要对比的品牌关键词列表（至少2个）",
    ),
    days: int = Query(7, ge=1, le=90, description="统计的时间范围（天）"),
):
    if len(keywords) < 2:
        raise HTTPException(status_code=400, detail="至少需要提供2个关键词进行对比")

    report = await ComparisonService.compare_keywords(keywords, days=days)
    return report
