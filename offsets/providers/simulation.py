"""
Simulation Offset Provider

A simulated carbon offset provider for testing and development.
In production, this would be replaced with real offset API integrations.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List

# In-memory storage for simulated purchases (would be database in production)
_purchase_history: List[Dict] = []


def purchase_offset(
    amount_g: float,
    run_id: str = None,
    metadata: Dict = None
) -> Dict[str, Any]:
    """
    Simulate purchasing a carbon offset.
    
    Args:
        amount_g: Amount of CO2 to offset in grams
        run_id: Optional ID of the inference run
        metadata: Optional additional metadata
    
    Returns:
        Transaction details
    """
    if amount_g <= 0:
        return {
            "status": "error",
            "message": "Offset amount must be positive"
        }
    
    # Calculate cost (simulation uses $10/tonne)
    cost_usd = (amount_g / 1_000_000) * 10.0
    
    # Generate transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "run_id": run_id,
        "amount_g": round(amount_g, 2),
        "amount_tonnes": round(amount_g / 1_000_000, 8),
        "cost_usd": round(cost_usd, 6),
        "provider": "simulation",
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {},
        "certificate": generate_certificate_id()
    }
    
    # Store in history
    _purchase_history.append(transaction)
    
    return {
        "status": "success",
        "transaction": transaction
    }


def generate_certificate_id() -> str:
    """Generate a simulated offset certificate ID."""
    return f"SIM-CERT-{uuid.uuid4().hex[:12].upper()}"


def get_purchase_history() -> List[Dict]:
    """Get all simulated purchase history."""
    return _purchase_history


def get_total_offset() -> Dict[str, Any]:
    """Get total offsets purchased."""
    total_g = sum(p["amount_g"] for p in _purchase_history)
    total_cost = sum(p["cost_usd"] for p in _purchase_history)
    
    return {
        "total_offset_g": round(total_g, 2),
        "total_offset_tonnes": round(total_g / 1_000_000, 6),
        "total_cost_usd": round(total_cost, 4),
        "transaction_count": len(_purchase_history)
    }


def clear_history():
    """Clear purchase history (for testing)."""
    global _purchase_history
    _purchase_history = []


# Example usage
if __name__ == "__main__":
    print("Simulation Offset Provider")
    print("=" * 60)
    
    # Purchase some offsets
    result1 = purchase_offset(10.0, run_id="run-001")
    print(f"\nPurchase 1: {result1['transaction']['amount_g']}g for ${result1['transaction']['cost_usd']}")
    print(f"  Certificate: {result1['transaction']['certificate']}")
    
    result2 = purchase_offset(25.5, run_id="run-002")
    print(f"\nPurchase 2: {result2['transaction']['amount_g']}g for ${result2['transaction']['cost_usd']}")
    print(f"  Certificate: {result2['transaction']['certificate']}")
    
    # Get totals
    totals = get_total_offset()
    print(f"\nTotal Offsets: {totals['total_offset_g']}g ({totals['transaction_count']} transactions)")
    print(f"Total Cost: ${totals['total_cost_usd']}")
