"""Tests for PCEM CWF Calculator module."""

import pytest
from pcem.calculator.cwf_calculator import (
    calculate_carbon_footprint,
    calculate_water_footprint,
    calculate_cwf,
    get_region_factors,
)


class TestRegionFactors:
    def test_known_region(self):
        factors = get_region_factors("eu-north-1")
        assert factors["carbon_intensity_g_kwh"] == 45

    def test_unknown_region_returns_global(self):
        factors = get_region_factors("nonexistent-region")
        assert factors["carbon_intensity_g_kwh"] == 436  # global average

    def test_india_high_carbon(self):
        factors = get_region_factors("ap-south-1")
        assert factors["carbon_intensity_g_kwh"] > 700


class TestCarbonFootprint:
    def test_basic_calculation(self):
        carbon = calculate_carbon_footprint(1.0, "eu-north-1")
        assert carbon == pytest.approx(45.0, rel=0.01)

    def test_zero_energy(self):
        carbon = calculate_carbon_footprint(0.0, "ap-south-1")
        assert carbon == 0.0

    def test_india_worse_than_sweden(self):
        india = calculate_carbon_footprint(1.0, "ap-south-1")
        sweden = calculate_carbon_footprint(1.0, "eu-north-1")
        assert india > sweden * 10  # India should be 15x worse


class TestWaterFootprint:
    def test_basic_calculation(self):
        water = calculate_water_footprint(1.0, "global_average")
        assert water == pytest.approx(1.8, rel=0.01)

    def test_zero_energy(self):
        water = calculate_water_footprint(0.0, "us-east-1")
        assert water == 0.0


class TestCWF:
    def test_returns_all_fields(self):
        result = calculate_cwf(0.5, "us-west-2")
        assert "energy_kwh" in result
        assert "carbon_g" in result
        assert "water_l" in result
        assert "region" in result
        assert result["energy_kwh"] == 0.5
        assert result["region"] == "us-west-2"

    def test_values_positive(self):
        result = calculate_cwf(1.0, "eu-central-1")
        assert result["carbon_g"] > 0
        assert result["water_l"] > 0
