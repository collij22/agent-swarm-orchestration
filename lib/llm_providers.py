#!/usr/bin/env python3
"""
Multi-LLM Provider Support System
Provides unified interface for multiple LLM providers with automatic fallback

Features:
- Support for Anthropic Claude, OpenAI GPT, Google Gemini
- Automatic fallback on failures
- Cost tracking per provider
- Response caching integration
- Token usage optimization
"""

import os
import json
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

# Import provider SDKs
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Note: Install anthropic for Claude support: pip install anthropic")

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Note: Install openai for GPT support: pip install openai")

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("Note: Install google-generativeai for Gemini support: pip install google-generativeai")

# Import our response cache
try:
    from response_cache import get_cache, cached_agent_call
except ImportError:
    get_cache = None
    cached_agent_call = None

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    MOCK = "mock"  # For testing

class ModelTier(Enum):
    """Model capability tiers for intelligent selection"""
    PREMIUM = "premium"  # Most capable, most expensive
    STANDARD = "standard"  # Balanced capability and cost
    FAST = "fast"  # Fast and cheap for simple tasks

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    provider: LLMProvider
    model_name: str
    tier: ModelTier
    cost_per_1k_input: float  # USD per 1K input tokens
    cost_per_1k_output: float  # USD per 1K output tokens
    max_tokens: int
    supports_tools: bool = True
    supports_vision: bool = False
    supports_streaming: bool = True
    
@dataclass
class LLMResponse:
    """Unified response structure"""
    content: str
    provider: LLMProvider
    model: str
    usage: Dict[str, int]
    cost: float
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "errors": 0
        }
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        pass
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate cost for token usage"""
        model_config = MODEL_REGISTRY.get(model)
        if not model_config:
            return 0.0
        
        input_cost = (input_tokens / 1000) * model_config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model_config.cost_per_1k_output
        return input_cost + output_cost

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"))
        if HAS_ANTHROPIC and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
    
    async def generate(
        self,
        prompt: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Claude"""
        if not self.client:
            raise ValueError("Anthropic client not initialized. Check API key.")
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            # Make API call
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system if system else None
            )
            
            # Extract usage stats
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
            
            # Calculate cost
            cost = self.calculate_cost(
                usage["input_tokens"],
                usage["output_tokens"],
                model
            )
            
            # Update stats
            self.usage_stats["total_requests"] += 1
            self.usage_stats["total_tokens"] += usage["total_tokens"]
            self.usage_stats["total_cost"] += cost
            
            return LLMResponse(
                content=response.content[0].text,
                provider=LLMProvider.ANTHROPIC,
                model=model,
                usage=usage,
                cost=cost
            )
            
        except Exception as e:
            self.usage_stats["errors"] += 1
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens for Claude (rough approximation)"""
        # Claude uses a similar tokenizer to GPT
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))
        if HAS_OPENAI and self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    async def generate(
        self,
        prompt: str,
        model: str = "gpt-4-turbo-preview",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using GPT"""
        if not self.client:
            raise ValueError("OpenAI client not initialized. Check API key.")
        
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            # Make API call
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Extract usage stats
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            # Calculate cost
            cost = self.calculate_cost(
                usage["input_tokens"],
                usage["output_tokens"],
                model
            )
            
            # Update stats
            self.usage_stats["total_requests"] += 1
            self.usage_stats["total_tokens"] += usage["total_tokens"]
            self.usage_stats["total_cost"] += cost
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider=LLMProvider.OPENAI,
                model=model,
                usage=usage,
                cost=cost
            )
            
        except Exception as e:
            self.usage_stats["errors"] += 1
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens for GPT"""
        if HAS_OPENAI:
            try:
                import tiktoken
                encoding = tiktoken.encoding_for_model("gpt-4")
                return len(encoding.encode(text))
            except:
                pass
        # Fallback to rough estimate
        return len(text) // 4

class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("GEMINI_API_KEY"))
        if HAS_GEMINI and self.api_key:
            genai.configure(api_key=self.api_key)
            self.client = genai
        else:
            self.client = None
    
    async def generate(
        self,
        prompt: str,
        model: str = "gemini-pro",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Gemini"""
        if not self.client:
            raise ValueError("Gemini client not initialized. Check API key.")
        
        try:
            # Get model
            gemini_model = self.client.GenerativeModel(model)
            
            # Generate response
            response = await asyncio.to_thread(
                gemini_model.generate_content,
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens
                }
            )
            
            # Estimate tokens (Gemini doesn't provide exact counts)
            input_tokens = self.estimate_tokens(prompt)
            output_tokens = self.estimate_tokens(response.text)
            
            usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
            
            # Calculate cost
            cost = self.calculate_cost(
                usage["input_tokens"],
                usage["output_tokens"],
                model
            )
            
            # Update stats
            self.usage_stats["total_requests"] += 1
            self.usage_stats["total_tokens"] += usage["total_tokens"]
            self.usage_stats["total_cost"] += cost
            
            return LLMResponse(
                content=response.text,
                provider=LLMProvider.GEMINI,
                model=model,
                usage=usage,
                cost=cost
            )
            
        except Exception as e:
            self.usage_stats["errors"] += 1
            logger.error(f"Gemini API error: {e}")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens for Gemini"""
        # Gemini uses a similar approach to other models
        return len(text) // 4

class MockProvider(BaseLLMProvider):
    """Mock provider for testing"""
    
    async def generate(
        self,
        prompt: str,
        model: str = "mock-model",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate mock response"""
        response = f"Mock response to: {prompt[:50]}..."
        
        usage = {
            "input_tokens": len(prompt) // 4,
            "output_tokens": len(response) // 4,
            "total_tokens": (len(prompt) + len(response)) // 4
        }
        
        return LLMResponse(
            content=response,
            provider=LLMProvider.MOCK,
            model=model,
            usage=usage,
            cost=0.0
        )
    
    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

