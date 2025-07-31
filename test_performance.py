#!/usr/bin/env python3
"""
Performance testing script to measure /data/{id} endpoint performance
"""

import asyncio
import aiohttp
import time
import statistics
from typing import List
import json

async def fetch_data(session: aiohttp.ClientSession, base_url: str, item_id: str) -> float:
    """Fetch a single item and return response time"""
    start_time = time.time()
    try:
        async with session.get(f"{base_url}/data/{item_id}") as response:
            await response.json()
            return time.time() - start_time
    except Exception as e:
        print(f"Error fetching {item_id}: {e}")
        return -1

async def create_test_data(session: aiohttp.ClientSession, base_url: str, num_items: int):
    """Create test data items"""
    print(f"Creating {num_items} test items...")
    for i in range(num_items):
        data = {
            "id": f"test_item_{i}",
            "value": {
                "name": f"Test Item {i}",
                "description": f"This is test item number {i}",
                "tags": ["test", "performance", f"item_{i}"],
                "metadata": {
                    "created_by": "performance_test",
                    "index": i
                }
            }
        }
        async with session.post(f"{base_url}/data", json=data) as response:
            if response.status != 200:
                print(f"Failed to create item {i}: {response.status}")

async def run_performance_test(base_url: str = "http://localhost:8000", 
                              num_items: int = 100, 
                              num_requests: int = 500,
                              concurrent_requests: int = 10):
    """Run performance test with concurrent requests"""
    
    async with aiohttp.ClientSession() as session:
        # Create test data
        await create_test_data(session, base_url, num_items)
        
        print(f"\nRunning performance test...")
        print(f"- Total requests: {num_requests}")
        print(f"- Concurrent requests: {concurrent_requests}")
        print(f"- Test items: {num_items}")
        
        # Prepare request tasks
        tasks = []
        for i in range(num_requests):
            item_id = f"test_item_{i % num_items}"  # Cycle through test items
            tasks.append(fetch_data(session, base_url, item_id))
        
        # Run requests with concurrency limit
        start_time = time.time()
        response_times = []
        
        for i in range(0, len(tasks), concurrent_requests):
            batch = tasks[i:i + concurrent_requests]
            batch_results = await asyncio.gather(*batch)
            response_times.extend([t for t in batch_results if t > 0])
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            p99_response_time = statistics.quantiles(response_times, n=100)[98]  # 99th percentile
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            print("\n=== Performance Test Results ===")
            print(f"Total test duration: {total_time:.2f} seconds")
            print(f"Successful requests: {len(response_times)}/{num_requests}")
            print(f"Requests per second: {len(response_times)/total_time:.2f}")
            print(f"\nResponse Time Statistics (seconds):")
            print(f"  Average: {avg_response_time:.4f}")
            print(f"  Median: {median_response_time:.4f}")
            print(f"  Min: {min_response_time:.4f}")
            print(f"  Max: {max_response_time:.4f}")
            print(f"  95th percentile: {p95_response_time:.4f}")
            print(f"  99th percentile: {p99_response_time:.4f}")
            
            # Check cache effectiveness (second run should be faster)
            print("\n=== Testing Cache Effectiveness ===")
            print("Running second test (should hit cache)...")
            
            cached_times = []
            for i in range(min(50, num_requests)):
                item_id = f"test_item_{i % num_items}"
                response_time = await fetch_data(session, base_url, item_id)
                if response_time > 0:
                    cached_times.append(response_time)
            
            if cached_times:
                avg_cached_time = statistics.mean(cached_times)
                print(f"Average response time (cached): {avg_cached_time:.4f} seconds")
                print(f"Cache speedup: {avg_response_time/avg_cached_time:.2f}x faster")

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    num_items = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    num_requests = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    concurrent_requests = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    
    asyncio.run(run_performance_test(base_url, num_items, num_requests, concurrent_requests))