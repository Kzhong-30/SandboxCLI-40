import base64
import urllib.parse
from fastapi import APIRouter, HTTPException, Query, Response
from ..services.comparison_service import ComparisonService

router = APIRouter(prefix='/wordcloud', tags=['关键词云'])

@router.get(
    '/generate.png',
    summary='生成关键词云图片',
    description='根据关键词生成词云PNG图片并下载',
    responses={200: {'content': {'image/png': {}}}},
)
async def generate_wordcloud(
    keyword: str = Query(..., description='关键词'),
    days: int = Query(7, ge=1, le=90, description='统计天数'),
):
    result = await ComparisonService.compare_keywords(
        [keyword], days=days, generate_image=True
    )
    if not result["items"]:
        raise HTTPException(status_code=404, detail="未找到相关数据")
    wordcloud_b64 = result["items"][0].get("wordcloud_image_base64")
    if not wordcloud_b64:
        raise HTTPException(status_code=500, detail="词云生成失败")
    png_bytes = base64.b64decode(wordcloud_b64)
    fname = f"keyword_cloud_{keyword}.png"
    ascii_name = fname.encode("ascii", errors="replace").decode("ascii")
    utf8_name = urllib.parse.quote(fname, safe="")
    cd = f"inline; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}"
    headers = {"Content-Disposition": cd, "Cache-Control": "public, max-age=3600"}
    return Response(content=png_bytes, media_type="image/png", headers=headers)