# Model Registry
MODEL_REGISTRY = {
    # Anthropic Models
    "claude-3-5-sonnet-20241022": ModelConfig(
        provider=LLMProvider.ANTHROPIC,
        model_name="claude-3-5-sonnet-20241022",
        tier=ModelTier.STANDARD,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        max_tokens=8192,
        supports_vision=True
    ),
    "claude-3-5-haiku-20241022": ModelConfig(
        provider=LLMProvider.ANTHROPIC,
        model_name="claude-3-5-haiku-20241022",
        tier=ModelTier.FAST,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.004,
        max_tokens=8192
    ),
    "claude-3-opus-20240229": ModelConfig(
        provider=LLMProvider.ANTHROPIC,
        model_name="claude-3-opus-20240229",
        tier=ModelTier.PREMIUM,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        max_tokens=4096,
        supports_vision=True
    ),
    
    # OpenAI Models
    "gpt-4-turbo-preview": ModelConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4-turbo-preview",
        tier=ModelTier.PREMIUM,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        max_tokens=4096,
        supports_vision=True
    ),
    "gpt-4": ModelConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-4",
        tier=ModelTier.PREMIUM,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        max_tokens=8192
    ),
    "gpt-3.5-turbo": ModelConfig(
        provider=LLMProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        tier=ModelTier.FAST,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
        max_tokens=4096
    ),
    
    # Google Gemini Models
    "gemini-pro": ModelConfig(
        provider=LLMProvider.GEMINI,
        model_name="gemini-pro",
        tier=ModelTier.STANDARD,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.0005,
        max_tokens=30720
    ),
    "gemini-pro-vision": ModelConfig(
        provider=LLMProvider.GEMINI,
        model_name="gemini-pro-vision",
        tier=ModelTier.STANDARD,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.0005,
        max_tokens=30720,
        supports_vision=True
    ),
}

