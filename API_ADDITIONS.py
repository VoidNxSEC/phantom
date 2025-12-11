# Add after line 29 in cortex_api.py

from latency_optimizer import QueryCache, LatencyMetrics, parallel_semantic_search
from prompt_workbench import PromptWorkbench, PromptTest, TestResult
from cloud_providers import CloudProviderClient, LLMConfig, get_available_models

# Initialize optimization tools
_query_cache = QueryCache(maxsize=1000, ttl_seconds=3600)
_metrics = LatencyMetrics()
_workbench = PromptWorkbench()

# File processing queue
_processing_queue: Dict[str, Dict] = {}
