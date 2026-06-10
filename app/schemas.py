from datetime import datetime
from typing import List, Optional, Generic, TypeVar, Any
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId

T = TypeVar('T')


class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        from pydantic import GetCoreSchemaHandler

        def validate(v: Any) -> ObjectId:
            if isinstance(v, ObjectId):
                return v
            if isinstance(v, str) and ObjectId.is_valid(v):
                return ObjectId(v)
            raise ValueError(f"Invalid ObjectId: {v}")

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v), return_schema=core_schema.str_schema()
            ),
        )


class MonitorCreateSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., description="监控任务名称", min_length=1, max_length=200)
    keywords: List[str] = Field(..., description="监控关键词列表", min_length=1)
    sources: List[str] = Field(..., description="监控来源: weibo/news/forum", min_length=1)
    sentiment_threshold: float = Field(
        default=-0.3, ge=-1.0, le=1.0, description="情感告警阈值，低于此值触发告警"
    )
    alert_enabled: bool = Field(default=True, description="是否启用告警")
    alert_spike_ratio: float = Field(
        default=2.0, ge=1.0, description="负面数量突增倍数阈值"
    )
    is_active: bool = Field(default=True, description="是否激活监控")


class MonitorUpdateSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, description="监控任务名称")
    keywords: Optional[List[str]] = Field(default=None, description="监控关键词列表")
    sources: Optional[List[str]] = Field(default=None, description="监控来源")
    sentiment_threshold: Optional[float] = Field(default=None, description="情感告警阈值")
    alert_enabled: Optional[bool] = Field(default=None, description="是否启用告警")
    alert_spike_ratio: Optional[float] = Field(default=None, description="负面数量突增倍数阈值")
    is_active: Optional[bool] = Field(default=None, description="是否激活监控")


class MonitorResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId = Field(alias="_id", description="监控任务ID")
    name: str
    keywords: List[str]
    sources: List[str]
    sentiment_threshold: float
    alert_enabled: bool
    alert_spike_ratio: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CollectedDataResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId = Field(alias="_id", description="数据ID")
    monitor_id: PyObjectId = Field(description="所属监控任务ID")
    source_type: str = Field(description="数据来源类型")
    title: str
    content: str
    author: Optional[str] = None
    url: Optional[str] = None
    sentiment_score: float = Field(description="情感得分，-1到1之间")
    sentiment_label: str = Field(description="情感标签: positive/negative/neutral")
    collected_at: datetime


class AlertResponseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId = Field(alias="_id", description="告警ID")
    monitor_id: PyObjectId = Field(description="所属监控任务ID")
    alert_type: str = Field(description="告警类型")
    message: str = Field(description="告警消息")
    details: dict = Field(default_factory=dict, description="告警详情")
    is_read: bool = Field(default=False, description="是否已读")
    created_at: datetime


class TrendPointSchema(BaseModel):
    timestamp: datetime
    count: int = Field(description="总数量")
    positive_count: int = Field(description="正面数量")
    negative_count: int = Field(description="负面数量")
    neutral_count: int = Field(description="中性数量")
    avg_sentiment: float = Field(description="平均情感得分")


class TrendsResponseSchema(BaseModel):
    monitor_id: str
    time_granularity: str = Field(description="时间粒度: hour/day")
    start_time: datetime
    end_time: datetime
    data_points: List[TrendPointSchema]


class ComparisonItemSchema(BaseModel):
    keyword: str = Field(description="对比关键词")
    total_mentions: int = Field(description="总提及数")
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_sentiment: float = Field(description="平均情感得分")
    sentiment_distribution: dict = Field(description="情感分布")
    top_keywords: List[dict] = Field(description="热门关键词")


class ComparisonResponseSchema(BaseModel):
    items: List[ComparisonItemSchema]
    generated_at: datetime


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    message: str
