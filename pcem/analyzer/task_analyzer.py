"""
Task Analyzer - LLM Task Complexity Estimation

Estimates energy consumption for AI/LLM tasks based on:
- Token count (input + output)
- Model size and architecture
- GPU requirements
"""

from typing import Dict, Any
import math


# Energy consumption estimates per model (kWh per 1000 tokens)
# Based on model parameter counts and architecture efficiency
MODEL_ENERGY_FACTORS = {
    # OpenAI Models (2024-2026)
    "gpt-4o": 0.00016,            # Optimized multimodal, efficient
    "gpt-4o-mini": 0.00005,       # Lightweight variant
    "gpt-4.5": 0.00024,           # Largest OpenAI model
    "gpt-4-turbo": 0.00018,       # Previous gen turbo
    "o1": 0.00030,                # Reasoning model, high compute
    "o3": 0.00035,                # Latest reasoning, very heavy
    "o3-mini": 0.00012,           # Lightweight reasoning
    "o4-mini": 0.00014,           # Latest compact reasoning

    # Anthropic Models (2024-2026)
    "claude-4-opus": 0.00028,     # Largest Anthropic model
    "claude-4-sonnet": 0.00015,   # Balanced performance
    "claude-3.5-sonnet": 0.00013, # Previous gen, very popular
    "claude-3.5-haiku": 0.00004,  # Fast and lightweight

    # Google Models (2024-2026)
    "gemini-2.5-pro": 0.00020,    # Latest Gemini, thinking model
    "gemini-2.0-flash": 0.00008,  # Fast and efficient
    "gemini-2.5-flash": 0.00009,  # Latest flash variant

    # Meta Models (open-source, self-hosted)
    "llama-4-maverick": 0.00018,  # 400B MoE model
    "llama-4-scout": 0.00010,     # 109B efficient variant
    "llama-3.3-70b": 0.00014,     # Popular open-source

    # Other Open Models
    "deepseek-r1": 0.00022,       # DeepSeek reasoning model
    "mistral-large": 0.00016,     # Mistral flagship

    # Legacy (backward compatibility)
    "gpt-4": 0.00021,
    "gpt-3.5-turbo": 0.00004,
    "claude-3-opus": 0.00025,

    # Default fallback
    "default": 0.00010
}


def estimate_tokens(prompt: str, max_output_tokens: int = 1000) -> Dict[str, int]:
    """
    Estimate token count for a prompt.
    
    Rough estimation: ~4 characters per token for English text.
    """
    input_tokens = max(1, len(prompt) // 4)
    output_tokens = max_output_tokens
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens
    }


def estimate_energy_kwh(total_tokens: int, model: str) -> float:
    """
    Estimate energy consumption in kWh for processing tokens.
    
    Formula: Energy = (tokens / 1000) * model_factor
    """
    model_factor = MODEL_ENERGY_FACTORS.get(model, MODEL_ENERGY_FACTORS["default"])
    energy_kwh = (total_tokens / 1000) * model_factor
    return energy_kwh


def estimate_gpu_seconds(total_tokens: int, model: str) -> float:
    """
    Estimate GPU processing time in seconds.
    
    Based on typical inference speeds for different model sizes.
    """
    # Tokens per second estimates
    tokens_per_second = {
        "gpt-4o": 80, "gpt-4o-mini": 120, "gpt-4.5": 30,
        "gpt-4-turbo": 40, "o1": 15, "o3": 12, "o3-mini": 50, "o4-mini": 45,
        "claude-4-opus": 20, "claude-4-sonnet": 55, "claude-3.5-sonnet": 60, "claude-3.5-haiku": 150,
        "gemini-2.5-pro": 50, "gemini-2.0-flash": 120, "gemini-2.5-flash": 110,
        "llama-4-maverick": 25, "llama-4-scout": 45, "llama-3.3-70b": 30,
        "deepseek-r1": 20, "mistral-large": 55,
        "gpt-4": 25, "gpt-3.5-turbo": 100, "claude-3-opus": 20,
        "default": 50
    }
    
    tps = tokens_per_second.get(model, tokens_per_second["default"])
    return total_tokens / tps


def analyze_task(prompt: str, model: str = "gpt-4o", max_output_tokens: int = 1000) -> Dict[str, Any]:
    """
    Analyze an LLM task and estimate resource requirements.
    
    Args:
        prompt: The input prompt/task
        model: The model to use (e.g., "gpt-4", "claude-3-opus")
        max_output_tokens: Expected maximum output tokens
    
    Returns:
        Dict with task analysis including:
        - Token estimates
        - Energy consumption (kWh)
        - GPU time (seconds)
        - Model info
    """
    # Estimate tokens
    token_info = estimate_tokens(prompt, max_output_tokens)
    
    # Estimate energy
    energy_kwh = estimate_energy_kwh(token_info["total_tokens"], model)
    
    # Estimate GPU time
    gpu_seconds = estimate_gpu_seconds(token_info["total_tokens"], model)
    
    # Get model factor for reference
    model_factor = MODEL_ENERGY_FACTORS.get(model, MODEL_ENERGY_FACTORS["default"])
    
    return {
        "model": model,
        "input_tokens": token_info["input_tokens"],
        "output_tokens": token_info["output_tokens"],
        "total_tokens": token_info["total_tokens"],
        "estimated_energy_kwh": round(energy_kwh, 6),
        "estimated_gpu_seconds": round(gpu_seconds, 2),
        "model_energy_factor": model_factor,
        "complexity": categorize_complexity(token_info["total_tokens"])
    }


def categorize_complexity(total_tokens: int) -> str:
    """Categorize task complexity based on token count."""
    if total_tokens < 500:
        return "simple"
    elif total_tokens < 2000:
        return "moderate"
    elif total_tokens < 8000:
        return "complex"
    else:
        return "heavy"


# Example usage
if __name__ == "__main__":
    test_prompts = [
        ("What is 2+2?", "gpt-3.5-turbo"),
        ("Summarize the key themes in Shakespeare's Hamlet.", "gpt-4"),
        ("Write a 2000-word essay on climate change impacts.", "claude-3-opus"),
    ]
    
    print("Task Analysis Examples")
    print("=" * 60)
    
    for prompt, model in test_prompts:
        result = analyze_task(prompt, model)
        print(f"\nPrompt: {prompt[:50]}...")
        print(f"Model: {result['model']}")
        print(f"Total Tokens: {result['total_tokens']}")
        print(f"Energy: {result['estimated_energy_kwh']} kWh")
        print(f"GPU Time: {result['estimated_gpu_seconds']}s")
        print(f"Complexity: {result['complexity']}")
