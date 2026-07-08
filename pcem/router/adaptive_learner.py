"""
Adaptive Learner — Self-Improving Server Selection via Thompson Sampling

PATENT-CRITICAL MODULE: This implements a Bayesian multi-armed bandit approach
to server routing that LEARNS from historical routing outcomes.

Unlike static weight presets, this system:
1. Tracks every routing decision and its actual outcome
2. Maintains Beta distributions (success/failure) per server per urgency level
3. Uses Thompson Sampling to balance exploration vs exploitation
4. Adjusts routing scores based on learned server performance

The key insight: A server that consistently delivers LOWER carbon than
predicted gets a reward, shifting future traffic toward it. A server
that underperforms gets penalized, even if its static score looks good.

Algorithm:
  - Each (server, urgency_level) pair has a Beta(α, β) distribution
  - α = successful outcomes (actual carbon < predicted)
  - β = unsuccessful outcomes (actual carbon >= predicted)
  - Thompson Sampling: sample θ ~ Beta(α, β), use as exploration bonus
  - Adaptive weight adjustment: shift weights based on observed patterns
"""

import json
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from backend.database.connection import SessionLocal
from backend.database.models import RoutingFeedback


class AdaptiveLearner:
    """
    Bayesian adaptive routing learner using Thompson Sampling.
    
    Learns optimal server selection by tracking routing outcomes
    and adjusting future decisions based on observed performance.
    """

    # Base urgency weights (starting point before adaptation)
    BASE_URGENCY_WEIGHTS = {
        1: {"carbon": 0.15, "renewable": 0.10, "latency": 0.45, "cost": 0.30},
        2: {"carbon": 0.20, "renewable": 0.10, "latency": 0.35, "cost": 0.35},
        3: {"carbon": 0.30, "renewable": 0.15, "latency": 0.25, "cost": 0.30},
        4: {"carbon": 0.40, "renewable": 0.20, "latency": 0.15, "cost": 0.25},
        5: {"carbon": 0.50, "renewable": 0.25, "latency": 0.05, "cost": 0.20},
    }

    # Learning rate: how fast weights adapt (0.0 = no learning, 1.0 = instant)
    LEARNING_RATE = 0.15

    # Exploration parameter: higher = more exploration of unfamiliar servers
    EXPLORATION_WEIGHT = 0.05

    # Minimum samples before adaptation kicks in
    MIN_SAMPLES_FOR_ADAPTATION = 3

    def __init__(self):
        """Initialize with prior beliefs (uninformative Beta(1,1) = uniform)."""
        self._cache = {}  # In-memory cache of learned parameters
        self._cache_loaded = False

    def _load_cache(self):
        """Load learned parameters from database into memory."""
        if self._cache_loaded:
            return

        db = SessionLocal()
        try:
            # Load recent feedback (last 30 days)
            cutoff = datetime.utcnow() - timedelta(days=30)
            feedbacks = (
                db.query(RoutingFeedback)
                .filter(RoutingFeedback.created_at >= cutoff)
                .all()
            )

            for fb in feedbacks:
                key = (fb.server_region, fb.urgency_level)
                if key not in self._cache:
                    self._cache[key] = {
                        "alpha": 1.0,  # Prior: 1 success
                        "beta": 1.0,   # Prior: 1 failure
                        "total_carbon_error": 0.0,
                        "total_latency_error": 0.0,
                        "count": 0,
                        "avg_satisfaction": 0.5,
                    }

                entry = self._cache[key]
                # Update Beta distribution based on outcome
                if fb.satisfaction_score and fb.satisfaction_score > 0.5:
                    entry["alpha"] += 1
                else:
                    entry["beta"] += 1

                # Track prediction errors
                if fb.predicted_carbon and fb.actual_carbon:
                    entry["total_carbon_error"] += (
                        fb.predicted_carbon - fb.actual_carbon
                    )
                if fb.predicted_latency and fb.actual_latency:
                    entry["total_latency_error"] += (
                        fb.predicted_latency - fb.actual_latency
                    )

                entry["count"] += 1
                if fb.satisfaction_score:
                    # Running average of satisfaction
                    n = entry["count"]
                    entry["avg_satisfaction"] = (
                        entry["avg_satisfaction"] * (n - 1) + fb.satisfaction_score
                    ) / n

            self._cache_loaded = True
        finally:
            db.close()

    def record_outcome(
        self,
        server_region: str,
        urgency: int,
        predicted_carbon: float,
        actual_carbon: float,
        predicted_latency: float,
        actual_latency: float,
        model_used: str = None,
    ):
        """
        Record the outcome of a routing decision for future learning.
        
        Satisfaction is computed as a composite score:
        - Carbon accuracy: was actual carbon close to or below prediction?
        - Latency accuracy: was actual latency close to or below prediction?
        
        Returns:
            satisfaction_score (0.0 to 1.0)
        """
        # Compute satisfaction score (0 to 1)
        carbon_ratio = actual_carbon / max(predicted_carbon, 0.0001)
        latency_ratio = actual_latency / max(predicted_latency, 1.0)

        # Carbon satisfaction: 1.0 if actual <= predicted, decays if over
        carbon_satisfaction = min(1.0, 1.0 / max(carbon_ratio, 0.5))

        # Latency satisfaction: 1.0 if actual <= predicted, decays if over
        latency_satisfaction = min(1.0, 1.0 / max(latency_ratio, 0.5))

        # Weighted composite (carbon matters more for sustainability)
        satisfaction = 0.6 * carbon_satisfaction + 0.4 * latency_satisfaction

        # Save to database
        db = SessionLocal()
        try:
            feedback = RoutingFeedback(
                server_region=server_region,
                urgency_level=urgency,
                predicted_carbon=predicted_carbon,
                actual_carbon=actual_carbon,
                predicted_latency=predicted_latency,
                actual_latency=actual_latency,
                satisfaction_score=round(satisfaction, 4),
                model_used=model_used,
            )
            db.add(feedback)
            db.commit()

            # Update in-memory cache
            key = (server_region, urgency)
            if key not in self._cache:
                self._cache[key] = {
                    "alpha": 1.0, "beta": 1.0,
                    "total_carbon_error": 0.0, "total_latency_error": 0.0,
                    "count": 0, "avg_satisfaction": 0.5,
                }
            entry = self._cache[key]

            if satisfaction > 0.5:
                entry["alpha"] += 1
            else:
                entry["beta"] += 1

            entry["total_carbon_error"] += (predicted_carbon - actual_carbon)
            entry["total_latency_error"] += (predicted_latency - actual_latency)
            entry["count"] += 1
            n = entry["count"]
            entry["avg_satisfaction"] = (
                entry["avg_satisfaction"] * (n - 1) + satisfaction
            ) / n

            return satisfaction

        except Exception:
            db.rollback()
            return 0.5
        finally:
            db.close()

    def get_exploration_bonus(self, server_region: str, urgency: int) -> float:
        """
        Thompson Sampling: sample from the server's Beta distribution.
        
        Returns a bonus score (0 to 1) representing the sampled
        probability of success for this server+urgency combination.
        
        Servers with less data get more variable samples → more exploration.
        Servers with confirmed good performance get consistently high samples.
        """
        self._load_cache()

        key = (server_region, urgency)
        entry = self._cache.get(key, {"alpha": 1.0, "beta": 1.0})

        # Thompson Sampling: draw from Beta(α, β)
        try:
            sample = random.betavariate(entry["alpha"], entry["beta"])
        except ValueError:
            sample = 0.5

        # Convert to a bonus: good servers get negative bonus (lower score = better)
        # Bad servers get positive bonus (higher score = worse)
        bonus = (0.5 - sample) * self.EXPLORATION_WEIGHT

        return round(bonus, 6)

    def get_adaptive_weights(self, urgency: int) -> Dict[str, float]:
        """
        Return adapted weights based on learned patterns.
        
        Starts with base urgency weights, then adjusts based on
        observed outcomes across all servers at this urgency level.
        
        If we've learned that carbon predictions are consistently
        off (e.g., carbon is always higher than predicted), we
        increase the carbon weight to compensate.
        """
        self._load_cache()

        base = dict(self.BASE_URGENCY_WEIGHTS.get(urgency, self.BASE_URGENCY_WEIGHTS[3]))

        # Collect all feedback for this urgency level
        relevant = {
            k: v for k, v in self._cache.items()
            if k[1] == urgency and v["count"] >= self.MIN_SAMPLES_FOR_ADAPTATION
        }

        if not relevant:
            return base  # Not enough data, use base weights

        # Calculate average prediction errors across all servers
        total_count = sum(v["count"] for v in relevant.values())
        avg_carbon_error = sum(v["total_carbon_error"] for v in relevant.values()) / max(total_count, 1)
        avg_latency_error = sum(v["total_latency_error"] for v in relevant.values()) / max(total_count, 1)

        # If carbon is consistently UNDER-predicted (actual > predicted),
        # increase carbon weight to be more cautious
        if avg_carbon_error < 0:  # Predicted < Actual → we underestimate carbon
            carbon_adjustment = min(self.LEARNING_RATE, abs(avg_carbon_error) / 100)
            base["carbon"] += carbon_adjustment
            base["latency"] -= carbon_adjustment / 2
            base["cost"] -= carbon_adjustment / 2

        # If latency is consistently UNDER-predicted,
        # increase latency weight
        if avg_latency_error < 0:  # Predicted < Actual → we underestimate latency
            latency_adjustment = min(self.LEARNING_RATE, abs(avg_latency_error) / 500)
            base["latency"] += latency_adjustment
            base["carbon"] -= latency_adjustment / 2
            base["cost"] -= latency_adjustment / 2

        # Normalize weights to sum to 1.0
        total = sum(base.values())
        if total > 0:
            base = {k: round(v / total, 4) for k, v in base.items()}

        return base

    def get_server_stats(self, server_region: str = None) -> Dict[str, Any]:
        """
        Get learning statistics for a server or all servers.
        
        Returns performance history, Beta distribution parameters,
        and estimated success probability for each server.
        """
        self._load_cache()

        stats = {}
        for (region, urgency), entry in self._cache.items():
            if server_region and region != server_region:
                continue

            key = f"{region}_u{urgency}"
            alpha, beta_val = entry["alpha"], entry["beta"]
            expected = alpha / (alpha + beta_val) if (alpha + beta_val) > 0 else 0.5

            stats[key] = {
                "server_region": region,
                "urgency": urgency,
                "alpha": round(alpha, 1),
                "beta": round(beta_val, 1),
                "expected_success_rate": round(expected, 3),
                "total_decisions": entry["count"],
                "avg_satisfaction": round(entry["avg_satisfaction"], 3),
                "confidence": "high" if entry["count"] >= 10 else "medium" if entry["count"] >= 5 else "low",
            }

        return stats

    def reset_learning(self):
        """Reset all learned parameters (for testing)."""
        self._cache = {}
        self._cache_loaded = False


# Singleton instance
adaptive_learner = AdaptiveLearner()
