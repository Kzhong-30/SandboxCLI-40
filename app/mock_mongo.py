from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from copy import deepcopy
import re


class MockCursor:
    def __init__(self, documents: List[dict]):
        self._docs = documents
        self._index = 0
        self._sort_key = None
        self._sort_order = 1
        self._skip = 0
        self._limit = None

    def sort(self, key, order=1):
        self._sort_key = key
        self._sort_order = order
        return self

    def skip(self, n: int):
        self._skip = n
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    async def to_list(self, length: int = None) -> List[dict]:
        docs = deepcopy(self._docs)
        if self._sort_key:
            reverse = self._sort_order == -1
            if isinstance(self._sort_key, list):
                key, order = self._sort_key[0]
                reverse = order == -1
                docs.sort(key=lambda x: x.get(key) if x.get(key) is not None else "", reverse=reverse)
            else:
                docs.sort(key=lambda x: x.get(self._sort_key) if x.get(self._sort_key) is not None else "", reverse=reverse)
        if self._skip:
            docs = docs[self._skip:]
        if self._limit:
            docs = docs[:self._limit]
        if length:
            docs = docs[:length]
        return docs

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._docs):
            raise StopAsyncIteration
        item = self._docs[self._index]
        self._index += 1
        return item


class MockAggregationCursor:
    def __init__(self, results: List[dict]):
        self._results = results
        self._index = 0

    async def to_list(self, length: int = None) -> List[dict]:
        if length:
            return self._results[:length]
        return self._results

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._results):
            raise StopAsyncIteration
        item = self._results[self._index]
        self._index += 1
        return item


def _match_condition(doc: dict, condition: dict) -> bool:
    for key, value in condition.items():
        if key == "$or":
            if not any(_match_condition(doc, sub) for sub in value):
                return False
        elif key == "$and":
            if not all(_match_condition(doc, sub) for sub in value):
                return False
        elif isinstance(value, dict):
            doc_val = doc.get(key)
            for op, op_val in value.items():
                if op == "$gte":
                    if not (doc_val is not None and doc_val >= op_val):
                        return False
                elif op == "$gt":
                    if not (doc_val is not None and doc_val > op_val):
                        return False
                elif op == "$lte":
                    if not (doc_val is not None and doc_val <= op_val):
                        return False
                elif op == "$lt":
                    if not (doc_val is not None and doc_val < op_val):
                        return False
                elif op == "$eq":
                    if doc_val != op_val:
                        return False
                elif op == "$ne":
                    if doc_val == op_val:
                        return False
                elif op == "$regex":
                    if doc_val is None:
                        return False
                    pattern = op_val
                    flags = 0
                    if "$options" in value:
                        if "i" in value["$options"]:
                            flags = re.IGNORECASE
                    try:
                        if not re.search(pattern.pattern if hasattr(pattern, 'pattern') else str(pattern), str(doc_val), flags):
                            return False
                    except Exception:
                        return False
        else:
            if doc.get(key) != value:
                return False
    return True


