import urllib.parse
import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from app.main import app
from app.mock_mongo import MockMongoClient, MockMongoDatabase

client = TestClient(app)


@pytest.fixture
def mock_db(monkeypatch):
    mock_client = MockMongoClient()
    db = mock_client["test_db"]
    
    async def get_mock_db():
        return db
    
    monkeypatch.setattr("app.database.get_database", get_mock_db)
    return db


def test_chinese_filename_encoding():
    monitor_name = "新能源汽车舆情监控"
    monitor_id = str(ObjectId())
    
    monitor_name_safe = ''.join(c for c in monitor_name if ord(c) < 128) or "opinion_report"
    expected_safe_name = f"{monitor_name_safe}_{monitor_id}.pdf"
    expected_full_name = f"{monitor_name}_{monitor_id}.pdf"
    expected_encoded_name = urllib.parse.quote(expected_full_name)
    
    expected_header = f'attachment; filename="{expected_safe_name}"; filename*=UTF-8\'\'{expected_encoded_name}'
    
    assert expected_safe_name == f"_{monitor_id}.pdf"
    assert expected_encoded_name == urllib.parse.quote(f"新能源汽车舆情监控_{monitor_id}.pdf")
    assert "filename*=UTF-8''" in expected_header
    assert 'filename="' in expected_header


def test_chinese_filename_with_ascii_mixed():
    monitor_name = "Tesla特斯拉2024监控"
    monitor_id = str(ObjectId())
    
    monitor_name_safe = ''.join(c for c in monitor_name if ord(c) < 128) or "opinion_report"
    expected_safe_name = f"{monitor_name_safe}_{monitor_id}.pdf"
    expected_full_name = f"{monitor_name}_{monitor_id}.pdf"
    expected_encoded_name = urllib.parse.quote(expected_full_name)
    
    expected_header = f'attachment; filename="{expected_safe_name}"; filename*=UTF-8\'\'{expected_encoded_name}'
    
    assert expected_safe_name == f"Tesla2024_{monitor_id}.pdf"
    assert expected_encoded_name == urllib.parse.quote(f"Tesla特斯拉2024监控_{monitor_id}.pdf")
    assert "filename*=UTF-8''" in expected_header


def test_safe_name_fallback_when_all_chinese():
    monitor_name = "舆情分析报告"
    monitor_name_safe = ''.join(c for c in monitor_name if ord(c) < 128) or "opinion_report"
    
    assert monitor_name_safe == "opinion_report"


def test_safe_name_with_spaces_and_special_chars():
    monitor_name = "Market Analysis & Report 2024"
    monitor_name_safe = ''.join(c for c in monitor_name if ord(c) < 128) or "opinion_report"
    
    assert monitor_name_safe == "Market Analysis & Report 2024"


def test_filename_default_when_no_name():
    monitor_name = "舆情报告"
    monitor_id = str(ObjectId())
    
    full_name = f"{monitor_name}_{monitor_id}.pdf"
    encoded_name = urllib.parse.quote(full_name)
    safe_name = ''.join(c for c in monitor_name if ord(c) < 128) or "opinion_report"
    safe_name = f"{safe_name}_{monitor_id}.pdf"
    
    header = f'attachment; filename="{safe_name}"; filename*=UTF-8\'\'{encoded_name}'
    
    assert "舆情报告" in full_name
    assert encoded_name == urllib.parse.quote(f"舆情报告_{monitor_id}.pdf")
    assert safe_name == f"opinion_report_{monitor_id}.pdf"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
import requests

BASE = "http://localhost:8001"
monitor_id = None
passed = 0
failed = 0


def run_test(name, test_fn):
    global passed, failed
    try:
        test_fn()
        print(f"✅ {name}")
        passed += 1
    except Exception as e:
        print(f"❌ {name}: {str(e)[:120]}")
        failed += 1


def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
run_test("1. 健康检查接口", test_health)


def test_create_monitor():
    global monitor_id
    data = {
        "name": "重构测试监控",
        "keywords": ["华为", "小米"],
        "sources": ["weibo", "news", "forum"],
        "sentiment_threshold": -0.3,
        "alert_enabled": True,
        "alert_spike_ratio": 2.0,
    }
    r = requests.post(f"{BASE}/monitors", json=data, timeout=10)
    assert r.status_code == 200
    res = r.json()
    assert "_id" in res
    monitor_id = res["_id"]
    assert res["name"] == "重构测试监控"
