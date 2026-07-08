"""
Smart Router - Self-Adaptive Carbon-Aware Server Selection

Selects the optimal server for AI inference using a multi-objective
scoring function that LEARNS from historical routing outcomes.

Scoring combines:
- Static urgency-based weights (user preference)
- Adaptive weight adjustments (learned from prediction errors)
- Thompson Sampling exploration bonus (Bayesian bandit)

Over time, the router improves its decisions by tracking
predicted vs actual carbon/latency for each server.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from pcem.monitor.carbon_monitor import get_current_carbon_data, get_region_carbon
from pcem.router.adaptive_learner import adaptive_learner


DATA_DIR = Path(__file__).parent.parent / "data"
SERVERS_PATH = DATA_DIR / "servers.json"


def load_servers() -> List[Dict]:
    """Load available GPU servers from JSON file."""
    if SERVERS_PATH.exists():
        with open(SERVERS_PATH, "r") as f:
            data = json.load(f)
            return data.get("servers", [])
    return []


def get_available_servers() -> List[Dict]:
    """Get list of all available GPU servers with current carbon data."""
    servers = load_servers()
    carbon_data = get_current_carbon_data()
    
    enriched_servers = []
    for server in servers:
        region = server.get("region")
        region_carbon = carbon_data.get("regions", {}).get(region, {})
        
        enriched_servers.append({
            **server,
            "carbon_intensity": region_carbon.get("carbon_intensity_g_kwh", 500),
            "renewable_pct": region_carbon.get("renewable_pct", 0),
            "energy_mix": region_carbon.get("energy_mix", {})
        })
    
    return enriched_servers


def calculate_server_score(
    server: Dict,
    task_analysis: Dict,
    preferences: Dict
) -> float:
    """
    Calculate a score for a server (lower is better).
    
    Three-layer scoring system:
    
    Layer 1 — Urgency-Based Weights:
      Static presets based on user urgency (1-5)
    
    Layer 2 — Adaptive Weight Adjustment:
      Learned adjustments based on historical prediction errors.
      If carbon is consistently under-predicted, carbon weight increases.
    
    Layer 3 — Thompson Sampling Exploration Bonus:
      Bayesian bandit term that encourages trying under-explored servers
      while favoring servers with proven good performance.
    
    Final Score = Σ(adapted_weights × factors) + exploration_bonus
    """
    # Get urgency level (1-5, default 3 = balanced)
    urgency = preferences.get("urgency", 3)
    urgency = max(1, min(5, int(urgency)))

    # Layer 1 + 2: Get adapted weights (base urgency + learned adjustments)
    weights = adaptive_learner.get_adaptive_weights(urgency)
    
    # Normalize factors to 0-1 scale
    carbon_norm = server.get("carbon_intensity", 500) / 1000  # Max ~1000 g/kWh
    renewable_norm = 1 - server.get("renewable_pct", 0)  # Invert (higher is better)
    latency_norm = server.get("latency_ms", 200) / 1000  # Max ~1000ms
    cost_norm = server.get("cost_per_hour", 1.0) / 10  # Max ~$10/hour
    
    # Weighted sum with adapted weights
    base_score = (
        weights["carbon"] * carbon_norm +
        weights["renewable"] * renewable_norm +
        weights["latency"] * latency_norm +
        weights["cost"] * cost_norm
    )

    # Layer 3: Thompson Sampling exploration bonus
    region = server.get("region", "unknown")
    exploration_bonus = adaptive_learner.get_exploration_bonus(region, urgency)
    
    score = base_score + exploration_bonus
    
    return round(score, 4)


def select_best_server(
    task_analysis: Dict,
    carbon_data: Dict,
    carbon_budget_g: float = 100.0,
    preferences: Dict = None
) -> Dict[str, Any]:
    """
    Select the best server for the given task.
    
    Args:
        task_analysis: Output from task_analyzer.analyze_task()
        carbon_data: Current carbon data from carbon_monitor
        carbon_budget_g: Maximum allowed carbon in grams
        preferences: User preferences (prioritize, min_renewable_pct, etc.)
    
    Returns:
        Dict with selected server, predicted carbon, alternatives, etc.
    """
    if preferences is None:
        preferences = {}
    
    servers = get_available_servers()
    
    if not servers:
        # Return a default if no servers configured
        return {
            "selected_server": {
                "name": "default-server",
                "region": "us-east-1",
                "carbon_intensity": 400,
                "renewable_pct": 0.3,
                "energy_mix": {},
                "latency_ms": 100
            },
            "predicted_carbon_g": task_analysis["estimated_energy_kwh"] * 400,
            "carbon_saved_vs_default": 0,
            "alternatives": []
        }
    
    # Filter by minimum renewable percentage if specified
    min_renewable = preferences.get("min_renewable_pct", 0)
    eligible_servers = [s for s in servers if s.get("renewable_pct", 0) >= min_renewable]
    
    if not eligible_servers:
        eligible_servers = servers  # Fall back to all servers
    
    # Score each server
    scored_servers = []
    for server in eligible_servers:
        score = calculate_server_score(server, task_analysis, preferences)
        energy_kwh = task_analysis["estimated_energy_kwh"]
        predicted_carbon = energy_kwh * server.get("carbon_intensity", 500)
        
        scored_servers.append({
            **server,
            "score": score,
            "predicted_carbon_g": round(predicted_carbon, 2)
        })
    
    # Sort by score (lower is better)
    scored_servers.sort(key=lambda x: x["score"])
    
    # Select best server
    best_server = scored_servers[0]
    
    # Calculate carbon savings vs default (highest carbon option)
    worst_carbon = max(s["predicted_carbon_g"] for s in scored_servers)
    carbon_saved = worst_carbon - best_server["predicted_carbon_g"]
    
    # Get alternatives (next 2 best options)
    alternatives = [
        {
            "name": s["name"],
            "region": s["region"],
            "predicted_carbon_g": s["predicted_carbon_g"],
            "renewable_pct": s.get("renewable_pct", 0)
        }
        for s in scored_servers[1:3]
    ]
    
    return {
        "selected_server": {
            "name": best_server["name"],
            "region": best_server["region"],
            "provider": best_server.get("provider", "unknown"),
            "carbon_intensity": best_server.get("carbon_intensity"),
            "renewable_pct": best_server.get("renewable_pct", 0),
            "energy_mix": best_server.get("energy_mix", {}),
            "latency_ms": best_server.get("latency_ms", 100),
            "cost_per_hour": best_server.get("cost_per_hour", 1.0),
            "score": best_server["score"]
        },
        "predicted_carbon_g": best_server["predicted_carbon_g"],
        "carbon_saved_vs_default": round(carbon_saved, 2),
        "alternatives": alternatives,
        "servers_evaluated": len(scored_servers)
    }


# Example usage
if __name__ == "__main__":
    from pcem.analyzer.task_analyzer import analyze_task
    
    # Example task
    task = analyze_task("Write a summary of climate change impacts on agriculture.", "gpt-4")
    
    print("Smart Router - Server Selection")
    print("=" * 60)
    print(f"\nTask: {task['total_tokens']} tokens, {task['estimated_energy_kwh']} kWh")
    
    # Get current carbon data
    carbon_data = get_current_carbon_data()
    
    # Select best server
    result = select_best_server(task, carbon_data, carbon_budget_g=10.0)
    
    print(f"\n✅ Selected Server: {result['selected_server']['name']}")
    print(f"   Region: {result['selected_server']['region']}")
    print(f"   Carbon Intensity: {result['selected_server']['carbon_intensity']} g/kWh")
    print(f"   Renewable: {result['selected_server']['renewable_pct']*100:.1f}%")
    print(f"   Predicted Carbon: {result['predicted_carbon_g']}g CO2")
    print(f"   Carbon Saved: {result['carbon_saved_vs_default']}g")
    
    if result['alternatives']:
        print("\n📋 Alternatives:")
        for alt in result['alternatives']:
            print(f"   - {alt['name']}: {alt['predicted_carbon_g']}g CO2")
