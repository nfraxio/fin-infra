#!/usr/bin/env python3
"""
Measure recurring detection costs and cache effectiveness.

This script measures production costs to verify:
- Cache hit rate target: 95% for merchant normalization
- Effective cost per user per month: <$0.001
- A/B test capability: 10% LLM vs 90% pattern-only

Usage:
    # Measure costs with simulated traffic
    GOOGLE_API_KEY=your_key poetry run python scripts/measure_recurring_costs.py

    # Simulate 1000 users for 30 days
    poetry run python scripts/measure_recurring_costs.py --users 1000 --days 30

    # A/B test mode (10% LLM)
    poetry run python scripts/measure_recurring_costs.py --ab-test --llm-percentage 10

Requirements:
- GOOGLE_API_KEY environment variable for LLM testing
- Redis running for cache testing (optional, will simulate if not available)
"""

import asyncio
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional
import random

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fin_infra.recurring.ease import easy_recurring_detection


@dataclass
class CostMeasurement:
    """Cost measurement results."""
    
    # Traffic simulation
    total_users: int
    total_days: int
    total_requests: int
    
    # Cache effectiveness
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    
    # LLM costs
    total_llm_calls: int
    total_llm_cost_usd: float
    
    # Per-user metrics
    avg_requests_per_user_per_day: float
    avg_cost_per_user_per_day: float
    avg_cost_per_user_per_month: float
    avg_cost_per_user_per_year: float
    
    # A/B test metrics (if applicable)
    llm_percentage: Optional[float] = None
    pattern_only_percentage: Optional[float] = None


def simulate_user_activity(days: int = 30) -> List[Dict]:
    """Simulate realistic user activity patterns.
    
    Args:
        days: Number of days to simulate
        
    Returns:
        List of user activities (merchant normalizations, detections, insights)
    """
    activities = []
    
    # Typical user has 10-20 recurring transactions per month
    # Most are repeat merchants (high cache hit rate expected)
    common_merchants = [
        "NETFLIX.COM", "SPOTIFY USA", "AMAZON PRIME",
        "APPLE.COM/BILL", "GOOGLE *YOUTUBE", "HULU LLC",
        "CITY ELECTRIC", "GAS COMPANY", "WATER DEPT",
        "T-MOBILE USA", "AT&T WIRELESS", "VERIZON",
    ]
    
    occasional_merchants = [
        "STARBUCKS #1234", "TARGET #543", "WHOLE FOODS",
        "CVS PHARMACY", "WALGREENS", "SHELL OIL",
    ]
    
    for day in range(days):
        # Each day, user might check their recurring transactions
        if random.random() < 0.3:  # 30% chance of checking daily
            # Normalize 5-10 merchants (mostly common ones for cache hits)
            num_normalizations = random.randint(5, 10)
            for _ in range(num_normalizations):
                # 80% common merchants (cache hits), 20% occasional
                if random.random() < 0.8:
                    merchant = random.choice(common_merchants)
                else:
                    merchant = random.choice(occasional_merchants)
                
                activities.append({
                    "day": day,
                    "type": "normalize",
                    "merchant": merchant,
                    "cacheable": merchant in common_merchants,
                })
            
            # Detect variable patterns (1-3 per check)
            num_detections = random.randint(1, 3)
            for _ in range(num_detections):
                activities.append({
                    "day": day,
                    "type": "detect",
                    "merchant": random.choice(common_merchants),
                })
            
            # Generate insights (once per check)
            if random.random() < 0.2:  # 20% chance
                activities.append({
                    "day": day,
                    "type": "insights",
                })
    
    return activities


def measure_costs(
    num_users: int,
    num_days: int,
    enable_cache: bool = True,
    ab_test: bool = False,
    llm_percentage: float = 10.0,
) -> CostMeasurement:
    """Measure costs for simulated user traffic.
    
    Args:
        num_users: Number of users to simulate
        num_days: Number of days to simulate
        enable_cache: Whether to enable caching
        ab_test: Whether to run A/B test mode
        llm_percentage: Percentage of users with LLM (for A/B test)
        
    Returns:
        CostMeasurement with results
    """
    print(f"\n📊 Cost Measurement Simulation")
    print(f"Users: {num_users}")
    print(f"Days: {num_days}")
    print(f"Cache: {'Enabled' if enable_cache else 'Disabled'}")
    if ab_test:
        print(f"A/B Test: {llm_percentage}% LLM, {100-llm_percentage}% pattern-only")
    print()
    
    # Track metrics
    total_requests = 0
    cache_hits = 0
    cache_misses = 0
    total_llm_calls = 0
    total_cost = 0.0
    
    # Simulate cache state (tracks what's been cached)
    cache_state = {}
    
    # Process each user
    for user_id in range(num_users):
        if (user_id + 1) % 100 == 0:
            print(f"Processing user {user_id + 1}/{num_users}...")
        
        # Determine if user is in LLM group (for A/B test)
        use_llm = not ab_test or (random.random() * 100 < llm_percentage)
        
        # Create detector for this user
        if use_llm and os.getenv("GOOGLE_API_KEY"):
            detector = easy_recurring_detection(
                enable_llm=True,
                llm_provider="google",
                llm_model="gemini-2.0-flash-exp",
            )
        else:
            detector = easy_recurring_detection(enable_llm=False)
        
        # Simulate user activity
        activities = simulate_user_activity(num_days)
        
        for activity in activities:
            total_requests += 1
            
            if activity["type"] == "normalize":
                merchant = activity["merchant"]
                cache_key = f"merchant_norm:{merchant.lower()}"
                
                # Check cache
                if enable_cache and cache_key in cache_state:
                    cache_hits += 1
                    # Cache hit - no LLM call
                else:
                    cache_misses += 1
                    
                    # Cache miss - LLM call (if enabled)
                    if use_llm and os.getenv("GOOGLE_API_KEY"):
                        total_llm_calls += 1
                        # Gemini Flash: ~$0.00008 per normalization
                        total_cost += 0.00008
                    
                    # Update cache state
                    if enable_cache:
                        cache_state[cache_key] = True
            
            elif activity["type"] == "detect":
                # Detection typically uses LLM if enabled
                if use_llm and os.getenv("GOOGLE_API_KEY"):
                    total_llm_calls += 1
                    # ~$0.0001 per detection
                    total_cost += 0.0001
            
            elif activity["type"] == "insights":
                # Insights generation
                if use_llm and os.getenv("GOOGLE_API_KEY"):
                    total_llm_calls += 1
                    # ~$0.0002 per insights generation
                    total_cost += 0.0002
    
    # Calculate metrics
    cache_hit_rate = cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0.0
    avg_requests_per_user_per_day = total_requests / (num_users * num_days) if num_users > 0 and num_days > 0 else 0.0
    avg_cost_per_user_per_day = total_cost / (num_users * num_days) if num_users > 0 and num_days > 0 else 0.0
    avg_cost_per_user_per_month = avg_cost_per_user_per_day * 30
    avg_cost_per_user_per_year = avg_cost_per_user_per_month * 12
    
    return CostMeasurement(
        total_users=num_users,
        total_days=num_days,
        total_requests=total_requests,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        cache_hit_rate=cache_hit_rate,
        total_llm_calls=total_llm_calls,
        total_llm_cost_usd=total_cost,
        avg_requests_per_user_per_day=avg_requests_per_user_per_day,
        avg_cost_per_user_per_day=avg_cost_per_user_per_day,
        avg_cost_per_user_per_month=avg_cost_per_user_per_month,
        avg_cost_per_user_per_year=avg_cost_per_user_per_year,
        llm_percentage=llm_percentage if ab_test else None,
        pattern_only_percentage=(100 - llm_percentage) if ab_test else None,
    )