def _run_aggregation(docs: List[dict], pipeline: List[dict]) -> List[dict]:
    result = deepcopy(docs)
    for stage in pipeline:
        for op, params in stage.items():
            if op == "$match":
                result = [d for d in result if _match_condition(d, params)]
            elif op == "$group":
                groups: Dict[str, dict] = {}
                group_id_spec = params.get("_id", None)
                for doc in result:
                    if isinstance(group_id_spec, dict):
                        key_parts = []
                        for k, expr in group_id_spec.items():
                            if isinstance(expr, dict):
                                for op_k, op_v in expr.items():
                                    if op_k.startswith("$"):
                                        field = op_v.replace("$", "")
                                        val = doc.get(field)
                                        if isinstance(val, datetime):
                                            if op_k == "$year":
                                                key_parts.append(str(val.year))
                                            elif op_k == "$month":
                                                key_parts.append(str(val.month))
                                            elif op_k == "$dayOfMonth":
                                                key_parts.append(str(val.day))
                                            elif op_k == "$hour":
                                                key_parts.append(str(val.hour))
                            else:
                                key_parts.append(str(doc.get(expr.replace("$", ""), "")))
                        key = "|".join(key_parts)
                    else:
                        key = str(doc.get(group_id_spec.replace("$", ""), "") if group_id_spec else "all")

                    if key not in groups:
                        group_data = {"_id": {}}
                        if isinstance(group_id_spec, dict):
                            idx = 0
                            for k, expr in group_id_spec.items():
                                if isinstance(expr, dict):
                                    for op_k, op_v in expr.items():
                                        field = op_v.replace("$", "")
                                        val = doc.get(field)
                                        if isinstance(val, datetime):
                                            if op_k == "$year":
                                                group_data["_id"][k] = val.year
                                            elif op_k == "$month":
                                                group_data["_id"][k] = val.month
                                            elif op_k == "$dayOfMonth":
                                                group_data["_id"][k] = val.day
                                            elif op_k == "$hour":
                                                group_data["_id"][k] = val.hour
                                idx += 1

                        for field, expr in params.items():
                            if field == "_id":
                                continue
                            if isinstance(expr, dict):
                                for agg_op in expr:
                                    if agg_op == "$sum":
                                        if agg_op == "$sum":
                                            val = expr[agg_op]
                                            if isinstance(val, int) or isinstance(val, float):
                                                group_data[field] = val
                                            elif isinstance(val, dict):
                                                for cond_op, cond_val in val.items():
                                                    if cond_op == "$cond":
                                                        if_expr, true_val, false_val = cond_val
                                                        ok = False
                                                        if isinstance(if_expr, list):
                                                            eq_op, eq_vals = if_expr[0], if_expr[1:]
                                                            if eq_op == "$eq":
                                                                doc_v1 = eq_vals[0]
                                                                doc_v2 = eq_vals[1]
                                                                if isinstance(doc_v1, str) and doc_v1.startswith("$"):
                                                                    doc_v1 = doc.get(doc_v1[1:])
                                                                if isinstance(doc_v2, str) and doc_v2.startswith("$"):
                                                                    doc_v2 = doc.get(doc_v2[1:])
                                                                ok = doc_v1 == doc_v2
                                                        if ok:
                                                            if isinstance(true_val, int):
                                                                group_data[field] = group_data.get(field, 0) + true_val
                                                        else:
                                                            if isinstance(false_val, int):
                                                                group_data[field] = group_data.get(field, 0) + false_val
                                                        break
                                    elif agg_op == "$avg":
                                        field_val = expr[agg_op].replace("$", "")
                                        vals = groups.get(key, {}).get(f"__{field}__", [])
                                        vals.append(doc.get(field_val))
                                        group_data[f"__{field}__"] = vals
                                    elif agg_op == "$push":
                                        push_val = expr[agg_op]
                                        if isinstance(push_val, dict):
                                            for concat_op, concat_fields in push_val.items():
                                                if concat_op == "$concat":
                                                    parts = []
                                                    for f in concat_fields:
                                                        if isinstance(f, str) and f.startswith("$"):
                                                            parts.append(str(doc.get(f[1:], "")))
                                                        else:
                                                            parts.append(str(f))
                                                    push_result = "".join(parts)
                                                    break
                                            arr = group_data.get(field, [])
                                            arr.append(push_result)
                                            group_data[field] = arr

                        if field not in group_data:
                            pass
                    groups[key] = group_data

                final_groups = []
                for key, gdata in groups.items():
                    clean_gdata = {}
                    for f, v in gdata.items():
                        if f.startswith("__") and f.endswith("__"):
                            real_field = f[2:-2]
                            if v:
                                clean_gdata[real_field] = sum(filter(None, v)) / len([x for x in v if x is not None]) if [x for x in v if x is not None] else 0
                        else:
                            clean_gdata[f] = v
                    final_groups.append(clean_gdata)
                result = final_groups
            elif op == "$sort":
                sort_key = list(params.keys())[0]
                order = params[sort_key]
                result.sort(key=lambda x: x.get("_id", {}).get(sort_key, x.get(sort_key, "")) if isinstance(x.get("_id"), dict) else x.get("_id", ""), reverse=(order == -1))
    return result


