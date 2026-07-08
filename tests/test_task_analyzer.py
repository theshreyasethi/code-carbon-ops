"""Tests for PCEM Task Analyzer module."""

from pcem.analyzer.task_analyzer import (
    estimate_tokens,
    estimate_energy_kwh,
    estimate_gpu_seconds,
    analyze_task,
    categorize_complexity,
)


class TestEstimateTokens:
    def test_short_prompt(self):
        result = estimate_tokens("Hello world", max_output_tokens=100)
        assert result["input_tokens"] >= 1
        assert result["output_tokens"] == 100
        assert result["total_tokens"] == result["input_tokens"] + result["output_tokens"]

    def test_long_prompt(self):
        prompt = "x" * 4000  # ~1000 tokens
        result = estimate_tokens(prompt)
        assert result["input_tokens"] == 1000

    def test_empty_prompt(self):
        result = estimate_tokens("")
        assert result["input_tokens"] == 1  # min 1

    def test_total_tokens_sum(self):
        result = estimate_tokens("Test prompt", max_output_tokens=500)
        assert result["total_tokens"] == result["input_tokens"] + result["output_tokens"]


class TestEstimateEnergy:
    def test_gpt4_energy(self):
        energy = estimate_energy_kwh(1000, "gpt-4")
        assert energy == pytest.approx(0.00021, rel=0.01)

    def test_gpt35_cheaper(self):
        gpt4_energy = estimate_energy_kwh(1000, "gpt-4")
        gpt35_energy = estimate_energy_kwh(1000, "gpt-3.5-turbo")
        assert gpt35_energy < gpt4_energy

    def test_unknown_model_uses_default(self):
        energy = estimate_energy_kwh(1000, "unknown-model")
        default_energy = estimate_energy_kwh(1000, "default")
        assert energy == default_energy

    def test_zero_tokens(self):
        energy = estimate_energy_kwh(0, "gpt-4")
        assert energy == 0


class TestGPUSeconds:
    def test_gpt4_slower_than_gpt35(self):
        gpt4_time = estimate_gpu_seconds(1000, "gpt-4")
        gpt35_time = estimate_gpu_seconds(1000, "gpt-3.5-turbo")
        assert gpt4_time > gpt35_time


class TestAnalyzeTask:
    def test_returns_required_fields(self):
        result = analyze_task("Test prompt", "gpt-4")
        required_keys = [
            "model", "input_tokens", "output_tokens", "total_tokens",
            "estimated_energy_kwh", "estimated_gpu_seconds", "complexity"
        ]
        for key in required_keys:
            assert key in result

    def test_model_preserved(self):
        result = analyze_task("Test", "claude-3-opus")
        assert result["model"] == "claude-3-opus"


class TestCategorizeComplexity:
    def test_simple(self):
        assert categorize_complexity(100) == "simple"

    def test_moderate(self):
        assert categorize_complexity(1000) == "moderate"

    def test_complex(self):
        assert categorize_complexity(5000) == "complex"

    def test_heavy(self):
        assert categorize_complexity(10000) == "heavy"


import pytest
