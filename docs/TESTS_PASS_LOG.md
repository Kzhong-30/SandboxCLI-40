============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Library/Developer/CommandLineTools/usr/bin/python3
cachedir: .pytest_cache
rootdir: /Users/koillinjag/Desktop/solocoder/52
plugins: asyncio-1.2.0, anyio-3.7.1
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 27 items

tests/test_compare.py::TestCompareExtract::test_empty PASSED             [  3%]
tests/test_compare.py::TestCompareExtract::test_basic PASSED             [  7%]
tests/test_mongo_agg.py::TestMockMongoAggregate::test_group_sum PASSED   [ 11%]
tests/test_mongo_agg.py::TestMockMongoAggregate::test_cond PASSED        [ 14%]
tests/test_mongo_agg.py::TestMockMongoAggregate::test_push PASSED        [ 18%]
tests/test_mongo_agg.py::TestMockMongoAggregate::test_match_group PASSED [ 22%]
tests/test_mongo_agg.py::TestMockMongoAggregate::test_sort_limit_skip PASSED [ 25%]
tests/test_mongo_agg.py::TestMockMongoAggregate::test_sort_asc PASSED    [ 29%]
tests/test_mongo_basic.py::TestMockMongoBasic::test_insert_count PASSED  [ 33%]
tests/test_mongo_basic.py::TestMockMongoBasic::test_find_filter PASSED   [ 37%]
tests/test_mongo_basic.py::TestMockMongoBasic::test_sort_asc PASSED      [ 40%]
tests/test_mongo_basic.py::TestMockMongoBasic::test_sort_desc PASSED     [ 44%]
tests/test_mongo_basic.py::TestMockMongoBasic::test_limit PASSED         [ 48%]
tests/test_mongo_basic.py::TestMockMongoBasic::test_skip PASSED          [ 51%]
tests/test_mongo_basic.py::TestMockMongoBasic::test_sort_limit_skip PASSED [ 55%]
tests/test_mongo_basic.py::TestMockMongoBasic::test_find_one PASSED      [ 59%]
tests/test_sentiment_service.py::TestSentimentService::test_empty_text PASSED [ 62%]
tests/test_sentiment_service.py::TestSentimentService::test_score_range PASSED [ 66%]
tests/test_sentiment_service.py::TestSentimentService::test_english_positive PASSED [ 70%]
tests/test_sentiment_service.py::TestSentimentService::test_english_negative PASSED [ 74%]
tests/test_sentiment_service.py::TestSentimentService::test_contains_chinese PASSED [ 77%]
tests/test_sentiment_service.py::TestSentimentService::test_rule_fallback PASSED [ 81%]
tests/test_sentiment_service.py::TestSentimentService::test_return_type PASSED [ 85%]
tests/test_sentiment_service.py::TestSentimentService::test_whitespace_text PASSED [ 88%]
tests/test_sentiment_service.py::TestSentimentService::test_very_long_text PASSED [ 92%]
tests/test_short.py::test_one PASSED                                     [ 96%]
tests/test_short.py::test_two PASSED                                     [100%]

=============================== warnings summary ===============================
../../../Library/Python/3.9/lib/python/site-packages/pydantic/_internal/_config.py:284
  /Users/koillinjag/Library/Python/3.9/lib/python/site-packages/pydantic/_internal/_config.py:284: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.7/migration/
    warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning)

../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:64
  /Users/koillinjag/Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:64: PyparsingDeprecationWarning: 'oneOf' deprecated - use 'one_of'
    prop = Group((name + Suppress("=") + comma_separated(value)) | oneOf(_CONSTANTS))

../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85
  /Users/koillinjag/Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:85: PyparsingDeprecationWarning: 'parseString' deprecated - use 'parse_string'
    parse = parser.parseString(pattern)

../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
../../../Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89
  /Users/koillinjag/Library/Python/3.9/lib/python/site-packages/matplotlib/_fontconfig_pattern.py:89: PyparsingDeprecationWarning: 'resetCache' deprecated - use 'reset_cache'
    parser.resetCache()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 27 passed, 14 warnings in 2.65s ========================
