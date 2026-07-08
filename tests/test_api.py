"""Tests for all API endpoints."""

import pytest


class TestHealthEndpoints:
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["services"]["database"] == "up"


class TestCarbonEndpoints:
    def test_realtime_carbon(self, client):
        response = client.get("/api/v1/carbon/realtime")
        assert response.status_code == 200
        data = response.json()
        assert "regions" in data
        assert "last_updated" in data

    def test_regions(self, client):
        response = client.get("/api/v1/carbon/regions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "carbon_intensity" in data[0]

    def test_servers(self, client):
        response = client.get("/api/v1/carbon/servers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestInferenceEndpoint:
    def test_basic_inference(self, client):
        response = client.post("/api/v1/infer", json={
            "prompt": "Hello world",
            "model": "gpt-4",
            "carbon_budget_g": 50.0
        })
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "metadata" in data
        assert "budget_status" in data
        assert data["metadata"]["server_region"] is not None

    def test_inference_saves_to_history(self, client):
        # Run an inference
        client.post("/api/v1/infer", json={
            "prompt": "Test for history",
            "model": "gpt-3.5-turbo",
            "carbon_budget_g": 100.0
        })
        
        # Check history
        history = client.get("/api/v1/history")
        assert history.status_code == 200
        assert history.json()["count"] > 0


class TestOffsetEndpoints:
    def test_purchase_offset(self, client):
        response = client.post("/api/v1/offsets/purchase", json={
            "amount_g": 10.0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["amount_g"] == 10.0

    def test_offset_history(self, client):
        response = client.get("/api/v1/offsets/history")
        assert response.status_code == 200
        data = response.json()
        assert "total_offset_g" in data
        assert "transactions" in data


class TestStatsEndpoint:
    def test_stats(self, client):
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_runs" in data
        assert "total_carbon_used_g" in data
        assert "total_carbon_saved_g" in data
