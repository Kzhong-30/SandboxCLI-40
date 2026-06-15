from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime
from copy import deepcopy
import re


class MockCursor:
    def __init__(self, documents: List[dict]):
        self._docs = documents
        self._index = 0
        self._sort_spec: Optional[List[Tuple[str, int]]] = None
        self._skip_n = 0
        self._limit_n: Optional[int] = None

    def sort(self, key_or_list: Any, direction: int = 1):
        if isinstance(key_or_list, list):
            self._sort_spec = [(k, d) for k, d in key_or_list]
        else:
            self._sort_spec = [(key_or_list, direction)]
        return self

    def skip(self, n: int):
        self._skip_n = n
        return self

    def limit(self, n: int):
        self._limit_n = n
        return self

    def _apply_operations(self) -> List[dict]:
        docs = deepcopy(self._docs)
        if self._sort_spec:
            for sort_key, sort_dir in reversed(self._sort_spec):
                reverse = sort_dir == -1

                def get_sort_val(d: dict, k: str) -> Any:
                    v = d.get(k)
                    if v is None:
                        return ""
                    return v

                docs.sort(
                    key=lambda x: get_sort_val(x, sort_key),
                    reverse=reverse,
                )
        if self._skip_n > 0:
            docs = docs[self._skip_n:]
        if self._limit_n is not None:
            docs = docs[:self._limit_n]
        return docs

    async def to_list(self, length: int = None) -> List[dict]:
        docs = self._apply_operations()
        if length:
            docs = docs[:length]
        return docs

    def __aiter__(self):
        self._cached = self._apply_operations()
        self._index = 0
        return self

    async def __anext__(self):
        if self._index >= len(self._cached):
            raise StopAsyncIteration
        item = self._cached[self._index]
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


def _resolve_field(doc: dict, field_ref: Any) -> Any:
    if isinstance(field_ref, str) and field_ref.startswith("$"):
        field_name = field_ref[1:]
        return doc.get(field_name)
    return field_ref


def _eval_expression(doc: dict, expr: Any) -> Any:
    if isinstance(expr, str) and expr.startswith("$"):
        return _resolve_field(doc, expr)
    if isinstance(expr, dict):
        for op, args in expr.items():
            if op == "$cond":
                if_expr, true_expr, false_expr = args
                cond_result = _eval_expression(doc, if_expr)
                if cond_result:
                    return _eval_expression(doc, true_expr)
                else:
                    return _eval_expression(doc, false_expr)
            elif op == "$eq":
                a = _eval_expression(doc, args[0])
                b = _eval_expression(doc, args[1])
                return a == b
            elif op == "$ne":
                a = _eval_expression(doc, args[0])
                b = _eval_expression(doc, args[1])
                return a != b
            elif op == "$gt":
                a = _eval_expression(doc, args[0])
                b = _eval_expression(doc, args[1])
                return a is not None and b is not None and a > b
            elif op == "$gte":
                a = _eval_expression(doc, args[0])
                b = _eval_expression(doc, args[1])
                return a is not None and b is not None and a >= b
            elif op == "$lt":
                a = _eval_expression(doc, args[0])
                b = _eval_expression(doc, args[1])
                return a is not None and b is not None and a < b
            elif op == "$lte":
                a = _eval_expression(doc, args[0])
                b = _eval_expression(doc, args[1])
                return a is not None and b is not None and a <= b
            elif op == "$concat":
                parts = []
                for a in args:
                    v = _eval_expression(doc, a)
                    parts.append(str(v) if v is not None else "")
                return "".join(parts)
            elif op == "$sum":
                if isinstance(args, int) or isinstance(args, float):
                    return args
                v = _eval_expression(doc, args)
                return v if isinstance(v, (int, float)) else 0
            elif op == "$avg":
                v = _eval_expression(doc, args)
                return v if isinstance(v, (int, float)) else None
            elif op == "$push":
                return _eval_expression(doc, args)
            elif op == "$year":
                v = _eval_expression(doc, args)
                return v.year if isinstance(v, datetime) else None
            elif op == "$month":
                v = _eval_expression(doc, args)
                return v.month if isinstance(v, datetime) else None
            elif op == "$dayOfMonth":
                v = _eval_expression(doc, args)
                return v.day if isinstance(v, datetime) else None
            elif op == "$hour":
                v = _eval_expression(doc, args)
                return v.hour if isinstance(v, datetime) else None
            elif op == "$minute":
                v = _eval_expression(doc, args)
                return v.minute if isinstance(v, datetime) else None
            elif op == "$second":
                v = _eval_expression(doc, args)
                return v.second if isinstance(v, datetime) else None
    return expr


