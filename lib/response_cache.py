#!/usr/bin/env python3
"""
Enhanced Response Caching System for Agent Swarm
Provides intelligent caching to reduce API calls and costs

Features:
- LRU cache with configurable size
- TTL-based expiration
- Similarity matching for semantic caching
- Persistent cache storage
- Cache statistics and hit rate tracking
"""

import os
import json
import time
import hashlib
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
from dataclasses import dataclass, asdict
from enum import Enum

# Optional imports for advanced features
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    print("Note: Install sentence-transformers for semantic caching: pip install sentence-transformers")

class CacheStrategy(Enum):
    """Cache strategies for different use cases"""
    EXACT = "exact"  # Exact match only
    SEMANTIC = "semantic"  # Semantic similarity matching
    HYBRID = "hybrid"  # Try exact first, then semantic

@dataclass
class CacheEntry:
    """Represents a cached response entry"""
    key: str
    prompt: str
    response: str
    agent_name: str
    model: str
    timestamp: float
    ttl: int  # Time to live in seconds
    hit_count: int = 0
    cost_saved: float = 0.0
    embedding: Optional[List[float]] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.timestamp > self.ttl
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert embedding to list if numpy array
        if self.embedding is not None and hasattr(self.embedding, 'tolist'):
            data['embedding'] = self.embedding.tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheEntry':
        """Create from dictionary"""
        return cls(**data)

class ResponseCache:
    """
    Enhanced response caching system with multiple strategies
    """
    
    def __init__(
        self,
        cache_dir: str = ".cache/responses",
        max_memory_entries: int = 1000,
        default_ttl: int = 3600,  # 1 hour default
        strategy: CacheStrategy = CacheStrategy.HYBRID,
        similarity_threshold: float = 0.85,
        enable_persistence: bool = True
    ):
        """
        Initialize the response cache
        
        Args:
            cache_dir: Directory for persistent cache storage
            max_memory_entries: Maximum entries in memory cache
            default_ttl: Default time-to-live in seconds
            strategy: Caching strategy to use
            similarity_threshold: Threshold for semantic similarity (0-1)
            enable_persistence: Whether to persist cache to disk
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_entries = max_memory_entries
        self.default_ttl = default_ttl
        self.strategy = strategy
        self.similarity_threshold = similarity_threshold
        self.enable_persistence = enable_persistence
        
        # Memory cache (LRU)
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "cost_saved": 0.0,
            "api_calls_saved": 0,
            "last_cleanup": time.time()
        }
        
        # Semantic similarity model
        self.embedder = None
        if HAS_EMBEDDINGS and strategy in [CacheStrategy.SEMANTIC, CacheStrategy.HYBRID]:
            try:
                # Use a lightweight model for speed
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                print("Semantic caching enabled with sentence-transformers")
            except Exception as e:
                print(f"Failed to load embedding model: {e}")
                self.strategy = CacheStrategy.EXACT
        
        # Load persistent cache
        if enable_persistence:
            self._load_persistent_cache()
    
    def _generate_key(self, prompt: str, agent_name: str, model: str) -> str:
        """Generate a unique cache key"""
        content = f"{agent_name}:{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        # Convert to numpy arrays if needed
        if HAS_EMBEDDINGS:
            import numpy as np
            e1 = np.array(embedding1)
            e2 = np.array(embedding2)
            
            # Cosine similarity
            dot_product = np.dot(e1, e2)
            norm1 = np.linalg.norm(e1)
            norm2 = np.linalg.norm(e2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        return 0.0
    
    def _find_semantic_match(
        self, 
        prompt: str, 
        agent_name: str,
        embedding: Optional[List[float]] = None
    ) -> Optional[CacheEntry]:
        """Find a semantically similar cached response"""
        if not self.embedder or not embedding:
            return None
        
        best_match = None
        best_similarity = 0.0
        
        with self.lock:
            for entry in self.memory_cache.values():
                # Only match same agent type
                if entry.agent_name != agent_name:
                    continue
                
                if entry.is_expired():
                    continue
                
                if entry.embedding:
                    similarity = self._calculate_similarity(embedding, entry.embedding)
                    if similarity > best_similarity and similarity >= self.similarity_threshold:
                        best_similarity = similarity
                        best_match = entry
        
        return best_match
    
    def get(
        self, 
        prompt: str, 
        agent_name: str, 
        model: str,
        semantic_search: bool = True
    ) -> Optional[str]:
        """
        Retrieve a cached response
        
        Args:
            prompt: The prompt to look up
            agent_name: Name of the agent
            model: Model being used
            semantic_search: Whether to use semantic similarity
            
        Returns:
            Cached response if found, None otherwise
        """
        # Generate key for exact match
        key = self._generate_key(prompt, agent_name, model)
        
        with self.lock:
            # Try exact match first
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if not entry.is_expired():
                    # Move to end (LRU)
                    self.memory_cache.move_to_end(key)
                    entry.hit_count += 1
                    self.stats["hits"] += 1
                    self.stats["api_calls_saved"] += 1
                    self._estimate_cost_saved(model)
                    return entry.response
                else:
                    # Remove expired entry
                    del self.memory_cache[key]
            
            # Try semantic match if enabled
            if semantic_search and self.strategy in [CacheStrategy.SEMANTIC, CacheStrategy.HYBRID]:
                embedding = None
                if self.embedder:
                    embedding = self.embedder.encode(prompt).tolist()
                
                semantic_match = self._find_semantic_match(prompt, agent_name, embedding)
                if semantic_match:
                    semantic_match.hit_count += 1
                    self.stats["hits"] += 1
                    self.stats["api_calls_saved"] += 1
                    self._estimate_cost_saved(model)
                    return semantic_match.response
            
            self.stats["misses"] += 1
            return None
    
    def set(
        self,
        prompt: str,
        response: str,
        agent_name: str,
        model: str,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache a response
        
        Args:
            prompt: The prompt that generated the response
            response: The response to cache
            agent_name: Name of the agent
            model: Model used
            ttl: Time-to-live in seconds (uses default if None)
        """
        key = self._generate_key(prompt, agent_name, model)
        ttl = ttl or self.default_ttl
        
        # Generate embedding if using semantic caching
        embedding = None
        if self.embedder and self.strategy in [CacheStrategy.SEMANTIC, CacheStrategy.HYBRID]:
            embedding = self.embedder.encode(prompt).tolist()
        
        entry = CacheEntry(
            key=key,
            prompt=prompt,
            response=response,
            agent_name=agent_name,
            model=model,
            timestamp=time.time(),
            ttl=ttl,
            embedding=embedding
        )
        
        with self.lock:
            # Add to cache (moves to end if exists)
            self.memory_cache[key] = entry
            self.memory_cache.move_to_end(key)
            
            # Enforce size limit (LRU eviction)
            while len(self.memory_cache) > self.max_memory_entries:
                # Remove oldest entry
                oldest_key = next(iter(self.memory_cache))
                del self.memory_cache[oldest_key]
            
            # Periodic cleanup
            self._cleanup_expired()
        
        # Persist if enabled
        if self.enable_persistence:
            self._save_entry_to_disk(entry)
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries (called periodically)"""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self.stats["last_cleanup"] < 300:
            return
        
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        self.stats["last_cleanup"] = current_time
    
    def _estimate_cost_saved(self, model: str) -> None:
        """Estimate cost saved by cache hit"""
        # Rough estimates based on model ($ per 1M tokens)
        cost_per_million = {
            "claude-3-5-haiku": 1.0,
            "claude-sonnet-4": 3.0,
            "claude-opus-4": 15.0
        }
        
        # Assume average 500 tokens per request
        tokens = 500
        base_cost = 3.0  # Default
        
        for model_key, cost in cost_per_million.items():
            if model_key in model.lower():
                base_cost = cost
                break
        
        estimated_cost = (tokens / 1_000_000) * base_cost
        self.stats["cost_saved"] += estimated_cost
    
    def _save_entry_to_disk(self, entry: CacheEntry) -> None:
        """Save a cache entry to disk"""
        try:
            file_path = self.cache_dir / f"{entry.key}.json"
            with open(file_path, 'w') as f:
                json.dump(entry.to_dict(), f)
        except Exception as e:
            print(f"Failed to save cache entry to disk: {e}")
    
    def _load_persistent_cache(self) -> None:
        """Load cache from disk on initialization"""
        try:
            loaded_count = 0
            for file_path in self.cache_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        entry = CacheEntry.from_dict(data)
                        
                        # Only load non-expired entries
                        if not entry.is_expired():
                            self.memory_cache[entry.key] = entry
                            loaded_count += 1
                            
                            # Respect memory limit
                            if loaded_count >= self.max_memory_entries:
                                break
                        else:
                            # Clean up expired file
                            file_path.unlink()
                            
                except Exception as e:
                    print(f"Failed to load cache file {file_path}: {e}")
                    
            if loaded_count > 0:
                print(f"Loaded {loaded_count} cache entries from disk")
                
        except Exception as e:
            print(f"Failed to load persistent cache: {e}")
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.memory_cache.clear()
        
        # Clear disk cache if enabled
        if self.enable_persistence:
            for file_path in self.cache_dir.glob("*.json"):
                try:
                    file_path.unlink()
                except:
                    pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
            
            return {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate": f"{hit_rate:.1%}",
                "entries": len(self.memory_cache),
                "cost_saved": f"${self.stats['cost_saved']:.2f}",
                "api_calls_saved": self.stats["api_calls_saved"],
                "memory_usage_mb": self._estimate_memory_usage()
            }
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        try:
            # Rough estimate based on entry count and average size
            avg_entry_size = 2048  # bytes (conservative estimate)
            total_bytes = len(self.memory_cache) * avg_entry_size
            return total_bytes / (1024 * 1024)
        except:
            return 0.0
    
    def export_metrics(self) -> str:
        """Export cache metrics in a readable format"""
        stats = self.get_stats()
        
        return f"""