class MultiLLMOrchestrator:
    """
    Orchestrates multiple LLM providers with intelligent routing and fallback
    """
    
    def __init__(
        self,
        providers: Optional[List[LLMProvider]] = None,
        enable_cache: bool = True,
        enable_fallback: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize the orchestrator
        
        Args:
            providers: List of providers to enable (defaults to all available)
            enable_cache: Whether to use response caching
            enable_fallback: Whether to fallback to other providers on failure
            max_retries: Maximum retry attempts per provider
        """
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.enable_cache = enable_cache and get_cache is not None
        self.enable_fallback = enable_fallback
        self.max_retries = max_retries
        
        # Initialize cache if enabled
        if self.enable_cache:
            self.cache = get_cache()
        else:
            self.cache = None
        
        # Initialize providers
        providers = providers or [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GEMINI]
        for provider in providers:
            self._initialize_provider(provider)
        
        # Add mock provider for testing
        self.providers[LLMProvider.MOCK] = MockProvider()
        
        # Usage tracking
        self.total_stats = {
            "requests": 0,
            "cache_hits": 0,
            "fallbacks": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "errors_by_provider": {}
        }
    
    def _initialize_provider(self, provider: LLMProvider):
        """Initialize a specific provider"""
        try:
            if provider == LLMProvider.ANTHROPIC and HAS_ANTHROPIC:
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    self.providers[provider] = AnthropicProvider(api_key)
                    logger.info(f"Initialized {provider.value} provider")
            
            elif provider == LLMProvider.OPENAI and HAS_OPENAI:
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.providers[provider] = OpenAIProvider(api_key)
                    logger.info(f"Initialized {provider.value} provider")
            
            elif provider == LLMProvider.GEMINI and HAS_GEMINI:
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    self.providers[provider] = GeminiProvider(api_key)
                    logger.info(f"Initialized {provider.value} provider")
            
        except Exception as e:
            logger.warning(f"Failed to initialize {provider.value}: {e}")
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        tier: Optional[ModelTier] = None,
        use_cache: Optional[bool] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response using the best available provider
        
        Args:
            prompt: The prompt to send
            model: Specific model to use (overrides tier)
            provider: Specific provider to use
            tier: Model tier for automatic selection
            use_cache: Override cache setting for this request
            **kwargs: Additional parameters for the provider
            
        Returns:
            LLMResponse with the generated content
        """
        self.total_stats["requests"] += 1
        use_cache = use_cache if use_cache is not None else self.enable_cache
        
        # Check cache first
        if use_cache and self.cache:
            cache_key = f"{provider or 'auto'}:{model or tier or 'auto'}"
            cached_response = self.cache.get(prompt, "orchestrator", cache_key)
            if cached_response:
                self.total_stats["cache_hits"] += 1
                return LLMResponse(
                    content=cached_response,
                    provider=LLMProvider.ANTHROPIC,  # Default for cached
                    model=model or "cached",
                    usage={"cached": True},
                    cost=0.0,
                    cached=True
                )
        
        # Determine model and provider
        if model:
            # Use specific model
            model_config = MODEL_REGISTRY.get(model)
            if not model_config:
                raise ValueError(f"Unknown model: {model}")
            provider = model_config.provider
        elif provider and tier:
            # Find model for provider and tier
            model = self._select_model_for_tier(provider, tier)
        elif tier:
            # Auto-select best provider for tier
            provider, model = self._auto_select_provider(tier)
        else:
            # Default to standard tier
            provider, model = self._auto_select_provider(ModelTier.STANDARD)
        
        # Generate with fallback
        providers_to_try = [provider]
        if self.enable_fallback:
            # Add other providers as fallback
            for p in self.providers:
                if p != provider and p != LLMProvider.MOCK:
                    providers_to_try.append(p)
        
        last_error = None
        for attempt_provider in providers_to_try:
            if attempt_provider not in self.providers:
                continue
            
            try:
                # Try with current provider
                provider_instance = self.providers[attempt_provider]
                
                # Get appropriate model for this provider if switching
                if attempt_provider != provider:
                    model = self._select_model_for_tier(attempt_provider, tier or ModelTier.STANDARD)
                    self.total_stats["fallbacks"] += 1
                
                # Generate response
                response = await provider_instance.generate(
                    prompt=prompt,
                    model=model,
                    **kwargs
                )
                
                # Update stats
                self.total_stats["total_cost"] += response.cost
                self.total_stats["total_tokens"] += response.usage.get("total_tokens", 0)
                
                # Cache successful response
                if use_cache and self.cache and not response.cached:
                    cache_key = f"{attempt_provider}:{model}"
                    self.cache.set(prompt, response.content, "orchestrator", cache_key)
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {attempt_provider.value} failed: {e}")
                
                # Track errors
                if attempt_provider.value not in self.total_stats["errors_by_provider"]:
                    self.total_stats["errors_by_provider"][attempt_provider.value] = 0
                self.total_stats["errors_by_provider"][attempt_provider.value] += 1
        
        # All providers failed
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    def _select_model_for_tier(self, provider: LLMProvider, tier: ModelTier) -> str:
        """Select best model for a provider and tier"""
        for model_name, config in MODEL_REGISTRY.items():
            if config.provider == provider and config.tier == tier:
                return model_name
        
        # Fallback to any model from provider
        for model_name, config in MODEL_REGISTRY.items():
            if config.provider == provider:
                return model_name
        
        raise ValueError(f"No model found for {provider.value} with tier {tier.value}")
    
    def _auto_select_provider(self, tier: ModelTier) -> tuple[LLMProvider, str]:
        """Auto-select best available provider for tier"""
        # Priority order based on cost and capability
        priority_order = {
            ModelTier.FAST: [LLMProvider.GEMINI, LLMProvider.OPENAI, LLMProvider.ANTHROPIC],
            ModelTier.STANDARD: [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GEMINI],
            ModelTier.PREMIUM: [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GEMINI]
        }
        
        for provider in priority_order.get(tier, []):
            if provider in self.providers:
                try:
                    model = self._select_model_for_tier(provider, tier)
                    return provider, model
                except:
                    continue
        
        # Fallback to any available
        for provider in self.providers:
            if provider != LLMProvider.MOCK:
                try:
                    model = self._select_model_for_tier(provider, tier)
                    return provider, model
                except:
                    continue
        
        # Last resort: mock
        return LLMProvider.MOCK, "mock-model"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        stats = {
            "total": self.total_stats.copy(),
            "providers": {}
        }
        
        # Add per-provider stats
        for provider_enum, provider_instance in self.providers.items():
            if hasattr(provider_instance, 'usage_stats'):
                stats["providers"][provider_enum.value] = provider_instance.usage_stats
        
        # Calculate cache hit rate
        if self.total_stats["requests"] > 0:
            stats["total"]["cache_hit_rate"] = (
                self.total_stats["cache_hits"] / self.total_stats["requests"]
            )
        
        return stats
    
    def export_cost_report(self) -> str:
        """Export a formatted cost report"""
        stats = self.get_stats()
        
        report = """
═══════════════════════════════════════════════════════
                 MULTI-LLM COST REPORT
═══════════════════════════════════════════════════════
  Total Requests: {requests:,}
  Cache Hits: {cache_hits:,} ({cache_rate:.1%})
  Fallbacks Used: {fallbacks:,}
  
  💰 Total Cost: ${total_cost:.4f}
  📊 Total Tokens: {total_tokens:,}
  
  Provider Breakdown:
""".format(
            requests=stats["total"]["requests"],
            cache_hits=stats["total"]["cache_hits"],
            cache_rate=stats["total"].get("cache_hit_rate", 0),
            fallbacks=stats["total"]["fallbacks"],
            total_cost=stats["total"]["total_cost"],
            total_tokens=stats["total"]["total_tokens"]
        )
        
        for provider_name, provider_stats in stats["providers"].items():
            if provider_stats.get("total_requests", 0) > 0:
                report += f"""
  {provider_name.upper()}:
    Requests: {provider_stats['total_requests']:,}
    Tokens: {provider_stats['total_tokens']:,}
    Cost: ${provider_stats['total_cost']:.4f}
    Errors: {provider_stats['errors']}
"""
        
        report += """═══════════════════════════════════════════════════════
"""
        return report

# Convenience functions for agent integration
async def generate_with_best_model(
    prompt: str,
    tier: ModelTier = ModelTier.STANDARD,
    **kwargs
) -> str:
    """
    Generate response using the best available model for the tier
    
    Args:
        prompt: The prompt to send
        tier: Model capability tier
        **kwargs: Additional parameters
        
    Returns:
        Generated text response
    """
    orchestrator = MultiLLMOrchestrator()
    response = await orchestrator.generate(prompt, tier=tier, **kwargs)
    return response.content

def select_model_for_task(task_type: str) -> tuple[LLMProvider, str]:
    """
    Select the best model for a specific task type
    
    Args:
        task_type: Type of task (e.g., "code_generation", "analysis", "simple_qa")
        
    Returns:
        Provider and model name tuple
    """
    task_mapping = {
        "code_generation": (LLMProvider.ANTHROPIC, "claude-3-5-sonnet-20241022"),
        "complex_analysis": (LLMProvider.ANTHROPIC, "claude-3-opus-20240229"),
        "simple_qa": (LLMProvider.GEMINI, "gemini-pro"),
        "fast_response": (LLMProvider.OPENAI, "gpt-3.5-turbo"),
        "vision": (LLMProvider.OPENAI, "gpt-4-turbo-preview"),
        "long_context": (LLMProvider.GEMINI, "gemini-pro"),
    }
    
    return task_mapping.get(task_type, (LLMProvider.ANTHROPIC, "claude-3-5-sonnet-20241022"))

if __name__ == "__main__":
    # Demo and testing
    async def main():
        print("Multi-LLM Provider System - Demo")
        print("=" * 50)
        
        # Initialize orchestrator
        orchestrator = MultiLLMOrchestrator(
            providers=[LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GEMINI, LLMProvider.MOCK],
            enable_cache=True,
            enable_fallback=True
        )
        
        # Test prompts with different tiers
        test_cases = [
            ("What is 2+2?", ModelTier.FAST),
            ("Explain quantum computing", ModelTier.STANDARD),
            ("Write a Python web scraper", ModelTier.PREMIUM),
        ]
        
        print("\nTesting different model tiers...")
        for prompt, tier in test_cases:
            print(f"\n📝 Prompt: '{prompt[:50]}...'")
            print(f"   Tier: {tier.value}")
            
            try:
                response = await orchestrator.generate(
                    prompt=prompt,
                    tier=tier,
                    max_tokens=100
                )
                
                print(f"   ✅ Provider: {response.provider.value}")
                print(f"   Model: {response.model}")
                print(f"   Cost: ${response.cost:.4f}")
                print(f"   Cached: {response.cached}")
                print(f"   Response: {response.content[:100]}...")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Test fallback mechanism
        print("\n\nTesting fallback mechanism...")
        print("Simulating Anthropic failure...")
        
        # Force a specific provider that might fail
        try:
            response = await orchestrator.generate(
                prompt="Test fallback",
                provider=LLMProvider.ANTHROPIC,
                max_tokens=50
            )
            print(f"✅ Fallback successful: {response.provider.value}")
        except Exception as e:
            print(f"❌ All providers failed: {e}")
        
        # Show cost report
        print(orchestrator.export_cost_report())
    
    # Run demo
    asyncio.run(main())