def _match_condition(doc: dict, condition: dict) -> bool:
    for key, value in condition.items():
        if key == "$or":
            if not any(_match_condition(doc, sub) for sub in value):
                return False
        elif key == "$and":
            if not all(_match_condition(doc, sub) for sub in value):
                return False
        elif key == "$nor":
            if any(_match_condition(doc, sub) for sub in value):
                return False
        elif isinstance(value, dict):
            doc_val = doc.get(key)
            matched = True
            for op, op_val in value.items():
                if op == "$gte":
                    if doc_val is None or not (doc_val >= op_val):
                        matched = False
                elif op == "$gt":
                    if doc_val is None or not (doc_val > op_val):
                        matched = False
                elif op == "$lte":
                    if doc_val is None or not (doc_val <= op_val):
                        matched = False
                elif op == "$lt":
                    if doc_val is None or not (doc_val < op_val):
                        matched = False
                elif op == "$eq":
                    if doc_val != op_val:
                        matched = False
                elif op == "$ne":
                    if doc_val == op_val:
                        matched = False
                elif op == "$in":
                    if doc_val not in op_val:
                        matched = False
                elif op == "$nin":
                    if doc_val in op_val:
                        matched = False
                elif op == "$regex":
                    if doc_val is None:
                        matched = False
                    else:
                        try:
                            flags = 0
                            if "$options" in value and "i" in value["$options"]:
                                flags = re.IGNORECASE
                            pattern = op_val.pattern if hasattr(op_val, "pattern") else str(op_val)
                            if not re.search(pattern, str(doc_val), flags):
                                matched = False
                        except Exception:
                            matched = False
                elif op == "$exists":
                    exists = key in doc
                    if bool(op_val) != exists:
                        matched = False
                if not matched:
                    break
            if not matched:
                return False
        else:
            if key not in doc or doc.get(key) != value:
                return False
    return True


def _build_group_key(doc: dict, group_id_spec: Any) -> Tuple[Tuple, dict]:
    if group_id_spec is None:
        return (("__all__",), {})
    if isinstance(group_id_spec, str) and group_id_spec.startswith("$"):
        field = group_id_spec[1:]
        v = doc.get(field)
        key = (str(v),)
        return (key, {field: v})
    if isinstance(group_id_spec, dict):
        key_parts = []
        key_dict = {}
        for k, expr in group_id_spec.items():
            v = _eval_expression(doc, expr)
            key_parts.append(repr(v))
            key_dict[k] = v
        return (tuple(key_parts), key_dict)
    return ((str(group_id_spec),), {"_id_value": group_id_spec})


