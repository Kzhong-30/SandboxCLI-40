import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.comparison_service import ComparisonService

class TestCompareExtract:
    def test_empty(self):
        r = ComparisonService.extract_keywords("", top_n=10)
        assert len(r) == 0

    def test_basic(self):
        r = ComparisonService.extract_keywords("apple apple banana", top_n=5)
        assert len(r) > 0

