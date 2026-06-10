from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import connect_to_mongo, close_mongo_connection
from .scheduler import start_scheduler, stop_scheduler
from .routers import monitors, trends, comparison, reports, websockets


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    start_scheduler()
    yield
    stop_scheduler()
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    description="""
# 品牌舆情监控系统 API 文档

基于 FastAPI + MongoDB + TextBlob 构建的品牌舆情监控系统，提供以下核心功能：

## 主要功能
- **监控配置管理**: 创建/更新/删除监控任务，设置关键词、来源、情感阈值、告警规则
- **数据采集**: 定时模拟抓取微博/新闻/论坛数据，存储原始文本
- **情感分析**: 使用 TextBlob 分析文本情感倾向（正面/负面/中性），计算情感得分
- **趋势分析**: 获取关键词热度时间序列，按小时/天聚合
- **告警推送**: WebSocket 实时推送负面情感超阈值或数量突增告警
- **竞品对比**: 多品牌声量、情感、关键词云对比分析
- **报告导出**: 生成舆情分析 PDF 报告并下载

## 技术栈
- FastAPI + Python 3.11
- MongoDB (Motor 异步驱动)
- TextBlob (情感分析)
- APScheduler (定时任务)
- ReportLab (PDF 生成)
- WebSocket (实时告警)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "舆情监控系统开发团队",
        "email": "support@op-monitor.example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitors.router)
app.include_router(trends.router)
app.include_router(comparison.router)
app.include_router(reports.router)
app.include_router(websockets.router)


@app.get(
    "/",
    tags=["系统"],
    summary="系统健康检查",
    description="检查系统运行状态和版本信息",
)
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get(
    "/health",
    tags=["系统"],
    summary="健康检查接口",
    description="返回服务健康状态",
)
async def health_check():
    return {"status": "healthy"}