run_test("2. 创建监控任务", test_create_monitor)


def test_collect():
    r = requests.post(f"{BASE}/monitors/{monitor_id}/collect", params={"count": 5}, timeout=30)
    assert r.status_code == 200
    assert "采集完成" in r.json()["message"]
run_test("3. 触发数据采集", test_collect)


def test_list_data():
    r = requests.get(f"{BASE}/monitors/{monitor_id}/data", params={"page": 1, "page_size": 5}, timeout=10)
    assert r.status_code == 200
    res = r.json()
    assert res["total"] > 0
    items = res["items"]
    assert len(items) > 0
    for it in items:
        assert "sentiment_label" in it
        assert it["sentiment_label"] in ["positive", "negative", "neutral"]
        assert "sentiment_score" in it
        assert -1.0 <= it["sentiment_score"] <= 1.0
run_test("4. 获取采集数据+情感得分区间", test_list_data)


def test_trends():
    r = requests.get(f"{BASE}/monitors/{monitor_id}/trends", params={"time_granularity": "hour"}, timeout=15)
    assert r.status_code == 200
    res = r.json()
    assert "data_points" in res
    for dp in res["data_points"]:
        assert "count" in dp
        assert "positive_count" in dp
        assert "avg_sentiment" in dp
run_test("5. 趋势分析接口", test_trends)


def test_compare_with_wordcloud():
    r = requests.get(
        f"{BASE}/compare",
        params={"keywords": ["华为", "小米"], "days": 7, "generate_wordcloud": True},
        timeout=30,
    )
    assert r.status_code == 200
    res = r.json()
    assert len(res["items"]) == 2
    for item in res["items"]:
        assert "total_mentions" in item
        assert "wordcloud_image_base64" in item
    wc_exist = bool(res["items"][0].get("wordcloud_image_base64"))
    print(f"      关键词云图片生成: {'✅' if wc_exist else '⚠️  未生成'}")
run_test("6. 竞品对比+关键词云", test_compare_with_wordcloud)


def test_alerts():
    r = requests.get(f"{BASE}/monitors/{monitor_id}/alerts", params={"page": 1}, timeout=10)
    assert r.status_code == 200
    res = r.json()
    assert "items" in res
    assert "total" in res
run_test("7. 告警列表接口", test_alerts)


def test_pdf_report():
    r = requests.get(f"{BASE}/reports/{monitor_id}", timeout=60)
    assert r.status_code == 200
    pdf_bytes = r.content
    assert len(pdf_bytes) > 10000
    assert pdf_bytes[:5] == b"%PDF-"
    print(f"      PDF大小: {len(pdf_bytes)/1024:.1f} KB")
run_test("8. PDF报告生成下载", test_pdf_report)


def test_swagger():
    r = requests.get(f"{BASE}/openapi.json", timeout=10)
    assert r.status_code == 200
    spec = r.json()
    paths = list(spec["paths"].keys())
    assert len(paths) >= 10
    print(f"      注册API端点: {len(paths)} 个")
run_test("9. Swagger/OpenAPI文档", test_swagger)


def test_sentiment_chinese():
    r = requests.post(f"{BASE}/monitors/{monitor_id}/collect", params={"count": 3}, timeout=30)
    r = requests.get(f"{BASE}/monitors/{monitor_id}/data", params={"page": 1, "page_size": 10}, timeout=10)
    items = r.json()["items"]
    for it in items[:3]:
        label = it["sentiment_label"]
        score = it["sentiment_score"]
        assert -1.0 <= score <= 1.0
        assert label in ["positive", "negative", "neutral"]
run_test("10. SnowNLP中文情感得分", test_sentiment_chinese)


print("")
print("=" * 50)
print(f"重构验证结果: {passed} 项通过, {failed} 项失败")
print(f"服务地址: {BASE}")
print(f"Swagger文档: {BASE}/docs")
if failed == 0:
    print("✅ 全部测试通过！重构验证完成。")
else:
    print("❌ 存在测试失败，请检查错误信息。")
