"""
Carbon Offset Calculator

Calculates the amount and cost of carbon offsets needed
when carbon budgets cannot be met through green routing.
"""

from typing import Dict, Any


# Offset pricing (USD per tonne CO2)
OFFSET_PRICES = {
    "verified_carbon_standard": 15.00,  # VCS - High quality
    "gold_standard": 18.00,             # Gold Standard - Premium
    "american_carbon_registry": 12.00,  # ACR
    "climate_action_reserve": 14.00,    # CAR
    "simulation": 10.00                 # For testing
}

# Default provider
DEFAULT_PROVIDER = "simulation"


def calculate_offset_needed(
    predicted_carbon_g: float,
    budget_g: float
) -> float:
    """
    Calculate how much carbon offset is needed.
    
    Args:
        predicted_carbon_g: Predicted carbon emissions in grams
        budget_g: Carbon budget in grams
    
    Returns:
        Offset amount needed in grams (0 if within budget)
    """
    if predicted_carbon_g <= budget_g:
        return 0.0
    return predicted_carbon_g - budget_g


def calculate_offset_cost(
    offset_g: float,
    provider: str = DEFAULT_PROVIDER
) -> Dict[str, Any]:
    """
    Calculate the cost of purchasing carbon offsets.
    
    Args:
        offset_g: Amount to offset in grams
        provider: Offset provider name
    
    Returns:
        Dict with cost breakdown
    """
    if offset_g <= 0:
        return {
            "offset_g": 0,
            "offset_tonnes": 0,
            "cost_usd": 0,
            "provider": provider,
            "price_per_tonne": 0
        }
    
    # Convert grams to tonnes
    offset_tonnes = offset_g / 1_000_000
    
    # Get price per tonne
    price_per_tonne = OFFSET_PRICES.get(provider, OFFSET_PRICES["simulation"])
    
    # Calculate cost
    cost_usd = offset_tonnes * price_per_tonne
    
    return {
        "offset_g": round(offset_g, 2),
        "offset_tonnes": round(offset_tonnes, 8),
        "cost_usd": round(cost_usd, 6),
        "provider": provider,
        "price_per_tonne": price_per_tonne
    }


def get_offset_recommendation(
    predicted_carbon_g: float,
    budget_g: float,
    allow_offset: bool = True
) -> Dict[str, Any]:
    """
    Get a complete offset recommendation.
    
    Args:
        predicted_carbon_g: Predicted carbon in grams
        budget_g: Budget in grams
        allow_offset: Whether offsets are allowed
    
    Returns:
        Complete recommendation with offset details
    """
    offset_needed = calculate_offset_needed(predicted_carbon_g, budget_g)
    
    if offset_needed == 0:
        return {
            "status": "WITHIN_BUDGET",
            "predicted_carbon_g": round(predicted_carbon_g, 2),
            "budget_g": budget_g,
            "offset_needed_g": 0,
            "offset_cost_usd": 0,
            "recommendation": "No offset needed - task is within carbon budget."
        }
    
    if not allow_offset:
        return {
            "status": "OVER_BUDGET_NO_OFFSET",
            "predicted_carbon_g": round(predicted_carbon_g, 2),
            "budget_g": budget_g,
            "offset_needed_g": round(offset_needed, 2),
            "offset_cost_usd": 0,
            "recommendation": "Task exceeds budget and offsets are disabled. Consider a greener server or waiting for a green window."
        }
    
    # Calculate offset cost for different providers
    providers_comparison = {}
    for provider, price in OFFSET_PRICES.items():
        cost_info = calculate_offset_cost(offset_needed, provider)
        providers_comparison[provider] = cost_info["cost_usd"]
    
    # Get recommended (cheapest) provider
    cheapest = min(providers_comparison, key=providers_comparison.get)
    cheapest_cost = calculate_offset_cost(offset_needed, cheapest)
    
    return {
        "status": "OFFSET_RECOMMENDED",
        "predicted_carbon_g": round(predicted_carbon_g, 2),
        "budget_g": budget_g,
        "offset_needed_g": round(offset_needed, 2),
        "offset_cost_usd": cheapest_cost["cost_usd"],
        "recommended_provider": cheapest,
        "all_providers": providers_comparison,
        "recommendation": f"Purchase {offset_needed:.2f}g CO2 offset for ${cheapest_cost['cost_usd']:.6f} via {cheapest}."
    }


# Example usage
if __name__ == "__main__":
    print("Offset Calculator Examples")
    print("=" * 60)
    
    scenarios = [
        (5.0, 10.0),   # Within budget
        (15.0, 10.0),  # 5g over budget
        (100.0, 50.0), # 50g over budget
    ]
    
    for predicted, budget in scenarios:
        print(f"\nScenario: Predicted={predicted}g, Budget={budget}g")
        result = get_offset_recommendation(predicted, budget)
        print(f"  Status: {result['status']}")
        print(f"  Offset Needed: {result['offset_needed_g']}g")
        print(f"  Cost: ${result['offset_cost_usd']:.6f}")
        print(f"  Recommendation: {result['recommendation']}")
