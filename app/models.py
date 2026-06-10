from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class MonitorBase(BaseModel):
    name: str
    keywords: List[str]
    sources: List[str]
    sentiment_threshold: float = Field(default=-0.3, ge=-1.0, le=1.0)
    alert_enabled: bool = True
    alert_spike_ratio: float = Field(default=2.0, ge=1.0)
    is_active: bool = True


class MonitorCreate(MonitorBase):
    pass


class MonitorUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    sentiment_threshold: Optional[float] = None
    alert_enabled: Optional[bool] = None
    alert_spike_ratio: Optional[float] = None
    is_active: Optional[bool] = None


class Monitor(MonitorBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CollectedDataBase(BaseModel):
    monitor_id: PyObjectId
    source_type: str
    title: str
    content: str
    author: Optional[str] = None
    url: Optional[str] = None
    raw_data: dict = {}


class CollectedData(CollectedDataBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sentiment_score: float = 0.0
    sentiment_label: str = "neutral"
    collected_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class AlertBase(BaseModel):
    monitor_id: PyObjectId
    alert_type: str
    message: str
    details: dict = {}


class Alert(AlertBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TrendPoint(BaseModel):
    timestamp: datetime
    count: int
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_sentiment: float


class ComparisonItem(BaseModel):
    keyword: str
    total_mentions: int
    positive_count: int
    negative_count: int
    neutral_count: int
    avg_sentiment: float
    sentiment_distribution: dict
    top_keywords: List[dict]


class ComparisonReport(BaseModel):
    items: List[ComparisonItem]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