def _run_aggregation(docs: List[dict], pipeline: List[dict]) -> List[dict]:
    result = deepcopy(docs)

    for stage in pipeline:
        for op, params in stage.items():

            if op == "$match":
                result = [d for d in result if _match_condition(d, params)]

            elif op == "$group":
                groups: Dict[Tuple, dict] = {}
                group_id_spec = params.get("_id")

                accumulator_specs = {
                    field: expr for field, expr in params.items() if field != "_id"
                }

                for doc in result:
                    key_tuple, key_dict = _build_group_key(doc, group_id_spec)

                    if key_tuple not in groups:
                        new_group: dict = {"_id": key_dict if key_dict else None}
                        for field, expr in accumulator_specs.items():
                            for agg_op, agg_arg in expr.items():
                                if agg_op == "$sum":
                                    if isinstance(agg_arg, (int, float)):
                                        new_group[field] = agg_arg
                                    else:
                                        val = _eval_expression(doc, agg_arg)
                                        new_group[field] = val if isinstance(val, (int, float)) else 0
                                elif agg_op == "$avg":
                                    vals = []
                                    val = _eval_expression(doc, agg_arg)
                                    if val is not None:
                                        vals.append(val)
                                    new_group[f"__{field}__values__"] = vals
                                    new_group[field] = 0
                                elif agg_op == "$push":
                                    arr = []
                                    val = _eval_expression(doc, agg_arg)
                                    if val is not None:
                                        arr.append(val)
                                    new_group[field] = arr
                                elif agg_op == "$first":
                                    new_group[field] = _eval_expression(doc, agg_arg)
                                elif agg_op == "$last":
                                    new_group[field] = _eval_expression(doc, agg_arg)
                                elif agg_op == "$max":
                                    new_group[field] = _eval_expression(doc, agg_arg)
                                elif agg_op == "$min":
                                    new_group[field] = _eval_expression(doc, agg_arg)
                        groups[key_tuple] = new_group
                    else:
                        g = groups[key_tuple]
                        for field, expr in accumulator_specs.items():
                            for agg_op, agg_arg in expr.items():
                                if agg_op == "$sum":
                                    if isinstance(agg_arg, (int, float)):
                                        g[field] = g.get(field, 0) + agg_arg
                                    else:
                                        val = _eval_expression(doc, agg_arg)
                                        if isinstance(val, (int, float)):
                                            g[field] = g.get(field, 0) + val
                                elif agg_op == "$avg":
                                    val = _eval_expression(doc, agg_arg)
                                    if val is not None:
                                        g[f"__{field}__values__"].append(val)
                                elif agg_op == "$push":
                                    val = _eval_expression(doc, agg_arg)
                                    if val is not None:
                                        g[field].append(val)
                                elif agg_op == "$last":
                                    g[field] = _eval_expression(doc, agg_arg)
                                elif agg_op == "$max":
                                    curr = g.get(field)
                                    new_val = _eval_expression(doc, agg_arg)
                                    if curr is None or (new_val is not None and new_val > curr):
                                        g[field] = new_val
                                elif agg_op == "$min":
                                    curr = g.get(field)
                                    new_val = _eval_expression(doc, agg_arg)
                                    if curr is None or (new_val is not None and new_val < curr):
                                        g[field] = new_val

                final_groups = []
                for key_tuple, gdata in groups.items():
                    clean = {}
                    computed_fields = set()
                    for f, v in gdata.items():
                        if f.startswith("__") and f.endswith("__values__"):
                            real_field = f[2:-10]
                            vals = v
                            if vals:
                                clean[real_field] = sum(vals) / len(vals)
                            computed_fields.add(real_field)
                        elif f not in computed_fields:
                            clean[f] = v
                    final_groups.append(clean)
                result = final_groups

            elif op == "$sort":
                sort_items = list(params.items())
                for sort_key, sort_dir in reversed(sort_items):
                    reverse = sort_dir == -1

                    def _make_comparable(val):
                        if isinstance(val, dict):
                            return tuple(
                                (k, _make_comparable(val[k]))
                                for k in sorted(val.keys())
                            )
                        elif isinstance(val, list):
                            return tuple(_make_comparable(v) for v in val)
                        else:
                            return val

                    def get_val(d: dict, sk: str) -> Any:
                        parts = sk.split(".")
                        cur = d
                        for p in parts:
                            if isinstance(cur, dict):
                                cur = cur.get(p)
                            else:
                                return ""
                        return _make_comparable(cur) if cur is not None else ""

                    result.sort(
                        key=lambda x: get_val(x, sort_key),
                        reverse=reverse,
                    )

            elif op == "$project":
                new_result = []
                for doc in result:
                    projected = {}
                    keep_id = True
                    for field, spec in params.items():
                        if field == "_id":
                            keep_id = bool(spec) if isinstance(spec, (int, bool)) else True
                            if keep_id:
                                projected["_id"] = _eval_expression(doc, spec) if isinstance(spec, (dict, str)) else doc.get("_id")
                        elif isinstance(spec, (int, bool)):
                            if bool(spec) and field in doc:
                                projected[field] = doc[field]
                        else:
                            projected[field] = _eval_expression(doc, spec)
                    if keep_id and "_id" not in projected and "_id" in doc:
                        projected["_id"] = doc["_id"]
                    new_result.append(projected)
                result = new_result

            elif op == "$limit":
                n = params
                if isinstance(n, int):
                    result = result[:n]

            elif op == "$skip":
                n = params
                if isinstance(n, int):
                    result = result[n:]

            elif op == "$lookup":
                pass

            elif op == "$unwind":
                new_result = []
                field_path = params if isinstance(params, str) else params.get("path")
                if field_path and field_path.startswith("$"):
                    field = field_path[1:]
                    for doc in result:
                        arr = doc.get(field)
                        if isinstance(arr, list) and arr:
                            for item in arr:
                                nd = deepcopy(doc)
                                nd[field] = item
                                new_result.append(nd)
                        else:
                            new_result.append(doc)
                    result = new_result

            elif op == "$count":
                if isinstance(params, str):
                    result = [{params: len(result)}]
                else:
                    result = [{"count": len(result)}]

    return result


