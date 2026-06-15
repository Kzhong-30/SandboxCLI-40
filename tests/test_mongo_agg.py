import pytest
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.mock_mongo import MockCollection

@pytest.mark.asyncio
class TestMockMongoAggregate:
    async def test_group_sum(self):
        c = MockCollection()
        await c.insert_many([{"cat":"a","v":1},{"cat":"a","v":2},{"cat":"b","v":3}])
        r = await c.aggregate([{"$group":{"_id":"$cat","total":{"$sum":"$v"}}}]).to_list(None)
        assert len(r) == 2
        for d in r:
            if d["_id"] == "a":
                assert d["total"] == 3
            elif d["_id"] == "b":
                assert d["total"] == 3

    async def test_cond(self):
        c = MockCollection()
        await c.insert_many([{"label":"pos","v":1},{"label":"neg","v":2}])
        p = [{"$group":{"_id":None,"pos":{"$sum":{"$cond":[{"$eq":["$label","pos"]},1,0]}}}}]
        r = await c.aggregate(p).to_list(None)
        assert r[0]["pos"] == 1

    async def test_push(self):
        c = MockCollection()
        await c.insert_many([{"g":"a","v":1},{"g":"a","v":2},{"g":"b","v":3}])
        p = [{"$group":{"_id":"$g","items":{"$push":"$v"}}}]
        r = await c.aggregate(p).to_list(None)
        for d in r:
            if d["_id"] == "a":
                assert sorted(d["items"]) == [1,2]

    async def test_match_group(self):
        c = MockCollection()
        await c.insert_many([{"t":"a","v":1},{"t":"b","v":2},{"t":"a","v":3}])
        p = [{"$match":{"t":"a"}},{"$group":{"_id":None,"s":{"$sum":"$v"}}}]
        r = await c.aggregate(p).to_list(None)
        assert r[0]["s"] == 4

    async def test_sort_limit_skip(self):
        c = MockCollection()
        await c.insert_many([{"v":i} for i in range(10)])
        p = [{"$sort":{"v":-1}},{"$skip":2},{"$limit":3}]
        r = await c.aggregate(p).to_list(None)
        assert [d["v"] for d in r] == [7,6,5]

    async def test_sort_asc(self):
        c = MockCollection()
        await c.insert_many([{"v":3},{"v":1},{"v":2}])
        p = [{"$sort":{"v":1}}]
        r = await c.aggregate(p).to_list(None)
        assert [d["v"] for d in r] == [1,2,3]

