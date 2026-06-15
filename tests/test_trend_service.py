import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mock_mongo import MockCollection
from app.services.trend_service import TrendService
from bson import ObjectId


@pytest.fixture
def sample_monitor_id():
    return ObjectId()


@pytest.fixture
def mock_db_with_hourly_data(sample_monitor_id):
    coll = MockCollection()
    now = datetime.utcnow()
    docs = []
    for hour_offset in range(6):
        base_time = now - timedelta(hours=hour_offset)
        for i in range(3):
            docs.append({
                "monitor_id": sample_monitor_id,
                "content": f"test content {hour_offset}-{i}",
                "sentiment_score": 0.5 if i < 2 else -0.3,
                "sentiment_label": "positive" if i < 2 else "negative",
                "collected_at": base_time.replace(minute=i * 10, second=0, microsecond=0),
            })
    import asyncio
    asyncio.run(coll.insert_many(docs))
    return coll


@pytest.fixture
def mock_db_with_daily_data(sample_monitor_id):
    coll = MockCollection()
    now = datetime.utcnow()
    docs = []
    for day_offset in range(5):
        base_time = now - timedelta(days=day_offset)
        for i in range(4):
            docs.append({
                "monitor_id": sample_monitor_id,
                "content": f"test day {day_offset}-{i}",
                "sentiment_score": 0.6 if i < 3 else -0.4,
                "sentiment_label": "positive" if i < 3 else "negative",
                "collected_at": base_time.replace(hour=i * 3, minute=0, second=0, microsecond=0),
            })
    import asyncio
    asyncio.run(coll.insert_many(docs))
    return coll


@pytest.fixture
def mock_db_empty():
    return MockCollection()


class TestTrendServiceHourGranularity:
    @pytest.mark.asyncio
    async def test_hour_granularity_buckets(self, sample_monitor_id, mock_db_with_hourly_data, monkeypatch):
        fake_db = MagicMock()
        fake_db.collected_data = mock_db_with_hourly_data
        monkeypatch.setattr("app.services.trend_service.get_database", lambda: fake_db)

        data_points, start, end = await TrendService.get_trends(
            sample_monitor_id, time_granularity="hour", hours=24
        )

        assert len(data_points) > 0
        assert isinstance(data_points, list)

        for point in data_points:
            assert "timestamp" in point
            assert "count" in point
            assert "positive_count" in point
            assert "negative_count" in point
            assert "neutral_count" in point
            assert "avg_sentiment" in point
            assert isinstance(point["count"], int)
            assert point["count"] > 0
            assert isinstance(point["avg_sentiment"], float)

    @pytest.mark.asyncio
    async def test_hour_granularity_counts_match(self, sample_monitor_id, mock_db_with_hourly_data, monkeypatch):
        fake_db = MagicMock()
        fake_db.collected_data = mock_db_with_hourly_data
        monkeypatch.setattr("app.services.trend_service.get_database", lambda: fake_db)

        data_points, _, _ = await TrendService.get_trends(
            sample_monitor_id, time_granularity="hour", hours=24
        )

        total_count = sum(p["count"] for p in data_points)
        total_pos = sum(p["positive_count"] for p in data_points)
        total_neg = sum(p["negative_count"] for p in data_points)
        total_neu = sum(p["neutral_count"] for p in data_points)

        assert total_count == 18
        assert total_pos + total_neg + total_neu == total_count
        assert total_pos == 12
        assert total_neg == 6
        assert total_neu == 0


class TestTrendServiceDayGranularity:
    @pytest.mark.asyncio
    async def test_day_granularity_buckets(self, sample_monitor_id, mock_db_with_daily_data, monkeypatch):
        fake_db = MagicMock()
        fake_db.collected_data = mock_db_with_daily_data
        monkeypatch.setattr("app.services.trend_service.get_database", lambda: fake_db)

        data_points, start, end = await TrendService.get_trends(
            sample_monitor_id, time_granularity="day", hours=168
        )

        assert len(data_points) > 0
        assert isinstance(data_points, list)

        for point in data_points:
            assert "timestamp" in point
            assert isinstance(point["timestamp"], datetime)
            assert point["timestamp"].hour == 0
            assert point["timestamp"].minute == 0
            assert point["count"] > 0

    @pytest.mark.asyncio
    async def test_day_granularity_total_count(self, sample_monitor_id, mock_db_with_daily_data, monkeypatch):
        fake_db = MagicMock()
        fake_db.collected_data = mock_db_with_daily_data
        monkeypatch.setattr("app.services.trend_service.get_database", lambda: fake_db)

        data_points, _, _ = await TrendService.get_trends(
            sample_monitor_id, time_granularity="day", hours=168
        )

        total_count = sum(p["count"] for p in data_points)
        assert total_count == 20

        total_pos = sum(p["positive_count"] for p in data_points)
        total_neg = sum(p["negative_count"] for p in data_points)
        assert total_pos == 15
        assert total_neg == 5


class TestTrendServiceEmptyData:
    @pytest.mark.asyncio
    async def test_empty_dataset_no_division_by_zero(self, sample_monitor_id, mock_db_empty, monkeypatch):
        fake_db = MagicMock()
        fake_db.collected_data = mock_db_empty
        monkeypatch.setattr("app.services.trend_service.get_database", lambda: fake_db)

        try:
            data_points, start, end = await TrendService.get_trends(
                sample_monitor_id, time_granularity="hour", hours=24
            )
        except ZeroDivisionError:
            pytest.fail("ZeroDivisionError raised on empty dataset")

        assert isinstance(data_points, list)
        assert len(data_points) == 0

    @pytest.mark.asyncio
    async def test_empty_day_granularity(self, sample_monitor_id, mock_db_empty, monkeypatch):
        fake_db = MagicMock()
        fake_db.collected_data = mock_db_empty
        monkeypatch.setattr("app.services.trend_service.get_database", lambda: fake_db)

        try:
            data_points, start, end = await TrendService.get_trends(
                sample_monitor_id, time_granularity="day", hours=168
            )
        except ZeroDivisionError:
            pytest.fail("ZeroDivisionError raised on empty dataset (day)")

        assert isinstance(data_points, list)
        assert len(data_points) == 0