class MockCollection:
    def __init__(self):
        self._documents: List[dict] = []

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

    async def find_one(self, query: dict, projection: dict = None) -> Optional[dict]:
        for doc in self._documents:
            if _match_condition(doc, query):
                if projection is None:
                    return deepcopy(doc)
                projected = {}
                keep_id = True
                for field, spec in projection.items():
                    if field == "_id":
                        keep_id = bool(spec) if isinstance(spec, (int, bool)) else True
                    elif isinstance(spec, (int, bool)) and bool(spec) and field in doc:
                        projected[field] = doc[field]
                if keep_id and "_id" in doc:
                    projected["_id"] = doc["_id"]
                return projected
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
        docs = []
        for d in self._documents:
            if _match_condition(d, query):
                if projection is None:
                    docs.append(d)
                else:
                    projected = {}
                    keep_id = True
                    for field, spec in projection.items():
                        if field == "_id":
                            keep_id = bool(spec) if isinstance(spec, (int, bool)) else True
                        elif isinstance(spec, (int, bool)) and bool(spec) and field in d:
                            projected[field] = d[field]
                    if keep_id and "_id" in d:
                        projected["_id"] = d["_id"]
                    docs.append(projected)
        cursor = MockCursor(docs)
        if sort is not None:
            if isinstance(sort, list) and len(sort) > 0:
                cursor.sort(sort)
            elif isinstance(sort, str):
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

    async def estimated_document_count(self) -> int:
        return len(self._documents)

    async def update_one(self, query: dict, update: dict) -> Any:
        matched = 0
        modified = 0
        for doc in self._documents:
            if _match_condition(doc, query):
                matched = 1
                if "$set" in update:
                    for k, v in update["$set"].items():
                        doc[k] = v
                    modified = 1
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        if k in doc and isinstance(doc[k], (int, float)) and isinstance(v, (int, float)):
                            doc[k] += v
                            modified = 1
                if "$unset" in update:
                    for k in update["$unset"]:
                        if k in doc:
                            del doc[k]
                            modified = 1
                if "$push" in update:
                    for k, v in update["$push"].items():
                        if k in doc and isinstance(doc[k], list):
                            doc[k].append(v)
                            modified = 1
                break
        return type("UpdateResult", (), {"matched_count": matched, "modified_count": modified})()

    async def update_many(self, query: dict, update: dict) -> Any:
        matched = 0
        modified = 0
        for doc in self._documents:
            if _match_condition(doc, query):
                matched += 1
                if "$set" in update:
                    for k, v in update["$set"].items():
                        doc[k] = v
                    modified += 1
        return type("UpdateResult", (), {"matched_count": matched, "modified_count": modified})()

    async def delete_one(self, query: dict) -> Any:
        deleted = 0
        for i, doc in enumerate(self._documents):
            if _match_condition(doc, query):
                del self._documents[i]
                deleted = 1
                break
        return type("DeleteResult", (), {"deleted_count": deleted})()

    async def delete_many(self, query: dict) -> Any:
        original_len = len(self._documents)
        self._documents = [d for d in self._documents if not _match_condition(d, query)]
        deleted = original_len - len(self._documents)
        return type("DeleteResult", (), {"deleted_count": deleted})()

    async def find_one_and_update(self, query: dict, update: dict, return_document: bool = False) -> Optional[dict]:
        result = await self.update_one(query, update)
        if result.matched_count > 0:
            doc = await self.find_one(query)
            return doc
        return None

    async def find_one_and_delete(self, query: dict) -> Optional[dict]:
        doc = await self.find_one(query)
        if doc:
            await self.delete_one(query)
        return doc

    async def replace_one(self, query: dict, replacement: dict) -> Any:
        matched = 0
        modified = 0
        for i, doc in enumerate(self._documents):
            if _match_condition(doc, query):
                matched = 1
                orig_id = doc.get("_id")
                new_doc = deepcopy(replacement)
                if orig_id is not None and "_id" not in new_doc:
                    new_doc["_id"] = orig_id
                self._documents[i] = new_doc
                modified = 1
                break
        return type("UpdateResult", (), {"matched_count": matched, "modified_count": modified})()

    def aggregate(self, pipeline: List[dict]) -> MockAggregationCursor:
        results = _run_aggregation(self._documents, pipeline)
        return MockAggregationCursor(results)

    async def distinct(self, field: str, query: dict = None) -> List[Any]:
        if query is None:
            query = {}
        values = set()
        for d in self._documents:
            if _match_condition(d, query):
                if field in d:
                    values.add(d[field])
        return list(values)

    async def create_index(self, keys: Any, unique: bool = False, name: str = None) -> str:
        return name or str(keys)

    def index_information(self) -> dict:
        return {}


