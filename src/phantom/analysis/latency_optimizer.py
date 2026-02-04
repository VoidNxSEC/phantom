"""
CORTEX - Latency Optimization & Caching

Performance optimizations for faster query processing
"""

import asyncio
import hashlib
import time
from typing import Any

# ═══════════════════════════════════════════════════════════════
# QUERY CACHE
# ═══════════════════════════════════════════════════════════════


class QueryCache:
    """LRU cache for semantic search queries"""

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 3600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache: dict[str, tuple[Any, float]] = {}

    def _make_key(self, query: str, top_k: int) -> str:
        """Generate cache key"""
        data = f"{query}:{top_k}".encode()
        return hashlib.sha256(data).hexdigest()[:16]

    def get(self, query: str, top_k: int) -> Any | None:
        """Get cached result"""
        key = self._make_key(query, top_k)

        if key not in self.cache:
            return None

        result, timestamp = self.cache[key]

        # Check TTL
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            return None

        return result

    def set(self, query: str, top_k: int, result: Any):
        """Cache result"""
        key = self._make_key(query, top_k)

        # LRU eviction
        if len(self.cache) >= self.maxsize:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]

        self.cache[key] = (result, time.time())

    def clear(self):
        """Clear all cache"""
        self.cache.clear()

    def stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "ttl_seconds": self.ttl_seconds,
            "hit_rate": "N/A",  # Would need hit/miss tracking
        }


# ═══════════════════════════════════════════════════════════════
# CONNECTION POOLING
# ═══════════════════════════════════════════════════════════════


class ConnectionPool:
    """HTTP connection pooling for external APIs"""

    def __init__(self):
        self.sessions = {}

    async def get_session(self, provider: str):
        """Get or create session for provider"""
        # Placeholder - would use httpx.AsyncClient in production
        if provider not in self.sessions:
            self.sessions[provider] = {"created_at": time.time()}

        return self.sessions[provider]

    async def close_all(self):
        """Close all sessions"""
        self.sessions.clear()


# ═══════════════════════════════════════════════════════════════
# BATCH PROCESSING
# ═══════════════════════════════════════════════════════════════


class BatchProcessor:
    """Batch processing for embeddings and search"""

    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self.queue = []

    def add(self, item: Any):
        """Add item to batch queue"""
        self.queue.append(item)

        if len(self.queue) >= self.batch_size:
            return self.flush()

        return None

    def flush(self) -> list[Any]:
        """Process all queued items"""
        batch = self.queue[:]
        self.queue.clear()
        return batch


# ═══════════════════════════════════════════════════════════════
# PARALLEL SEARCH
# ═══════════════════════════════════════════════════════════════


async def parallel_semantic_search(
    queries: list[str], search_func, top_k: int = 5
) -> list[list[Any]]:
    """
    Execute multiple semantic searches in parallel

    Args:
        queries: List of search queries
        search_func: Search function to call
        top_k: Number of results per query

    Returns:
        List of search results for each query
    """
    tasks = [asyncio.to_thread(search_func, query, top_k) for query in queries]

    results = await asyncio.gather(*tasks)
    return results


# ═══════════════════════════════════════════════════════════════
# METRICS
# ═══════════════════════════════════════════════════════════════


class LatencyOptimizer:
    """Facade combining cache, connection pool, batch processing, and metrics."""

    def __init__(self, cache_maxsize: int = 1000, cache_ttl: int = 3600, batch_size: int = 32):
        self.cache = QueryCache(maxsize=cache_maxsize, ttl_seconds=cache_ttl)
        self.pool = ConnectionPool()
        self.batch = BatchProcessor(batch_size=batch_size)
        self.metrics = LatencyMetrics()

    def cached_search(self, query: str, top_k: int, search_func) -> Any:
        """Execute search with cache layer and latency tracking."""
        start = time.perf_counter()
        result = self.cache.get(query, top_k)
        if result is None:
            result = search_func(query, top_k)
            self.cache.set(query, top_k, result)
        self.metrics.record("search", (time.perf_counter() - start) * 1000)
        return result

    def stats(self) -> dict[str, Any]:
        return {
            "cache": self.cache.stats(),
            "metrics": self.metrics.get_stats(),
        }


class LatencyMetrics:
    """Track query latency metrics"""

    def __init__(self):
        self.queries = []
        self.max_history = 1000

    def record(self, query_type: str, latency_ms: float):
        """Record query latency"""
        self.queries.append(
            {"type": query_type, "latency_ms": latency_ms, "timestamp": time.time()}
        )

        # Keep only recent queries
        if len(self.queries) > self.max_history:
            self.queries = self.queries[-self.max_history :]

    def get_stats(self, query_type: str | None = None) -> dict[str, float]:
        """Get latency statistics"""
        queries = self.queries

        if query_type:
            queries = [q for q in queries if q["type"] == query_type]

        if not queries:
            return {"count": 0}

        latencies = [q["latency_ms"] for q in queries]

        return {
            "count": len(latencies),
            "avg_ms": sum(latencies) / len(latencies),
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "p50_ms": sorted(latencies)[len(latencies) // 2],
            "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)],
        }
