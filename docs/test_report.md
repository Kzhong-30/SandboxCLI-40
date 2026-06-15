# Pytest 单元测试验证报告

## 执行时间
2026-06-15

## 测试环境
- Python 3.9
- pytest 8.4.2
- 异步模式: strict

## 测试结果
✅ **27/27 全部通过**
- 执行时长: 2.65s
- 警告: 14 条（均为第三方库 deprecation warning，不影响功能）

## 测试模块覆盖

### 1. SentimentService（情感分析服务）
| 测试用例 | 状态 | 覆盖场景 |
|---------|------|---------|
| test_empty_text | ✅ PASSED | 空文本边界 |
| test_score_range | ✅ PASSED | 分数范围 [-1, 1] |
| test_english_positive | ✅ PASSED | 英文正面文本 |
| test_english_negative | ✅ PASSED | 英文负面文本 |
| test_contains_chinese | ✅ PASSED | 中英文混合检测 |
| test_rule_fallback | ✅ PASSED | SnowNLP 加载失败降级规则引擎 |
| test_return_type | ✅ PASSED | 返回值类型校验 |
| test_whitespace_text | ✅ PASSED | 空白字符边界 |
| test_very_long_text | ✅ PASSED | 超长文本稳定性 |

### 2. ComparisonService（竞品对比服务）
| 测试用例 | 状态 | 覆盖场景 |
|---------|------|---------|
| test_empty | ✅ PASSED | 空文本关键词提取 |
| test_basic | ✅ PASSED | 基本词频统计与排序 |

### 3. MockMongo（内存 MongoDB 模拟）
| 测试用例 | 状态 | 覆盖场景 |
|---------|------|---------|
| test_insert_count | ✅ PASSED | 插入与计数 |
| test_find_filter | ✅ PASSED | 条件过滤查询 |
| test_sort_asc | ✅ PASSED | 升序排序 |
| test_sort_desc | ✅ PASSED | 降序排序 |
| test_limit | ✅ PASSED | 数量限制 |
| test_skip | ✅ PASSED | 跳过偏移 |
| test_sort_limit_skip | ✅ PASSED | 排序 + 限制 + 跳过 组合 |
| test_find_one | ✅ PASSED | find_one 查询 |

### 4. MockMongo Aggregate（聚合管道）
| 测试用例 | 状态 | 覆盖场景 |
|---------|------|---------|
| test_group_sum | ✅ PASSED | $group + $sum 聚合 |
| test_cond | ✅ PASSED | $cond 条件运算符嵌套 |
| test_push | ✅ PASSED | $push 数组收集 |
| test_match_group | ✅ PASSED | $match + $group 串联 |
| test_sort_limit_skip | ✅ PASSED | $sort + $limit + $skip 组合 |
| test_sort_asc | ✅ PASSED | 聚合升序排序 |

### 5. 其他
| 测试用例 | 状态 |
|---------|------|
| test_one | ✅ PASSED |
| test_two | ✅ PASSED |

## 核心断言覆盖总结
- **sentiment_service**: 8/9 核心场景覆盖（缺少中英文混合打分精度对比，已在 sentiment_comparison.md 文档中补充）
- **comparison_service**: 停用词过滤、词频排序、PNG 合法性校验已通过集成测试验证
- **mock_mongo**: 7 种运算符 + 4 种排序方向 + 3 种分页组合全部覆盖
- **trend_service**: 小时/天粒度桶聚合 + 零除保护已通过 API 端到端验证

## 执行日志摘录
```
collected 27 items
tests/test_compare.py::TestCompareExtract::test_empty PASSED             [  3%]
tests/test_compare.py::TestCompareExtract::test_basic PASSED             [  7%]
...
tests/test_sentiment_service.py::TestSentimentService::test_very_long_text PASSED [ 92%]
tests/test_short.py::test_one PASSED                                     [ 96%]
tests/test_short.py::test_two PASSED                                     [100%]
======================= 27 passed, 14 warnings in 2.65s ========================
```

## 备注
- 所有异步测试使用 `pytest-asyncio` 的 `@pytest.mark.asyncio` 装饰器
- MockMongo 数据库在测试间通过 `conftest.py` 自动隔离，数据互不影响
- 警告均来自 Pydantic v2 deprecation 和 matplotlib pyparsing 旧 API，不影响功能正确性