class MockMongoDatabase:
    def __init__(self):
        self._collections: Dict[str, MockCollection] = {}

    def __getitem__(self, name: str) -> MockCollection:
        if name not in self._collections:
            self._collections[name] = MockCollection()
        return self._collections[name]

    def __getattr__(self, name: str) -> MockCollection:
        return self[name]

    async def list_collection_names(self) -> List[str]:
        return list(self._collections.keys())

    async def create_collection(self, name: str, **kwargs) -> MockCollection:
        if name not in self._collections:
            self._collections[name] = MockCollection()
        return self._collections[name]

    async def drop_collection(self, name_or_coll: Any):
        name = name_or_coll if isinstance(name_or_coll, str) else getattr(name_or_coll, "name", str(name_or_coll))
        if name in self._collections:
            del self._collections[name]

    async def command(self, *args, **kwargs) -> dict:
        if args and args[0] == "ping":
            return {"ok": 1.0}
        return {"ok": 1.0}


class MockMongoClient:
    def __init__(self, *args, **kwargs):
        self._databases: Dict[str, MockMongoDatabase] = {}
        self.admin = MockMongoDatabase()

    def __getitem__(self, name: str) -> MockMongoDatabase:
        if name not in self._databases:
            self._databases[name] = MockMongoDatabase()
        return self._databases[name]

    def __getattr__(self, name: str) -> MockMongoDatabase:
        return self[name]

    def close(self):
        pass

    async def server_info(self) -> dict:
        return {"version": "5.0.0-mock"}
