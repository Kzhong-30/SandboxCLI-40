import pytest
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.mock_mongo import MockCollection

@pytest.mark.asyncio
class TestMockMongoBasic:
    async def test_insert_count(self):
        c = MockCollection()
        await c.insert_one({"v":1})
        assert await c.count_documents({}) == 1

    async def test_find_filter(self):
        c = MockCollection()
        await c.insert_many([{"t":"a"},{"t":"b"}])
        r = await c.find({"t":"a"}).to_list(None)
        assert len(r) == 1


    async def test_sort_asc(self):
        c = MockCollection()
        await c.insert_many([{"v":3},{"v":1},{"v":2}])
        r = await c.find({}, sort=[("v",1)]).to_list(None)
        assert [d["v"] for d in r] == [1,2,3]

    async def test_sort_desc(self):
        c = MockCollection()
        await c.insert_many([{"v":3},{"v":1},{"v":2}])
        r = await c.find({}, sort=[("v",-1)]).to_list(None)
        assert [d["v"] for d in r] == [3,2,1]


    async def test_limit(self):
        c = MockCollection()
        await c.insert_many([{"v":i} for i in range(10)])
        r = await c.find({}, limit=3).to_list(None)
        assert len(r) == 3

    async def test_skip(self):
        c = MockCollection()
        await c.insert_many([{"v":i} for i in range(10)])
        r = await c.find({}, sort=[("v",1)], skip=7).to_list(None)
        assert len(r) == 3 and r[0]["v"] == 7

    async def test_sort_limit_skip(self):
        c = MockCollection()
        await c.insert_many([{"r":i} for i in range(10)])
        r = await c.find({}, sort=[("r",-1)], limit=3, skip=2).to_list(None)
        assert [d["r"] for d in r] == [7,6,5]

    async def test_find_one(self):
        c = MockCollection()
        await c.insert_many([{"name":"a"},{"name":"b"}])
        r = await c.find_one({"name":"a"})
        assert r is not None and r["name"] == "a"

