"""
Carbon and Water Footprint (CWF) Calculator

Calculates carbon emissions (gCO2) and water usage (L) from energy consumption (kWh).
"""

import json
from pathlib import Path
from typing import Optional

# Load fallback factors on module import
DATA_DIR = Path(__file__).parent.parent / "data"
FALLBACK_FACTORS_PATH = DATA_DIR / "fallback_factors.json"


def load_fallback_factors() -> dict:
    """Load fallback carbon intensity factors from JSON file."""
    if FALLBACK_FACTORS_PATH.exists():
        with open(FALLBACK_FACTORS_PATH, "r") as f:
            return json.load(f)
    return {"regions": {"global_average": {"carbon_intensity_g_kwh": 436, "water_factor_l_kwh": 1.8}}}


FACTORS = load_fallback_factors()


def get_region_factors(region: str) -> dict:
    """
    Get carbon intensity and water factors for a given region.
    
    Args:
        region: Cloud region identifier (e.g., 'us-east-1', 'ap-south-1')
    
    Returns:
        Dict with carbon_intensity_g_kwh and water_factor_l_kwh
    """
    regions = FACTORS.get("regions", {})
    if region in regions:
        return regions[region]
    return regions.get("global_average", {"carbon_intensity_g_kwh": 436, "water_factor_l_kwh": 1.8})


def calculate_carbon_footprint(energy_kwh: float, region: str = "global_average") -> float:
    """
    Calculate carbon footprint from energy consumption.
    
    Args:
        energy_kwh: Energy consumption in kilowatt-hours
        region: Cloud region identifier
    
    Returns:
        Carbon emissions in grams of CO2
    """
    factors = get_region_factors(region)
    carbon_intensity = factors.get("carbon_intensity_g_kwh", 436)
    return energy_kwh * carbon_intensity


def calculate_water_footprint(energy_kwh: float, region: str = "global_average") -> float:
    """
    Calculate water footprint from energy consumption.
    
    Args:
        energy_kwh: Energy consumption in kilowatt-hours
        region: Cloud region identifier
    
    Returns:
        Water usage in liters
    """
    factors = get_region_factors(region)
    water_factor = factors.get("water_factor_l_kwh", 1.8)
    return energy_kwh * water_factor


def calculate_cwf(energy_kwh: float, region: str = "global_average") -> dict:
    """
    Calculate both carbon and water footprint.
    
    Args:
        energy_kwh: Energy consumption in kilowatt-hours
        region: Cloud region identifier
    
    Returns:
        Dict with carbon_g and water_l
    """
    return {
        "energy_kwh": energy_kwh,
        "carbon_g": round(calculate_carbon_footprint(energy_kwh, region), 2),
        "water_l": round(calculate_water_footprint(energy_kwh, region), 2),
        "region": region
    }


# Example usage
if __name__ == "__main__":
    # Test calculation for different regions
    test_energy = 0.5  # kWh
    
    regions_to_test = ["us-east-1", "eu-north-1", "ap-south-1", "global_average"]
    
    print(f"Energy: {test_energy} kWh\n")
    print(f"{'Region':<20} {'Carbon (g)':<15} {'Water (L)':<15}")
    print("-" * 50)
    
    for region in regions_to_test:
        result = calculate_cwf(test_energy, region)
        print(f"{region:<20} {result['carbon_g']:<15} {result['water_l']:<15}")
