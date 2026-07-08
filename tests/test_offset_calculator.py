"""Tests for Offset Calculator module."""

import pytest
from offsets.calculator import (
    calculate_offset_needed,
    calculate_offset_cost,
    get_offset_recommendation,
)


class TestCalculateOffsetNeeded:
    def test_within_budget(self):
        assert calculate_offset_needed(5.0, 10.0) == 0.0

    def test_exactly_at_budget(self):
        assert calculate_offset_needed(10.0, 10.0) == 0.0

    def test_over_budget(self):
        assert calculate_offset_needed(15.0, 10.0) == 5.0


class TestCalculateOffsetCost:
    def test_zero_offset(self):
        result = calculate_offset_cost(0)
        assert result["cost_usd"] == 0

    def test_positive_offset(self):
        result = calculate_offset_cost(1000.0, "simulation")
        assert result["cost_usd"] > 0
        assert result["provider"] == "simulation"

    def test_result_has_required_fields(self):
        result = calculate_offset_cost(100.0)
        assert "offset_g" in result
        assert "offset_tonnes" in result
        assert "cost_usd" in result
        assert "provider" in result


class TestGetOffsetRecommendation:
    def test_within_budget(self):
        result = get_offset_recommendation(5.0, 10.0)
        assert result["status"] == "WITHIN_BUDGET"
        assert result["offset_needed_g"] == 0

    def test_over_budget_with_offset(self):
        result = get_offset_recommendation(15.0, 10.0)
        assert result["status"] == "OFFSET_RECOMMENDED"
        assert result["offset_needed_g"] == 5.0
        assert result["offset_cost_usd"] > 0
        assert "recommended_provider" in result

    def test_over_budget_no_offset(self):
        result = get_offset_recommendation(15.0, 10.0, allow_offset=False)
        assert result["status"] == "OVER_BUDGET_NO_OFFSET"

    def test_all_providers_compared(self):
        result = get_offset_recommendation(20.0, 10.0)
        assert "all_providers" in result
        assert len(result["all_providers"]) > 0
