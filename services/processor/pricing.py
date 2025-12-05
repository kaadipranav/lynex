"""
Pricing module for model cost calculation.
Maintains pricing table and provides cost calculation utilities.
"""

from typing import Dict, Optional
from datetime import datetime

# Pricing per 1M tokens (input/output) in USD
# Updated as of December 2025
MODEL_PRICING = {
    # OpenAI
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "gpt-3.5-turbo-16k": {"input": 3.0, "output": 4.0},
    
    # Anthropic
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku": {"input": 1.0, "output": 5.0},
    
    # Google
    "gemini-pro": {"input": 0.50, "output": 1.50},
    "gemini-pro-vision": {"input": 0.50, "output": 1.50},
    "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
    "gemini-1.5-flash": {"input": 0.35, "output": 1.05},
    
    # Mistral
    "mistral-small": {"input": 1.0, "output": 3.0},
    "mistral-medium": {"input": 2.7, "output": 8.1},
    "mistral-large": {"input": 4.0, "output": 12.0},
    
    # Cohere
    "command": {"input": 1.0, "output": 2.0},
    "command-light": {"input": 0.30, "output": 0.60},
    "command-r": {"input": 0.50, "output": 1.50},
    "command-r-plus": {"input": 3.0, "output": 15.0},
    
    # Default for unknown models
    "default": {"input": 1.0, "output": 2.0},
}


class PricingCalculator:
    """Calculate costs for LLM API calls based on token usage."""
    
    def __init__(self):
        self.pricing = MODEL_PRICING
    
    def calculate_cost(
        self,
        model: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
    ) -> float:
        """
        Calculate cost for a model invocation.
        
        Args:
            model: Model name (e.g., "gpt-4", "claude-3-sonnet")
            input_tokens: Number of prompt tokens
            output_tokens: Number of completion tokens
            total_tokens: Total tokens (used if input/output not available)
        
        Returns:
            Cost in USD
        """
        # Normalize model name (remove version suffixes, lowercase)
        normalized_model = self._normalize_model_name(model)
        
        # Get pricing for this model (fallback to default)
        pricing = self.pricing.get(normalized_model, self.pricing["default"])
        
        cost = 0.0
        
        if input_tokens is not None and output_tokens is not None:
            # Precise calculation
            cost = (
                (input_tokens / 1_000_000) * pricing["input"]
                + (output_tokens / 1_000_000) * pricing["output"]
            )
        elif total_tokens is not None:
            # Estimate: assume 70% input, 30% output (typical ratio)
            estimated_input = int(total_tokens * 0.7)
            estimated_output = int(total_tokens * 0.3)
            cost = (
                (estimated_input / 1_000_000) * pricing["input"]
                + (estimated_output / 1_000_000) * pricing["output"]
            )
        
        return round(cost, 6)  # Round to 6 decimal places
    
    def _normalize_model_name(self, model: str) -> str:
        """
        Normalize model name to match pricing table keys.
        
        Examples:
            "gpt-4-0125-preview" -> "gpt-4"
            "claude-3-opus-20240229" -> "claude-3-opus"
            "gpt-4o-2024-05-13" -> "gpt-4o"
        """
        model = model.lower().strip()
        
        # Check for exact matches first
        if model in self.pricing:
            return model
        
        # Try prefix matching (handles versioned models)
        for key in self.pricing.keys():
            if model.startswith(key):
                return key
        
        # Fallback to default
        return "default"
    
    def get_model_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing info for a specific model."""
        normalized = self._normalize_model_name(model)
        return self.pricing.get(normalized, self.pricing["default"])


# Global calculator instance
pricing_calculator = PricingCalculator()
