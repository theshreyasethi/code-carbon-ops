"""Tests for PCEM Smart Router module."""

import pytest
from pcem.router.smart_router import (
    load_servers,
    get_available_servers,
    calculate_server_score,
    select_best_server,
)
from pcem.analyzer.task_analyzer import analyze_task
from pcem.monitor.carbon_monitor import get_current_carbon_data


class TestLoadServers:
    def test_loads_servers(self):
        servers = load_servers()
        assert len(servers) > 0

    def test_server_has_required_fields(self):
        servers = load_servers()
        for server in servers:
            assert "region" in server
            assert "name" in server
            assert "provider" in server


class TestGetAvailableServers:
    def test_enriches_with_carbon_data(self):
        servers = get_available_servers()
        for server in servers:
            assert "carbon_intensity" in server
            assert "renewable_pct" in server


class TestCalculateServerScore:
    def test_carbon_priority_urgency5(self):
        """Urgency 5 (least urgent) should prefer green server."""
        green_server = {"carbon_intensity": 50, "renewable_pct": 0.9, "latency_ms": 200, "cost_per_hour": 5}
        dirty_server = {"carbon_intensity": 700, "renewable_pct": 0.1, "latency_ms": 50, "cost_per_hour": 2}
        task = analyze_task("test", "gpt-4")

        green_score = calculate_server_score(green_server, task, {"urgency": 5})
        dirty_score = calculate_server_score(dirty_server, task, {"urgency": 5})
        assert green_score < dirty_score  # Lower is better

    def test_latency_priority_urgency1(self):
        """Urgency 1 (most urgent) should prefer near/fast server."""
        far_server = {"carbon_intensity": 50, "renewable_pct": 0.9, "latency_ms": 500, "cost_per_hour": 3}
        near_server = {"carbon_intensity": 700, "renewable_pct": 0.1, "latency_ms": 20, "cost_per_hour": 3}
        task = analyze_task("test", "gpt-4")

        far_score = calculate_server_score(far_server, task, {"urgency": 1})
        near_score = calculate_server_score(near_server, task, {"urgency": 1})
        assert near_score < far_score

    def test_balanced_urgency3(self):
        """Urgency 3 (balanced) should consider all factors."""
        server_a = {"carbon_intensity": 200, "renewable_pct": 0.5, "latency_ms": 100, "cost_per_hour": 3}
        server_b = {"carbon_intensity": 800, "renewable_pct": 0.1, "latency_ms": 100, "cost_per_hour": 3}
        task = analyze_task("test", "gpt-4")

        score_a = calculate_server_score(server_a, task, {"urgency": 3})
        score_b = calculate_server_score(server_b, task, {"urgency": 3})
        assert score_a < score_b  # Same latency/cost, but A has lower carbon


class TestSelectBestServer:
    def test_returns_required_fields(self):
        task = analyze_task("Summarize climate change", "gpt-4")
        carbon_data = get_current_carbon_data()
        result = select_best_server(task, carbon_data, carbon_budget_g=100.0)

        assert "selected_server" in result
        assert "predicted_carbon_g" in result
        assert "carbon_saved_vs_default" in result
        assert "alternatives" in result

    def test_selected_server_has_info(self):
        task = analyze_task("Test prompt", "gpt-4")
        carbon_data = get_current_carbon_data()
        result = select_best_server(task, carbon_data)

        server = result["selected_server"]
        assert "name" in server
        assert "region" in server
        assert "carbon_intensity" in server

    def test_carbon_savings_non_negative(self):
        task = analyze_task("Test", "gpt-4")
        carbon_data = get_current_carbon_data()
        result = select_best_server(task, carbon_data)
        assert result["carbon_saved_vs_default"] >= 0
