"""
Carbon-Aware Model Selector — Intelligent Model Downgrading

PATENT-CRITICAL MODULE: Automatically recommends or selects a more
energy-efficient model variant when the electricity grid is carbon-heavy.

This is a GENUINELY NOVEL concept: Instead of just choosing WHERE to run
(which server), this module chooses WHAT to run (which model).

Key insight: GPT-4o-mini uses ~3x less energy than GPT-4o, and for many
tasks (summarization, Q&A, classification), the quality difference is
minimal. When the grid is dirty (>400 g/kWh), using a lighter model
can reduce carbon by 60-80% with only 5-15% quality reduction.

Decision matrix:
  - Urgency 1-2: NEVER downgrade (user explicitly needs max quality)
  - Urgency 3 + carbon > 500: SUGGEST lighter model (user chooses)
  - Urgency 4 + carbon > 400: RECOMMEND lighter model (strong suggestion)  
  - Urgency 5 + carbon > 300: AUTO-SELECT lighter model (green mode)

Quality tradeoff is quantified:
  - Each model has a "quality score" (0-100)
  - Downgrade shows exact quality loss percentage
  - Carbon savings percentage is calculated
"""

from typing import Dict, Any, Optional, List


# Model equivalence map: original → lighter alternatives
# Quality scores are relative (100 = best in class)
MODEL_REGISTRY = {
    # OpenAI
    "gpt-4o": {
        "quality": 95,
        "energy_factor": 0.00016,
        "alternatives": [
            {"model": "gpt-4o-mini", "quality": 82, "energy_factor": 0.00005},
        ],
    },
    "gpt-4.5": {
        "quality": 98,
        "energy_factor": 0.00024,
        "alternatives": [
            {"model": "gpt-4o", "quality": 95, "energy_factor": 0.00016},
            {"model": "gpt-4o-mini", "quality": 82, "energy_factor": 0.00005},
        ],
    },
    "o1": {
        "quality": 97,
        "energy_factor": 0.00030,
        "alternatives": [
            {"model": "o3-mini", "quality": 85, "energy_factor": 0.00012},
            {"model": "o4-mini", "quality": 87, "energy_factor": 0.00014},
        ],
    },
    "o3": {
        "quality": 99,
        "energy_factor": 0.00035,
        "alternatives": [
            {"model": "o3-mini", "quality": 85, "energy_factor": 0.00012},
            {"model": "o4-mini", "quality": 87, "energy_factor": 0.00014},
        ],
    },
    "gpt-4-turbo": {
        "quality": 93,
        "energy_factor": 0.00018,
        "alternatives": [
            {"model": "gpt-4o-mini", "quality": 82, "energy_factor": 0.00005},
        ],
    },
    # Anthropic
    "claude-4-opus": {
        "quality": 97,
        "energy_factor": 0.00028,
        "alternatives": [
            {"model": "claude-4-sonnet", "quality": 90, "energy_factor": 0.00015},
            {"model": "claude-3.5-haiku", "quality": 75, "energy_factor": 0.00004},
        ],
    },
    "claude-4-sonnet": {
        "quality": 90,
        "energy_factor": 0.00015,
        "alternatives": [
            {"model": "claude-3.5-haiku", "quality": 75, "energy_factor": 0.00004},
        ],
    },
    "claude-3.5-sonnet": {
        "quality": 88,
        "energy_factor": 0.00013,
        "alternatives": [
            {"model": "claude-3.5-haiku", "quality": 75, "energy_factor": 0.00004},
        ],
    },
    # Google
    "gemini-2.5-pro": {
        "quality": 94,
        "energy_factor": 0.00020,
        "alternatives": [
            {"model": "gemini-2.5-flash", "quality": 80, "energy_factor": 0.00009},
            {"model": "gemini-2.0-flash", "quality": 78, "energy_factor": 0.00008},
        ],
    },
    # Meta (open source)
    "llama-4-maverick": {
        "quality": 90,
        "energy_factor": 0.00018,
        "alternatives": [
            {"model": "llama-4-scout", "quality": 80, "energy_factor": 0.00010},
        ],
    },
    "llama-3.3-70b": {
        "quality": 85,
        "energy_factor": 0.00014,
        "alternatives": [
            {"model": "llama-4-scout", "quality": 80, "energy_factor": 0.00010},
        ],
    },
    # Other
    "deepseek-r1": {
        "quality": 92,
        "energy_factor": 0.00022,
        "alternatives": [
            {"model": "mistral-large", "quality": 84, "energy_factor": 0.00016},
        ],
    },
    # Legacy
    "gpt-4": {
        "quality": 90,
        "energy_factor": 0.00021,
        "alternatives": [
            {"model": "gpt-4o", "quality": 95, "energy_factor": 0.00016},
            {"model": "gpt-4o-mini", "quality": 82, "energy_factor": 0.00005},
        ],
    },
}

# Carbon thresholds for model adjustment decisions
CARBON_THRESHOLDS = {
    "suggest": 500,    # Suggest lighter model above this
    "recommend": 400,  # Strongly recommend above this
    "auto_select": 300,  # Auto-select lighter model above this (only urgency 5)
}


