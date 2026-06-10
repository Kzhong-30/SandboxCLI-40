import urllib.parse
from io import BytesIO
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response
from bson import ObjectId
from ..database import get_database
from ..services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["报告生成导出"])


@router.get(
    "/{monitor_id}",
    summary="导出舆情分析报告 PDF",
    description="根据监控任务ID生成完整的舆情分析报告并以 PDF 格式下载",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF 格式的舆情分析报告",
        }
    },
)
async def download_report(
    monitor_id: str,
    db=Depends(get_database),
):
    if not ObjectId.is_valid(monitor_id):
        raise HTTPException(status_code=400, detail="无效的监控任务ID")

    monitor = await db.monitors.find_one({"_id": ObjectId(monitor_id)})
    if not monitor:
        raise HTTPException(status_code=404, detail="监控任务不存在")

    try:
        pdf_bytes = await ReportService.generate_report(ObjectId(monitor_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")

    filename = f"opinion_report_{monitor_id}.pdf"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}",
    }
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )
