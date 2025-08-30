#!/usr/bin/env python3
"""
Performance Optimizer - Production performance optimization for agent swarm

Features:
- Response caching with TTL and LRU eviction
- Database query optimization and connection pooling
- Concurrent execution tuning with resource management
- Memory management and garbage collection
- API call batching and request coalescing
"""

import os
import json
import time
import asyncio
import hashlib
import pickle
import gc
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import multiprocessing
from functools import wraps, lru_cache
from contextlib import contextmanager

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    print("Warning: redis not installed. Install with: pip install redis")

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    print("Warning: aiohttp not installed. Install with: pip install aiohttp")


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    cache_hits: int = 0
    cache_misses: int = 0
    avg_response_time: float = 0.0
    peak_memory_usage: float = 0.0
    concurrent_executions: int = 0
    api_calls_batched: int = 0
    queries_optimized: int = 0


class ResponseCache:
    """Multi-tier caching system with TTL and LRU eviction"""
    
    def __init__(self, max_memory_mb: int = 500, redis_url: str = None):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.memory_cache = OrderedDict()
        self.cache_lock = threading.Lock()
        self.metrics = PerformanceMetrics()
        
        # Redis for distributed cache
        self.redis_client = None
        if HAS_REDIS and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.redis_client = None
        
        # File-based cache for persistence
        self.cache_dir = Path("./cache/responses")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def _generate_key(self, prefix: str, params: Dict) -> str:
        """Generate cache key from parameters"""
        # Sort params for consistent hashing
        sorted_params = json.dumps(params, sort_keys=True)
        hash_val = hashlib.sha256(f"{prefix}:{sorted_params}".encode()).hexdigest()
        return f"{prefix}:{hash_val[:16]}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (checks all tiers)"""
        # Check memory cache first
        with self.cache_lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if datetime.now() < entry.expires_at:
                    # Move to end (LRU)
                    self.memory_cache.move_to_end(key)
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    self.metrics.cache_hits += 1
                    return entry.value
                else:
                    # Expired
                    del self.memory_cache[key]
        
        # Check Redis cache
        if self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    value = pickle.loads(cached)
                    self.metrics.cache_hits += 1
                    # Promote to memory cache
                    self._add_to_memory_cache(key, value, ttl_seconds=300)
                    return value
            except Exception:
                pass
        
        # Check file cache
        cache_file = self.cache_dir / f"{key.replace(':', '_')}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    entry = pickle.load(f)
                    if datetime.now() < entry.expires_at:
                        self.metrics.cache_hits += 1
                        # Promote to memory cache
                        self._add_to_memory_cache(key, entry.value, ttl_seconds=300)
                        return entry.value
                    else:
                        cache_file.unlink()
            except Exception:
                pass
        
        self.metrics.cache_misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set value in cache with TTL"""
        # Add to memory cache
        self._add_to_memory_cache(key, value, ttl_seconds)
        
        # Add to Redis if available
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key, ttl_seconds, pickle.dumps(value)
                )
            except Exception:
                pass
        
        # Add to file cache for persistence
        self._add_to_file_cache(key, value, ttl_seconds)
    
    def _add_to_memory_cache(self, key: str, value: Any, ttl_seconds: int):
        """Add entry to memory cache with LRU eviction"""
        try:
            size_bytes = len(pickle.dumps(value))
        except:
            size_bytes = 1000  # Default size estimate
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
            size_bytes=size_bytes
        )
        
        with self.cache_lock:
            # Check memory limit
            current_size = sum(e.size_bytes for e in self.memory_cache.values())
            
            # Evict LRU entries if needed
            while current_size + size_bytes > self.max_memory_bytes and self.memory_cache:
                oldest_key = next(iter(self.memory_cache))
                oldest_entry = self.memory_cache.pop(oldest_key)
                current_size -= oldest_entry.size_bytes
            
            # Add new entry
            self.memory_cache[key] = entry
    
    def _add_to_file_cache(self, key: str, value: Any, ttl_seconds: int):
        """Add entry to file cache"""
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
            size_bytes=0
        )
        
        cache_file = self.cache_dir / f"{key.replace(':', '_')}.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(entry, f)
        except Exception:
            pass
    
    def _cleanup_worker(self):
        """Background thread for cache cleanup"""
        while True:
            time.sleep(60)  # Clean every minute
            
            # Clean expired memory entries
            with self.cache_lock:
                expired_keys = [
                    k for k, v in self.memory_cache.items()
                    if datetime.now() > v.expires_at
                ]
                for key in expired_keys:
                    del self.memory_cache[key]
            
            # Clean expired file entries
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(cache_file, "rb") as f:
                        entry = pickle.load(f)
                        if datetime.now() > entry.expires_at:
                            cache_file.unlink()
                except Exception:
                    pass
    
    def invalidate(self, pattern: str = None):
        """Invalidate cache entries matching pattern"""
        if pattern:
            # Invalidate specific pattern
            with self.cache_lock:
                keys_to_delete = [k for k in self.memory_cache if pattern in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
            
            # Redis invalidation
            if self.redis_client:
                try:
                    for key in self.redis_client.scan_iter(f"*{pattern}*"):
                        self.redis_client.delete(key)
                except Exception:
                    pass
        else:
            # Clear all
            with self.cache_lock:
                self.memory_cache.clear()
            
            if self.redis_client:
                try:
                    self.redis_client.flushdb()
                except Exception:
                    pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.cache_lock:
            memory_size = sum(e.size_bytes for e in self.memory_cache.values())
            
        return {
            "memory_cache_size": len(self.memory_cache),
            "memory_usage_mb": memory_size / (1024 * 1024),
            "cache_hit_rate": self.metrics.cache_hits / max(1, self.metrics.cache_hits + self.metrics.cache_misses),
            "total_hits": self.metrics.cache_hits,
            "total_misses": self.metrics.cache_misses,
            "file_cache_size": len(list(self.cache_dir.glob("*.pkl"))),
            "redis_available": self.redis_client is not None
        }


class QueryOptimizer:
    """Database query optimization and connection pooling"""
    
    def __init__(self, max_connections: int = 20):
        self.max_connections = max_connections
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.query_cache = {}
        self.query_plans = {}
        self.slow_query_threshold = 1.0  # seconds
        self.metrics = PerformanceMetrics()
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = None
        try:
            with self.pool_lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()
                else:
                    # Create new connection (mock for demo)
                    conn = {"id": len(self.connection_pool), "created_at": time.time()}
            
            yield conn
        finally:
            if conn:
                with self.pool_lock:
                    if len(self.connection_pool) < self.max_connections:
                        self.connection_pool.append(conn)
    
    def optimize_query(self, query: str, params: Dict = None) -> Tuple[str, Dict]:
        """Optimize SQL query"""
        # Generate query fingerprint
        fingerprint = hashlib.md5(query.encode()).hexdigest()
        
        # Check if we have a cached plan
        if fingerprint in self.query_plans:
            self.metrics.queries_optimized += 1
            return self.query_plans[fingerprint]
        
        # Perform optimizations
        optimized_query = query
        optimized_params = params or {}
        
        # Add LIMIT if not present for SELECT
        if "SELECT" in query.upper() and "LIMIT" not in query.upper():
            optimized_query += " LIMIT 1000"
        
        # Add index hints for common patterns
        if "WHERE" in query.upper():
            # Suggest indexes (in real implementation, analyze actual schema)
            pass
        
        # Cache the plan
        self.query_plans[fingerprint] = (optimized_query, optimized_params)
        self.metrics.queries_optimized += 1
        
        return optimized_query, optimized_params
    
    def execute_query(self, query: str, params: Dict = None, cache_ttl: int = 60):
        """Execute query with caching and optimization"""
        # Check cache first
        cache_key = f"query:{hashlib.md5(f'{query}:{params}'.encode()).hexdigest()}"
        
        if cache_key in self.query_cache:
            cache_entry = self.query_cache[cache_key]
            if time.time() - cache_entry["timestamp"] < cache_ttl:
                return cache_entry["result"]
        
        # Optimize query
        optimized_query, optimized_params = self.optimize_query(query, params)
        
        # Execute (mock for demo)
        start_time = time.time()
        
        with self.get_connection() as conn:
            # Simulate query execution
            time.sleep(0.01)  # Simulate query time
            result = {"data": f"Result for {optimized_query[:50]}...", "rows": 100}
        
        execution_time = time.time() - start_time
        
        # Log slow queries
        if execution_time > self.slow_query_threshold:
            self._log_slow_query(query, execution_time)
        
        # Cache result
        self.query_cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }
        
        return result
    
    def _log_slow_query(self, query: str, execution_time: float):
        """Log slow queries for analysis"""
        log_file = Path("./logs/slow_queries.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()} - {execution_time:.2f}s - {query[:100]}...\n")
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze query performance"""
        return {
            "connection_pool_size": len(self.connection_pool),
            "max_connections": self.max_connections,
            "cached_queries": len(self.query_cache),
            "optimized_queries": self.metrics.queries_optimized,
            "query_plans_cached": len(self.query_plans)
        }


class ConcurrentExecutor:
    """Concurrent execution manager with resource optimization"""
    
    def __init__(self, max_workers: int = None, max_memory_gb: float = 2.0):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        
        # Thread pool for I/O bound tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Process pool for CPU bound tasks
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers // 2)
        
        # Semaphore for resource control
        self.resource_semaphore = asyncio.Semaphore(self.max_workers)
        
        # Task tracking
        self.active_tasks = set()
        self.task_metrics = defaultdict(list)
        self.metrics = PerformanceMetrics()
    
    async def execute_concurrent(self, tasks: List[Callable], task_type: str = "io") -> List[Any]:
        """Execute tasks concurrently with resource management"""
        results = []
        
        # Monitor memory before execution
        memory_before = psutil.Process().memory_info().rss
        
        if task_type == "io":
            # Use thread pool for I/O bound tasks
            results = await self._execute_io_tasks(tasks)
        elif task_type == "cpu":
            # Use process pool for CPU bound tasks
            results = await self._execute_cpu_tasks(tasks)
        elif task_type == "mixed":
            # Intelligently distribute tasks
            results = await self._execute_mixed_tasks(tasks)
        
        # Monitor memory after execution
        memory_after = psutil.Process().memory_info().rss
        memory_used = memory_after - memory_before
        
        # Update metrics
        self.metrics.peak_memory_usage = max(self.metrics.peak_memory_usage, memory_used)
        self.metrics.concurrent_executions += len(tasks)
        
        # Trigger GC if memory usage is high
        if memory_used > self.max_memory_bytes * 0.8:
            gc.collect()
        
        return results
    
    async def _execute_io_tasks(self, tasks: List[Callable]) -> List[Any]:
        """Execute I/O bound tasks"""
        async def run_with_semaphore(task):
            async with self.resource_semaphore:
                self.active_tasks.add(id(task))
                start_time = time.time()
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(self.thread_pool, task)
                    return result
                finally:
                    self.active_tasks.discard(id(task))
                    self.task_metrics["io"].append(time.time() - start_time)
        
        return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])
    
    async def _execute_cpu_tasks(self, tasks: List[Callable]) -> List[Any]:
        """Execute CPU bound tasks"""
        async def run_with_semaphore(task):
            async with self.resource_semaphore:
                self.active_tasks.add(id(task))
                start_time = time.time()
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(self.process_pool, task)
                    return result
                finally:
                    self.active_tasks.discard(id(task))
                    self.task_metrics["cpu"].append(time.time() - start_time)
        
        return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])
    
    async def _execute_mixed_tasks(self, tasks: List[Callable]) -> List[Any]:
        """Intelligently distribute mixed tasks"""
        io_tasks = []
        cpu_tasks = []
        
        # Simple heuristic: alternate between pools
        for i, task in enumerate(tasks):
            if i % 3 == 0:  # Every third task to CPU pool
                cpu_tasks.append(task)
            else:
                io_tasks.append(task)
        
        # Execute both types concurrently
        io_results = []
        cpu_results = []
        
        if io_tasks:
            io_results = await self._execute_io_tasks(io_tasks)
        if cpu_tasks:
            cpu_results = await self._execute_cpu_tasks(cpu_tasks)
        
        # Merge results maintaining order
        results = []
        io_idx = 0
        cpu_idx = 0
        
        for i in range(len(tasks)):
            if i % 3 == 0 and cpu_idx < len(cpu_results):
                results.append(cpu_results[cpu_idx])
                cpu_idx += 1
            elif io_idx < len(io_results):
                results.append(io_results[io_idx])
                io_idx += 1
        
        return results
    
    def optimize_concurrency(self) -> Dict[str, Any]:
        """Optimize concurrency settings based on system resources"""
        # Get system info
        cpu_count = multiprocessing.cpu_count()
        memory_available = psutil.virtual_memory().available
        
        # Calculate optimal workers
        optimal_thread_workers = min(cpu_count * 2, 32)  # 2x CPU for I/O
        optimal_process_workers = max(cpu_count - 1, 1)  # Leave 1 CPU free
        
        # Adjust based on memory
        memory_per_worker = 100 * 1024 * 1024  # 100MB per worker estimate
        max_workers_by_memory = int(memory_available / memory_per_worker)
        
        optimal_thread_workers = min(optimal_thread_workers, max_workers_by_memory)
        optimal_process_workers = min(optimal_process_workers, max_workers_by_memory // 2)
        
        return {
            "current_thread_workers": self.thread_pool._max_workers,
            "optimal_thread_workers": optimal_thread_workers,
            "current_process_workers": self.process_pool._max_workers,
            "optimal_process_workers": optimal_process_workers,
            "active_tasks": len(self.active_tasks),
            "memory_available_gb": memory_available / (1024**3)
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        io_times = self.task_metrics.get("io", [])
        cpu_times = self.task_metrics.get("cpu", [])
        
        return {
            "total_tasks_executed": self.metrics.concurrent_executions,
            "active_tasks": len(self.active_tasks),
            "avg_io_task_time": sum(io_times) / len(io_times) if io_times else 0,
            "avg_cpu_task_time": sum(cpu_times) / len(cpu_times) if cpu_times else 0,
            "peak_memory_usage_mb": self.metrics.peak_memory_usage / (1024**2),
            "thread_pool_workers": self.thread_pool._max_workers,
            "process_pool_workers": self.process_pool._max_workers
        }


class MemoryManager:
    """Memory management and garbage collection optimization"""
    
    def __init__(self, target_memory_mb: int = 1000, gc_threshold: float = 0.8):
        self.target_memory_bytes = target_memory_mb * 1024 * 1024
        self.gc_threshold = gc_threshold
        self.monitoring = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_memory(self):
        """Monitor memory usage and trigger GC when needed"""
        while self.monitoring:
            time.sleep(5)  # Check every 5 seconds
            
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = memory_info.rss / self.target_memory_bytes
            
            if memory_percent > self.gc_threshold:
                # Trigger garbage collection
                collected = gc.collect()
                
                # Log if significant collection
                if collected > 100:
                    print(f"GC collected {collected} objects at {memory_percent:.1%} memory usage")
    
    @contextmanager
    def memory_limit(self, limit_mb: int):
        """Context manager to limit memory for a block"""
        import resource
        
        if hasattr(resource, 'RLIMIT_AS'):
            # Unix-like systems
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            limit_bytes = limit_mb * 1024 * 1024
            
            try:
                resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, hard))
                yield
            finally:
                resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
        else:
            # Windows - no direct equivalent
            yield
    
    def optimize_gc(self):
        """Optimize garbage collection settings"""
        # Adjust GC thresholds for better performance
        # (generation0, generation1, generation2)
        gc.set_threshold(700, 10, 10)  # Default is (700, 10, 10)
        
        # Enable GC stats
        gc.set_debug(gc.DEBUG_STATS)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / (1024**2),
            "vms_mb": memory_info.vms / (1024**2),
            "percent_of_target": (memory_info.rss / self.target_memory_bytes) * 100,
            "gc_count": gc.get_count(),
            "gc_stats": gc.get_stats(),
            "objects_tracked": len(gc.get_objects())
        }


class APIBatcher:
    """API call batching and request coalescing"""
    
    def __init__(self, batch_size: int = 10, batch_timeout_ms: int = 100):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout_ms / 1000.0
        self.pending_requests = defaultdict(list)
        self.request_lock = threading.Lock()
        self.batch_events = defaultdict(asyncio.Event)
        self.metrics = PerformanceMetrics()
    
    async def add_request(self, endpoint: str, params: Dict) -> Any:
        """Add request to batch"""
        request_id = hashlib.md5(f"{endpoint}:{json.dumps(params)}".encode()).hexdigest()
        
        with self.request_lock:
            batch_key = endpoint
            self.pending_requests[batch_key].append({
                "id": request_id,
                "params": params,
                "future": asyncio.Future()
            })
            
            # Check if batch is ready
            if len(self.pending_requests[batch_key]) >= self.batch_size:
                asyncio.create_task(self._execute_batch(batch_key))
            elif len(self.pending_requests[batch_key]) == 1:
                # First request in batch, start timer
                asyncio.create_task(self._batch_timer(batch_key))
        
        # Wait for result
        for req in self.pending_requests[batch_key]:
            if req["id"] == request_id:
                return await req["future"]
    
    async def _batch_timer(self, batch_key: str):
        """Timer to execute batch after timeout"""
        await asyncio.sleep(self.batch_timeout)
        await self._execute_batch(batch_key)
    
    async def _execute_batch(self, batch_key: str):
        """Execute batched requests"""
        with self.request_lock:
            if batch_key not in self.pending_requests:
                return
            
            batch = self.pending_requests.pop(batch_key)
            if not batch:
                return
        
        # Execute batch request
        try:
            # Combine all params into single request
            combined_params = [req["params"] for req in batch]
            
            # Make batch API call (mock for demo)
            results = await self._make_batch_call(batch_key, combined_params)
            
            # Distribute results
            for i, req in enumerate(batch):
                if i < len(results):
                    req["future"].set_result(results[i])
                else:
                    req["future"].set_exception(Exception("Batch result missing"))
            
            # Update metrics
            self.metrics.api_calls_batched += len(batch)
            
        except Exception as e:
            # Set exception for all requests
            for req in batch:
                req["future"].set_exception(e)
    
    async def _make_batch_call(self, endpoint: str, params_list: List[Dict]) -> List[Any]:
        """Make actual batch API call"""
        # Mock implementation
        await asyncio.sleep(0.05)  # Simulate API call
        return [{"result": f"Response for {params}"} for params in params_list]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batching statistics"""
        return {
            "total_batched": self.metrics.api_calls_batched,
            "pending_batches": len(self.pending_requests),
            "batch_size": self.batch_size,
            "batch_timeout_ms": self.batch_timeout * 1000
        }


class PerformanceOptimizer:
    """Main performance optimization manager"""
    
    def __init__(self):
        self.cache = ResponseCache(max_memory_mb=500)
        self.query_optimizer = QueryOptimizer(max_connections=20)
        self.executor = ConcurrentExecutor()
        self.memory_manager = MemoryManager()
        self.api_batcher = APIBatcher()
        
        # Performance monitoring
        self.request_times = deque(maxlen=1000)
        
    def cache_response(self, key: str, response: Any, ttl: int = 3600):
        """Cache a response"""
        self.cache.set(key, response, ttl)
    
    def get_cached_response(self, key: str) -> Optional[Any]:
        """Get cached response"""
        return self.cache.get(key)
    
    async def execute_optimized(self, tasks: List[Callable], task_type: str = "io") -> List[Any]:
        """Execute tasks with optimization"""
        start_time = time.time()
        
        # Execute concurrently
        results = await self.executor.execute_concurrent(tasks, task_type)
        
        # Track performance
        execution_time = time.time() - start_time
        self.request_times.append(execution_time)
        
        return results
    
    async def batch_api_call(self, endpoint: str, params: Dict) -> Any:
        """Make batched API call"""
        return await self.api_batcher.add_request(endpoint, params)
    
    def optimize_system(self) -> Dict[str, Any]:
        """Perform system-wide optimization"""
        optimizations = {}
        
        # Optimize cache
        cache_stats = self.cache.get_stats()
        if cache_stats["cache_hit_rate"] < 0.5:
            optimizations["cache"] = "Consider increasing cache TTL or size"
        
        # Optimize concurrency
        concurrency_opts = self.executor.optimize_concurrency()
        optimizations["concurrency"] = concurrency_opts
        
        # Optimize memory
        self.memory_manager.optimize_gc()
        memory_stats = self.memory_manager.get_memory_stats()
        if memory_stats["percent_of_target"] > 90:
            optimizations["memory"] = "High memory usage, consider scaling"
        
        return optimizations
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        avg_response_time = sum(self.request_times) / len(self.request_times) if self.request_times else 0
        
        return {
            "avg_response_time_ms": avg_response_time * 1000,
            "cache_stats": self.cache.get_stats(),
            "query_performance": self.query_optimizer.analyze_performance(),
            "concurrency_stats": self.executor.get_performance_stats(),
            "memory_stats": self.memory_manager.get_memory_stats(),
            "batching_stats": self.api_batcher.get_stats(),
            "optimizations": self.optimize_system()
        }


# Decorators for easy integration
def cached(ttl: int = 3600):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            optimizer = PerformanceOptimizer()
            cached_result = optimizer.get_cached_response(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            optimizer.cache_response(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def optimized_query(cache_ttl: int = 60):
    """Decorator to optimize database queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(query: str, params: Dict = None):
            optimizer = PerformanceOptimizer()
            return optimizer.query_optimizer.execute_query(query, params, cache_ttl)
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        # Initialize optimizer
        optimizer = PerformanceOptimizer()
        
        # Test caching
        optimizer.cache_response("test_key", {"data": "test_value"}, ttl=60)
        cached = optimizer.get_cached_response("test_key")
        print(f"Cached value: {cached}")
        
        # Test concurrent execution
        async def sample_task(n):
            await asyncio.sleep(0.1)
            return n * 2
        
        tasks = [lambda n=i: sample_task(n) for i in range(10)]
        results = await optimizer.execute_optimized(tasks, "io")
        print(f"Concurrent results: {results}")
        
        # Test API batching
        batch_results = await asyncio.gather(*[
            optimizer.batch_api_call("/api/test", {"id": i})
            for i in range(15)
        ])
        print(f"Batched {len(batch_results)} API calls")
        
        # Generate performance report
        report = optimizer.get_performance_report()
        print(f"Performance Report: {json.dumps(report, indent=2)}")
    
    # Run demo
    asyncio.run(demo())