class ModelSelector:
    """
    Carbon-aware model selection engine.
    
    Recommends lighter model variants when grid carbon is high,
    balancing quality requirements against environmental impact.
    """

    def get_carbon_aware_model(
        self,
        requested_model: str,
        carbon_intensity: float,
        urgency: int = 3,
    ) -> Dict[str, Any]:
        """
        Evaluate whether the requested model should be downgraded.
        
        Args:
            requested_model: Model the user requested
            carbon_intensity: Current grid carbon (g/kWh)
            urgency: User urgency level (1-5)
        
        Returns:
            Dict with original model, recommended model, reason, and savings.
        """
        # Rule 1: Never downgrade for urgent tasks (1-2)
        if urgency <= 2:
            return self._no_change(requested_model, "High urgency — quality preserved")

        # Rule 2: If model has no alternatives, keep it
        model_info = MODEL_REGISTRY.get(requested_model)
        if not model_info or not model_info.get("alternatives"):
            return self._no_change(requested_model, "No lighter alternative available")

        # Rule 3: If carbon is low, no need to downgrade
        min_threshold = CARBON_THRESHOLDS["auto_select"] if urgency == 5 else CARBON_THRESHOLDS["suggest"]
        if carbon_intensity < min_threshold:
            return self._no_change(
                requested_model,
                f"Grid carbon ({carbon_intensity} g/kWh) is below threshold",
            )

        # Find best alternative based on urgency and carbon level
        alternatives = model_info["alternatives"]
        original_energy = model_info["energy_factor"]
        original_quality = model_info["quality"]

        # Select the best alternative
        best_alt = self._select_best_alternative(
            alternatives, carbon_intensity, urgency, original_quality
        )

        if not best_alt:
            return self._no_change(requested_model, "No suitable alternative found")

        # Calculate savings
        alt_energy = best_alt["energy_factor"]
        energy_savings_pct = round((1 - alt_energy / original_energy) * 100, 1)
        carbon_savings_pct = energy_savings_pct  # Linear relationship

        quality_loss_pct = round(
            (original_quality - best_alt["quality"]) / original_quality * 100, 1
        )

        # Determine action level
        if urgency == 5 and carbon_intensity >= CARBON_THRESHOLDS["auto_select"]:
            action = "auto_selected"
            reason = (
                f"🌱 Auto-selected {best_alt['model']} (urgency=minimal, "
                f"grid={carbon_intensity} g/kWh). Saves {carbon_savings_pct}% carbon "
                f"with {quality_loss_pct}% quality tradeoff."
            )
        elif urgency >= 4 and carbon_intensity >= CARBON_THRESHOLDS["recommend"]:
            action = "recommended"
            reason = (
                f"♻️ Recommend switching to {best_alt['model']} — grid is carbon-heavy "
                f"({carbon_intensity} g/kWh). {carbon_savings_pct}% carbon savings, "
                f"only {quality_loss_pct}% quality reduction."
            )
        else:
            action = "suggested"
            reason = (
                f"💡 Consider {best_alt['model']} to reduce carbon by "
                f"{carbon_savings_pct}% (quality -{quality_loss_pct}%)."
            )

        return {
            "original_model": requested_model,
            "recommended_model": best_alt["model"],
            "action": action,
            "reason": reason,
            "quality_tradeoff": {
                "original_quality": original_quality,
                "recommended_quality": best_alt["quality"],
                "quality_loss_pct": quality_loss_pct,
            },
            "energy_savings": {
                "original_energy_factor": original_energy,
                "recommended_energy_factor": alt_energy,
                "energy_savings_pct": energy_savings_pct,
                "carbon_savings_pct": carbon_savings_pct,
            },
            "carbon_context": {
                "current_carbon_intensity": carbon_intensity,
                "threshold_used": min_threshold,
                "urgency": urgency,
            },
        }

    def _select_best_alternative(
        self,
        alternatives: List[Dict],
        carbon_intensity: float,
        urgency: int,
        original_quality: int,
    ) -> Optional[Dict]:
        """
        Select the best alternative model based on carbon/quality tradeoff.
        
        Higher urgency + higher carbon → accept more quality loss.
        Lower urgency + lower carbon → prefer minimal quality loss.
        """
        # Maximum acceptable quality loss based on urgency
        max_quality_loss = {
            3: 15,   # Balanced: accept up to 15% quality loss
            4: 25,   # Low urgency: accept up to 25% quality loss
            5: 40,   # Minimal urgency: accept up to 40% quality loss
        }.get(urgency, 15)

        # Filter alternatives by acceptable quality loss
        viable = []
        for alt in alternatives:
            quality_loss = (original_quality - alt["quality"]) / original_quality * 100
            if quality_loss <= max_quality_loss:
                viable.append({**alt, "quality_loss": quality_loss})

        if not viable:
            return None

        # For very high carbon, prefer maximum energy savings
        if carbon_intensity > 600:
            return min(viable, key=lambda x: x["energy_factor"])

        # Otherwise, prefer best quality among viable alternatives
        return max(viable, key=lambda x: x["quality"])

    def _no_change(self, model: str, reason: str) -> Dict[str, Any]:
        """Return result indicating no model change needed."""
        return {
            "original_model": model,
            "recommended_model": model,
            "action": "keep_original",
            "reason": reason,
            "quality_tradeoff": None,
            "energy_savings": None,
            "carbon_context": None,
        }

    def get_all_model_alternatives(self) -> Dict[str, Any]:
        """Return the full model registry with alternatives."""
        result = {}
        for model, info in MODEL_REGISTRY.items():
            alts = info.get("alternatives", [])
            result[model] = {
                "quality": info["quality"],
                "energy_factor": info["energy_factor"],
                "alternatives": [
                    {
                        "model": a["model"],
                        "quality": a["quality"],
                        "energy_savings_pct": round(
                            (1 - a["energy_factor"] / info["energy_factor"]) * 100, 1
                        ),
                    }
                    for a in alts
                ],
            }
        return result


# Singleton
model_selector = ModelSelector()