class MockCollection:
    def __init__(self):
        self._documents: List[dict] = []
        self._counter = 0

    def _new_id(self):
        from bson import ObjectId
        return ObjectId()

    async def insert_one(self, document: dict) -> Any:
        doc = deepcopy(document)
        if "_id" not in doc:
            doc["_id"] = self._new_id()
        self._documents.append(doc)
        return type("InsertOneResult", (), {"inserted_id": doc["_id"]})()

    async def insert_many(self, documents: List[dict]) -> Any:
        ids = []
        for doc in documents:
            d = deepcopy(doc)
            if "_id" not in d:
                d["_id"] = self._new_id()
            self._documents.append(d)
            ids.append(d["_id"])
        return type("InsertManyResult", (), {"inserted_ids": ids})()

    async def find_one(self, query: dict) -> Optional[dict]:
        for doc in self._documents:
            if _match_condition(doc, query):
                return deepcopy(doc)
        return None

    def find(
        self,
        query: dict = None,
        projection: dict = None,
        sort: Any = None,
        limit: int = 0,
        skip: int = 0,
    ) -> MockCursor:
        if query is None:
            query = {}
        docs = [d for d in self._documents if _match_condition(d, query)]
        cursor = MockCursor(docs)
        if sort is not None:
            if isinstance(sort, list) and len(sort) > 0:
                key, order = sort[0]
                cursor.sort(key, order)
            else:
                cursor.sort(sort)
        if skip > 0:
            cursor.skip(skip)
        if limit > 0:
            cursor.limit(limit)
        return cursor

    async def count_documents(self, query: dict = None) -> int:
        if query is None:
            query = {}
        return sum(1 for d in self._documents if _match_condition(d, query))

    async def update_one(self, query: dict, update: dict) -> Any:
        matched_count = 0
        modified_count = 0
        for doc in self._documents:
            if _match_condition(doc, query):
                matched_count = 1
                if "$set" in update:
                    for k, v in update["$set"].items():
                        doc[k] = v
                    modified_count = 1
                break
        return type("UpdateResult", (), {"matched_count": matched_count, "modified_count": modified_count})()

    async def update_many(self, query: dict, update: dict) -> Any:
        matched_count = 0
        modified_count = 0
        for doc in self._documents:
            if _match_condition(doc, query):
                matched_count += 1
                if "$set" in update:
                    for k, v in update["$set"].items():
                        doc[k] = v
                    modified_count += 1
        return type("UpdateResult", (), {"matched_count": matched_count, "modified_count": modified_count})()

    async def delete_one(self, query: dict) -> Any:
        deleted_count = 0
        for i, doc in enumerate(self._documents):
            if _match_condition(doc, query):
                del self._documents[i]
                deleted_count = 1
                break
        return type("DeleteResult", (), {"deleted_count": deleted_count})()

    async def delete_many(self, query: dict) -> Any:
        original_len = len(self._documents)
        self._documents = [d for d in self._documents if not _match_condition(d, query)]
        deleted_count = original_len - len(self._documents)
        return type("DeleteResult", (), {"deleted_count": deleted_count})()

    def aggregate(self, pipeline: List[dict]) -> MockAggregationCursor:
        results = _run_aggregation(self._documents, pipeline)
        return MockAggregationCursor(results)


class MockMongoDatabase:
    def __init__(self):
        self._collections: Dict[str, MockCollection] = {}

    def __getitem__(self, name: str) -> MockCollection:
        if name not in self._collections:
            self._collections[name] = MockCollection()
        return self._collections[name]

    def __getattr__(self, name: str) -> MockCollection:
        return self[name]


class MockMongoClient:
    def __init__(self, *args, **kwargs):
        self._databases: Dict[str, MockMongoDatabase] = {}

    def __getitem__(self, name: str) -> MockMongoDatabase:
        if name not in self._databases:
            self._databases[name] = MockMongoDatabase()
        return self._databases[name]

    def __getattr__(self, name: str) -> MockMongoDatabase:
        return self[name]

    def close(self):
        pass
