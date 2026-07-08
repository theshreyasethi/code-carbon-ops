"""
Carbon Monitor - Real-Time Global Carbon Intensity Tracking

Monitors carbon intensity and energy mix data from:
- ElectricityMaps API (real-time, requires API key)
- UK Carbon Intensity API (free, no key needed)
- Fallback to static data when APIs unavailable
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import random  # For simulation fallback

# Path to fallback data
DATA_DIR = Path(__file__).parent.parent / "data"
FALLBACK_FACTORS_PATH = DATA_DIR / "fallback_factors.json"
SERVERS_PATH = DATA_DIR / "servers.json"


def load_fallback_factors() -> Dict:
    """Load fallback carbon intensity data."""
    if FALLBACK_FACTORS_PATH.exists():
        with open(FALLBACK_FACTORS_PATH, "r") as f:
            return json.load(f)
    return {}


def load_servers() -> List[Dict]:
    """Load available GPU servers."""
    if SERVERS_PATH.exists():
        with open(SERVERS_PATH, "r") as f:
            return json.load(f)
    return []


# Cache for carbon data
_carbon_cache = {}
_cache_timestamp = None
CACHE_TTL_SECONDS = 900  # 15 minutes


# ============== Real API Integration ==============

# Region mapping: our region IDs → ElectricityMaps zone codes
REGION_TO_ZONE = {
    "us-east-1": "US-MIDA-PJM",
    "us-west-2": "US-NW-PACW",
    "eu-west-1": "IE",
    "eu-north-1": "SE-SE3",
    "eu-central-1": "DE",
    "ap-south-1": "IN-WE",
    "ap-southeast-1": "SG",
    "ap-northeast-1": "JP-TK",
    "ap-east-1": "HK",
    "sa-east-1": "BR-S",
    "me-south-1": "BH",
    "af-south-1": "ZA",
    "ca-central-1": "CA-ON",
    "uk-south": "GB",
    "australia-east": "AU-NSW",
}


def fetch_electricity_maps_data(zone: str) -> Optional[Dict]:
    """
    Fetch real-time data from ElectricityMaps API.
    
    Requires API key in environment variable ELECTRICITY_MAPS_API_KEY.
    Free tier: 100 requests/month.
    
    Args:
        zone: ElectricityMaps zone code (e.g., "SE-SE3" for Sweden)
    
    Returns:
        Dict with carbon_intensity and power_breakdown, or None if unavailable.
    """
    api_key = os.environ.get("ELECTRICITY_MAPS_API_KEY", "")
    if not api_key:
        return None
    
    try:
        import httpx
        
        # Get carbon intensity
        response = httpx.get(
            f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={zone}",
            headers={"auth-token": api_key},
            timeout=10.0
        )
        
        if response.status_code != 200:
            return None
        
        intensity_data = response.json()
        
        # Get power breakdown (energy mix)
        power_response = httpx.get(
            f"https://api.electricitymap.org/v3/power-breakdown/latest?zone={zone}",
            headers={"auth-token": api_key},
            timeout=10.0
        )
        
        power_data = power_response.json() if power_response.status_code == 200 else {}
        
        # Parse power breakdown into energy mix percentages
        energy_mix = {}
        power_consumption = power_data.get("powerConsumptionBreakdown", {})
        total_power = power_data.get("powerConsumptionTotal", 1)
        
        if total_power and total_power > 0:
            for source in ["solar", "wind", "hydro", "nuclear", "gas", "coal", "oil", "biomass", "geothermal"]:
                value = power_consumption.get(source, 0)
                if value and value > 0:
                    energy_mix[source] = round(value / total_power, 3)
        
        return {
            "carbon_intensity_g_kwh": intensity_data.get("carbonIntensity", None),
            "energy_mix": energy_mix,
            "source": "electricitymaps",
            "zone": zone,
            "updated_at": intensity_data.get("datetime", datetime.now().isoformat())
        }
    
    except Exception as e:
        print(f"⚠️ ElectricityMaps API error for {zone}: {e}")
        return None


def fetch_uk_carbon_data() -> Optional[Dict]:
    """
    Fetch real-time carbon data from UK Carbon Intensity API.
    
    Free API, no key required.
    Docs: https://carbon-intensity.github.io/api-definitions/
    
    Returns:
        Dict with UK carbon intensity and fuel mix, or None if unavailable.
    """
    try:
        import httpx
        
        # Get current intensity
        response = httpx.get(
            "https://api.carbonintensity.org.uk/intensity",
            timeout=10.0
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        intensity_data = data.get("data", [{}])[0]
        intensity = intensity_data.get("intensity", {})
        
        # Get fuel mix
        mix_response = httpx.get(
            "https://api.carbonintensity.org.uk/generation",
            timeout=10.0
        )
        
        energy_mix = {}
        if mix_response.status_code == 200:
            mix_data = mix_response.json()
            gen_mix = mix_data.get("data", {}).get("generationmix", [])
            for item in gen_mix:
                fuel = item.get("fuel", "").lower()
                perc = item.get("perc", 0) / 100  # Convert to fraction
                
                # Map UK fuel names to our standard names
                fuel_mapping = {
                    "gas": "gas", "coal": "coal", "nuclear": "nuclear",
                    "wind": "wind", "solar": "solar", "hydro": "hydro",
                    "biomass": "biomass", "imports": "imports", "other": "other"
                }
                mapped_fuel = fuel_mapping.get(fuel, fuel)
                if perc > 0:
                    energy_mix[mapped_fuel] = round(perc, 3)
        
        return {
            "carbon_intensity_g_kwh": intensity.get("actual") or intensity.get("forecast"),
            "energy_mix": energy_mix,
            "source": "uk_carbon_intensity_api",
            "zone": "GB",
            "index": intensity.get("index", "unknown")  # very low, low, moderate, high, very high
        }
    
    except Exception as e:
        print(f"⚠️ UK Carbon API error: {e}")
        return None


# ============== Simulation Fallback ==============

def simulate_realtime_carbon_data(base_data: Dict) -> Dict:
    """
    Simulate real-time variations in carbon data.
    Used when real APIs are unavailable.
    """
    hour = datetime.now().hour
    solar_factor = max(0, min(1, 1 - abs(hour - 12) / 12))
    
    simulated = {}
    for region, data in base_data.get("regions", {}).items():
        base_intensity = data.get("carbon_intensity_g_kwh", 400)
        
        variation = random.uniform(-0.1, 0.1)
        current_intensity = base_intensity * (1 + variation)
        
        energy_mix = simulate_energy_mix(region, solar_factor)
        renewable_pct = sum([
            energy_mix.get("solar", 0),
            energy_mix.get("wind", 0),
            energy_mix.get("hydro", 0),
            energy_mix.get("nuclear", 0)
        ])
        
        simulated[region] = {
            "carbon_intensity_g_kwh": round(current_intensity, 1),
            "renewable_pct": round(renewable_pct, 2),
            "energy_mix": energy_mix,
            "timestamp": datetime.now().isoformat(),
            "region_name": data.get("region_name", region),
            "country": data.get("country", "Unknown")
        }
    
    return simulated


def simulate_energy_mix(region: str, solar_factor: float) -> Dict[str, float]:
    """Simulate energy mix for a region based on typical patterns."""
    region_profiles = {
        "eu-north-1": {"hydro": 0.65, "wind": 0.20, "nuclear": 0.10, "solar": 0.03, "gas": 0.02, "coal": 0.00},
        "us-west-2": {"hydro": 0.35, "wind": 0.30, "solar": 0.15, "gas": 0.15, "nuclear": 0.05, "coal": 0.00},
        "ap-south-1": {"coal": 0.55, "gas": 0.15, "solar": 0.10, "hydro": 0.10, "wind": 0.05, "nuclear": 0.05},
        "default": {"gas": 0.35, "coal": 0.25, "nuclear": 0.15, "hydro": 0.10, "wind": 0.10, "solar": 0.05}
    }
    
    profile = region_profiles.get(region, region_profiles["default"]).copy()
    
    if "solar" in profile:
        base_solar = profile["solar"]
        profile["solar"] = round(base_solar * solar_factor, 3)
        profile["gas"] = round(profile.get("gas", 0) + base_solar * (1 - solar_factor), 3)
    
    return profile


# ============== Main Data Function ==============

def get_current_carbon_data() -> Dict[str, Any]:
    """
    Get current carbon intensity data for all tracked regions.
    
    Priority order:
    1. Try ElectricityMaps API (if API key configured)
    2. Try UK Carbon Intensity API (for UK region, free)
    3. Fall back to simulated data
    """
    global _carbon_cache, _cache_timestamp
    
    # Check cache
    now = datetime.now()
    if _cache_timestamp and (now - _cache_timestamp).total_seconds() < CACHE_TTL_SECONDS:
        return _carbon_cache
    
    # Load fallback data as base
    fallback_data = load_fallback_factors()
    
    # Start with simulated data
    carbon_data = simulate_realtime_carbon_data(fallback_data)
    source = "simulated"
    
    # Try real ElectricityMaps API
    api_key = os.environ.get("ELECTRICITY_MAPS_API_KEY", "")
    if api_key:
        real_data_count = 0
        for region, zone in REGION_TO_ZONE.items():
            real_data = fetch_electricity_maps_data(zone)
            if real_data and real_data.get("carbon_intensity_g_kwh"):
                # Override simulated data with real data
                energy_mix = real_data.get("energy_mix", {})
                renewable_pct = sum([
                    energy_mix.get("solar", 0),
                    energy_mix.get("wind", 0),
                    energy_mix.get("hydro", 0),
                    energy_mix.get("nuclear", 0)
                ])
                
                fallback_region = fallback_data.get("regions", {}).get(region, {})
                carbon_data[region] = {
                    "carbon_intensity_g_kwh": real_data["carbon_intensity_g_kwh"],
                    "renewable_pct": round(renewable_pct, 2),
                    "energy_mix": energy_mix,
                    "timestamp": real_data.get("updated_at", now.isoformat()),
                    "region_name": fallback_region.get("region_name", region),
                    "country": fallback_region.get("country", "Unknown"),
                    "source": "electricitymaps"
                }
                real_data_count += 1
        
        if real_data_count > 0:
            source = f"electricitymaps ({real_data_count} regions live)"
            print(f"🌍 Fetched real carbon data for {real_data_count}/{len(REGION_TO_ZONE)} regions")
    
    # Try UK Carbon API for UK region (free, no key needed)
    uk_data = fetch_uk_carbon_data()
    if uk_data and uk_data.get("carbon_intensity_g_kwh"):
        energy_mix = uk_data.get("energy_mix", {})
        renewable_pct = sum([
            energy_mix.get("solar", 0),
            energy_mix.get("wind", 0),
            energy_mix.get("hydro", 0),
            energy_mix.get("nuclear", 0)
        ])
        
        carbon_data["uk-south"] = {
            "carbon_intensity_g_kwh": uk_data["carbon_intensity_g_kwh"],
            "renewable_pct": round(renewable_pct, 2),
            "energy_mix": energy_mix,
            "timestamp": now.isoformat(),
            "region_name": "UK South",
            "country": "United Kingdom",
            "source": "uk_carbon_intensity_api"
        }
        if source == "simulated":
            source = "simulated + uk_carbon_api"
        print(f"🇬🇧 UK Carbon: {uk_data['carbon_intensity_g_kwh']}g/kWh ({uk_data.get('index', 'unknown')})")
    
    # Update cache
    _carbon_cache = {
        "regions": carbon_data,
        "last_updated": now.isoformat(),
        "source": source,
        "cache_ttl_seconds": CACHE_TTL_SECONDS
    }
    _cache_timestamp = now
    
    return _carbon_cache


# ============== Helper Functions ==============

def get_all_regions() -> List[Dict]:
    """Get list of all available regions with their carbon data."""
    data = get_current_carbon_data()
    regions = []
    
    for region_id, region_data in data.get("regions", {}).items():
        regions.append({
            "id": region_id,
            "name": region_data.get("region_name", region_id),
            "country": region_data.get("country", "Unknown"),
            "carbon_intensity": region_data.get("carbon_intensity_g_kwh"),
            "renewable_pct": region_data.get("renewable_pct"),
            "energy_mix": region_data.get("energy_mix", {})
        })
    
    regions.sort(key=lambda x: x.get("carbon_intensity", 999))
    return regions


def get_greenest_regions(count: int = 5) -> List[Dict]:
    """Get the top N greenest regions currently."""
    all_regions = get_all_regions()
    return all_regions[:count]


def get_region_carbon(region: str) -> Optional[Dict]:
    """Get carbon data for a specific region."""
    data = get_current_carbon_data()
    return data.get("regions", {}).get(region)


# Example usage
if __name__ == "__main__":
    print("Carbon Monitor - Current Data")
    print("=" * 60)
    
    data = get_current_carbon_data()
    print(f"\nLast Updated: {data['last_updated']}")
    print(f"Source: {data['source']}")
    
    print("\n🌍 Top 5 Greenest Regions Right Now:")
    for region in get_greenest_regions(5):
        mix = region.get("energy_mix", {})
        renewable = region.get("renewable_pct", 0) * 100
        print(f"\n  {region['name']} ({region['country']})")
        print(f"    Carbon: {region['carbon_intensity']} g/kWh")
        print(f"    Renewable: {renewable:.1f}%")
        print(f"    Mix: Solar={mix.get('solar',0)*100:.0f}% Wind={mix.get('wind',0)*100:.0f}% Hydro={mix.get('hydro',0)*100:.0f}%")