═══════════════════════════════════════════════════════
                 CACHE PERFORMANCE METRICS
═══════════════════════════════════════════════════════
  Cache Strategy: {self.strategy.value}
  Hit Rate: {stats['hit_rate']}
  Total Hits: {stats['hits']:,}
  Total Misses: {stats['misses']:,}
  
  Cached Entries: {stats['entries']:,} / {self.max_memory_entries:,}
  Memory Usage: ~{stats['memory_usage_mb']:.1f} MB
  
  💰 Cost Savings:
  - Estimated Savings: {stats['cost_saved']}
  - API Calls Saved: {stats['api_calls_saved']:,}
═══════════════════════════════════════════════════════
"""

# Singleton instance for global access
_cache_instance: Optional[ResponseCache] = None

def get_cache() -> ResponseCache:
    """Get or create the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResponseCache()
    return _cache_instance

def configure_cache(**kwargs) -> ResponseCache:
    """Configure and return the global cache instance"""
    global _cache_instance
    _cache_instance = ResponseCache(**kwargs)
    return _cache_instance

# Example integration with agent runtime
def cached_agent_call(
    agent_name: str,
    prompt: str,
    model: str,
    agent_function,
    use_cache: bool = True,
    ttl: int = 3600
) -> str:
    """
    Wrapper function for cached agent calls
    
    Args:
        agent_name: Name of the agent
        prompt: The prompt to send
        model: Model to use
        agent_function: The actual agent function to call
        use_cache: Whether to use caching
        ttl: Cache time-to-live
        
    Returns:
        The agent response (cached or fresh)
    """
    cache = get_cache()
    
    # Check cache if enabled
    if use_cache:
        cached_response = cache.get(prompt, agent_name, model)
        if cached_response:
            print(f"✨ Cache hit for {agent_name} (saved API call)")
            return cached_response
    
    # Make actual API call
    response = agent_function(prompt)
    
    # Cache the response
    if use_cache and response:
        cache.set(prompt, response, agent_name, model, ttl)
    
    return response

if __name__ == "__main__":
    # Demo and testing
    print("Response Cache System - Demo")
    print("=" * 50)
    
    # Initialize cache with custom settings
    cache = configure_cache(
        max_memory_entries=500,
        default_ttl=7200,  # 2 hours
        strategy=CacheStrategy.HYBRID,
        similarity_threshold=0.8
    )
    
    # Simulate some agent calls
    test_prompts = [
        ("rapid-builder", "Create a FastAPI endpoint for user registration", "claude-sonnet-4"),
        ("frontend-specialist", "Build a React login form with TypeScript", "claude-sonnet-4"),
        ("rapid-builder", "Create FastAPI endpoint for user signup", "claude-sonnet-4"),  # Similar to first
        ("ai-specialist", "Implement GPT-4 integration", "claude-opus-4"),
    ]
    
    print("\nSimulating agent calls with caching...")
    for agent, prompt, model in test_prompts:
        # First call - cache miss
        response = cache.get(prompt, agent, model)
        if response is None:
            print(f"  ❌ Cache miss: {agent} - '{prompt[:50]}...'")
            # Simulate API response
            cache.set(prompt, f"Response for: {prompt}", agent, model)
        else:
            print(f"  ✅ Cache hit: {agent} - '{prompt[:50]}...'")
    
    print("\nTrying similar prompts (semantic matching)...")
    # Should find semantic match for "signup" -> "registration"
    similar_response = cache.get(
        "Create FastAPI endpoint for user signup",
        "rapid-builder",
        "claude-sonnet-4"
    )
    if similar_response:
        print(f"  ✅ Semantic match found!")
    
    # Display statistics
    print(cache.export_metrics())