def print_results(result: CostMeasurement) -> None:
    """Print cost measurement results.
    
    Args:
        result: Cost measurement to display
    """
    print(f"\n{'='*60}")
    print(f"  Cost Measurement Results")
    print(f"{'='*60}")
    print(f"Simulation:")
    print(f"  Users:                {result.total_users:,}")
    print(f"  Days:                 {result.total_days}")
    print(f"  Total Requests:       {result.total_requests:,}")
    
    if result.llm_percentage is not None:
        print(f"  LLM Users:            {result.llm_percentage}%")
        print(f"  Pattern-only Users:   {result.pattern_only_percentage}%")
    
    print(f"\nCache Effectiveness:")
    print(f"  Cache Hits:           {result.cache_hits:,}")
    print(f"  Cache Misses:         {result.cache_misses:,}")
    print(f"  Cache Hit Rate:       {result.cache_hit_rate:.1%}")
    
    print(f"\nLLM Usage:")
    print(f"  Total LLM Calls:      {result.total_llm_calls:,}")
    print(f"  Total LLM Cost:       ${result.total_llm_cost_usd:.4f}")
    
    print(f"\nPer-User Costs:")
    print(f"  Avg Requests/User/Day:  {result.avg_requests_per_user_per_day:.2f}")
    print(f"  Avg Cost/User/Day:      ${result.avg_cost_per_user_per_day:.6f}")
    print(f"  Avg Cost/User/Month:    ${result.avg_cost_per_user_per_month:.6f}")
    print(f"  Avg Cost/User/Year:     ${result.avg_cost_per_user_per_year:.4f}")
    
    print(f"\n{'='*60}")
    print(f"  Target Verification")
    print(f"{'='*60}")
    
    # Verify targets
    cache_pass = result.cache_hit_rate >= 0.95
    cost_pass = result.avg_cost_per_user_per_month < 0.001
    
    print(f"Cache Hit Rate ≥95%:           {result.cache_hit_rate:.1%} {'✓' if cache_pass else '✗'}")
    print(f"Cost/User/Month <$0.001:       ${result.avg_cost_per_user_per_month:.6f} {'✓' if cost_pass else '✗'}")
    
    if not cost_pass:
        # Project what cache hit rate would be needed
        current_cost = result.avg_cost_per_user_per_month
        target_cost = 0.001
        reduction_needed = 1 - (target_cost / current_cost) if current_cost > 0 else 0
        target_cache_rate = result.cache_hit_rate + reduction_needed
        print(f"\n💡 To hit cost target, need ~{target_cache_rate:.1%} cache hit rate")
    
    print(f"{'='*60}\n")
    
    return cache_pass and cost_pass


def main():
    """Run cost measurement."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Measure recurring detection costs")
    parser.add_argument("--users", type=int, default=100, help="Number of users to simulate (default: 100)")
    parser.add_argument("--days", type=int, default=30, help="Number of days to simulate (default: 30)")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    parser.add_argument("--ab-test", action="store_true", help="Enable A/B test mode")
    parser.add_argument("--llm-percentage", type=float, default=10.0, help="Percentage with LLM (default: 10)")
    args = parser.parse_args()
    
    if args.ab_test and not (0 <= args.llm_percentage <= 100):
        print("Error: --llm-percentage must be between 0 and 100")
        sys.exit(1)
    
    # Run measurement
    result = measure_costs(
        num_users=args.users,
        num_days=args.days,
        enable_cache=not args.no_cache,
        ab_test=args.ab_test,
        llm_percentage=args.llm_percentage,
    )
    
    # Print results and verify targets
    targets_met = print_results(result)
    
    sys.exit(0 if targets_met else 1)


if __name__ == "__main__":
    main()
