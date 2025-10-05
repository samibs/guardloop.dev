#!/usr/bin/env python3
"""Test pre-warm cache performance."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from guardrail.utils.config import get_config
from guardrail.core.daemon import GuardrailDaemon

def test_prewarm():
    """Test pre-warm cache initialization."""

    print("=" * 60)
    print("TESTING PRE-WARM CACHE")
    print("=" * 60)

    # Test initialization time
    start = time.time()
    config = get_config()
    daemon = GuardrailDaemon(config)
    init_time = (time.time() - start) * 1000

    print(f"\nInitialization Results:")
    print(f"  Total time: {init_time:.2f}ms")
    print(f"  Cache entries: {len(daemon.context_manager.cache._cache)}")
    print(f"  Cache keys: {list(daemon.context_manager.cache._cache.keys())}")

    # Test request without cache (should be fast now)
    print(f"\nTesting request after pre-warm:")
    start = time.time()
    context = daemon.context_manager.build_context(
        prompt="Hello, world!",
        agent=None,
        mode="standard",
        task_type="unknown"
    )
    request_time = (time.time() - start) * 1000

    print(f"  Context build time: {request_time:.2f}ms")
    print(f"  Context size: {len(context)} chars")
    print(f"  Was cached: {request_time < 5.0}")  # Should be <5ms if cached

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_prewarm()
