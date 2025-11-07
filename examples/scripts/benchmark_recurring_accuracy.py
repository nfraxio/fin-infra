#!/usr/bin/env python3
"""
Benchmark recurring detection accuracy: V2 (LLM) vs V1 (pattern-only).

This script measures detection accuracy on labeled transaction datasets to verify:
- Baseline (pattern-only): 85% accuracy, 8% false positives
- With LLM: Target 92%+ accuracy, <5% false positives
- Variable detection: 70% → 88% for utility bills with seasonal patterns
- Merchant grouping: 80% → 95% (handles name variants)

Usage:
    # Run with Google Gemini
    GOOGLE_API_KEY=your_key poetry run python scripts/benchmark_recurring_accuracy.py

    # Run with custom dataset
    poetry run python scripts/benchmark_recurring_accuracy.py --dataset path/to/labeled_data.json

    # Compare V1 vs V2
    poetry run python scripts/benchmark_recurring_accuracy.py --compare

Requirements:
- GOOGLE_API_KEY environment variable for V2 (LLM) testing
- Labeled dataset with ground truth recurring patterns
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fin_infra.recurring.ease import easy_recurring_detection


@dataclass
class BenchmarkResult:
    """Results from accuracy benchmark."""
    
    version: str  # "V1" or "V2"
    total_transactions: int
    correct_predictions: int
    accuracy: float
    false_positives: int
    false_negatives: int
    false_positive_rate: float
    false_negative_rate: float
    
    # Breakdown by category
    merchant_grouping_accuracy: float
    variable_detection_accuracy: float
    simple_pattern_accuracy: float
    
    # Performance metrics
    avg_processing_time_ms: float
    total_cost_usd: float


@dataclass
class LabeledTransaction:
    """Transaction with ground truth labels."""
    
    merchant_name: str
    canonical_merchant: str  # Ground truth canonical name
    amounts: List[float]
    dates: List[str]
    is_recurring: bool  # Ground truth
    pattern_type: str  # "simple", "variable", "seasonal"
    category: str  # "subscription", "utility", "other"


def load_default_dataset() -> List[LabeledTransaction]:
    """Load default labeled dataset for benchmarking.
    
    Returns:
        List of labeled transactions with ground truth.
    """
    return [
        # Merchant name normalization tests (20 variants)
        LabeledTransaction(
            merchant_name="NFLX*SUB #12345",
            canonical_merchant="netflix",
            amounts=[15.99] * 6,
            dates=["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01", "2024-06-01"],
            is_recurring=True,
            pattern_type="simple",
            category="subscription"
        ),
        LabeledTransaction(
            merchant_name="NETFLIX.COM",
            canonical_merchant="netflix",
            amounts=[15.99] * 6,
            dates=["2024-01-15", "2024-02-15", "2024-03-15", "2024-04-15", "2024-05-15", "2024-06-15"],
            is_recurring=True,
            pattern_type="simple",
            category="subscription"
        ),
        LabeledTransaction(
            merchant_name="Netflix Inc",
            canonical_merchant="netflix",
            amounts=[15.99] * 6,
            dates=["2024-01-20", "2024-02-20", "2024-03-20", "2024-04-20", "2024-05-20", "2024-06-20"],
            is_recurring=True,
            pattern_type="simple",
            category="subscription"
        ),
        LabeledTransaction(
            merchant_name="SQ *STARBUCKS #543",
            canonical_merchant="starbucks",
            amounts=[5.50] * 6,
            dates=["2024-01-05", "2024-02-05", "2024-03-05", "2024-04-05", "2024-05-05", "2024-06-05"],
            is_recurring=True,
            pattern_type="simple",
            category="subscription"
        ),
        LabeledTransaction(
            merchant_name="SPOTIFY USA",
            canonical_merchant="spotify",
            amounts=[10.99] * 6,
            dates=["2024-01-10", "2024-02-10", "2024-03-10", "2024-04-10", "2024-05-10", "2024-06-10"],
            is_recurring=True,
            pattern_type="simple",
            category="subscription"
        ),
        
        # Variable/seasonal utility bills (10 transactions)
        LabeledTransaction(
            merchant_name="City Electric Utility",
            canonical_merchant="city electric",
            amounts=[45.50, 52.30, 48.75, 54.20, 58.90, 62.40],
            dates=["2024-01-15", "2024-02-15", "2024-03-15", "2024-04-15", "2024-05-15", "2024-06-15"],
            is_recurring=True,
            pattern_type="seasonal",
            category="utility"
        ),
        LabeledTransaction(
            merchant_name="Natural Gas Company",
            canonical_merchant="gas company",
            amounts=[45.0, 120.0, 115.0, 85.0, 50.0, 40.0],
            dates=["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01", "2024-06-01"],
            is_recurring=True,
            pattern_type="seasonal",
            category="utility"
        ),
        LabeledTransaction(
            merchant_name="Water Dept",
            canonical_merchant="water utility",
            amounts=[35.0, 38.0, 36.5, 37.0, 35.5, 36.0],
            dates=["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01", "2024-05-01", "2024-06-01"],
            is_recurring=True,
            pattern_type="variable",
            category="utility"
        ),
        LabeledTransaction(
            merchant_name="T-Mobile USA",
            canonical_merchant="t-mobile",
            amounts=[50.0, 78.50, 50.0, 50.0, 50.0, 65.30],
            dates=["2024-01-15", "2024-02-15", "2024-03-15", "2024-04-15", "2024-05-15", "2024-06-15"],
            is_recurring=True,
            pattern_type="variable",
            category="utility"
        ),
        LabeledTransaction(
            merchant_name="AT&T Wireless",
            canonical_merchant="at&t",
            amounts=[65.0, 65.0, 92.0, 65.0, 65.0, 65.0],
            dates=["2024-01-20", "2024-02-20", "2024-03-20", "2024-04-20", "2024-05-20", "2024-06-20"],
            is_recurring=True,
            pattern_type="variable",
            category="utility"
        ),
        
        # Non-recurring patterns (false positive tests)
        LabeledTransaction(
            merchant_name="Random Store #123",
            canonical_merchant="random store",
            amounts=[25.0, 150.0, 40.0, 200.0, 15.0, 90.0],
            dates=["2024-01-05", "2024-02-12", "2024-03-20", "2024-04-08", "2024-05-15", "2024-06-02"],
            is_recurring=False,
            pattern_type="random",
            category="other"
        ),
        LabeledTransaction(
            merchant_name="Coffee Shop",
            canonical_merchant="coffee shop",
            amounts=[4.50, 12.0, 3.0, 25.0, 8.50, 15.0],
            dates=["2024-01-08", "2024-01-22", "2024-02-05", "2024-03-10", "2024-04-15", "2024-05-20"],
            is_recurring=False,
            pattern_type="random",
            category="other"
        ),
    ]


def benchmark_version(
    version: str,
    detector: "RecurringDetection",  # type: ignore
    dataset: List[LabeledTransaction],
) -> BenchmarkResult:
    """Run benchmark on a specific version (V1 or V2).
    
    Args:
        version: "V1" or "V2"
        detector: RecurringDetector instance
        dataset: Labeled transactions with ground truth
        
    Returns:
        BenchmarkResult with accuracy metrics
    """
    import time
    
    correct = 0
    false_positives = 0
    false_negatives = 0
    
    merchant_correct = 0
    merchant_total = 0
    variable_correct = 0
    variable_total = 0
    simple_correct = 0
    simple_total = 0
    
    processing_times = []
    total_cost = 0.0
    
    for txn in dataset:
        start = time.perf_counter()
        
        # Build transaction list for detector
        transactions = []
        for i, (amount, date) in enumerate(zip(txn.amounts, txn.dates)):
            transactions.append({
                "id": f"txn_{i}",
                "merchant": txn.merchant_name,
                "amount": amount,
                "date": date,
                "description": txn.merchant_name,
            })
        
        # Detect recurring patterns
        patterns = detector.detect_patterns(transactions)
        
        end = time.perf_counter()
        processing_times.append((end - start) * 1000)  # ms
        
        # Check if any recurring pattern was detected for this merchant
        predicted_recurring = len(patterns) > 0
        
        if predicted_recurring == txn.is_recurring:
            correct += 1
            
            # Category-specific accuracy
            if txn.pattern_type == "variable" or txn.pattern_type == "seasonal":
                variable_correct += 1
            elif txn.pattern_type == "simple":
                simple_correct += 1
        else:
            if predicted_recurring and not txn.is_recurring:
                false_positives += 1
            elif not predicted_recurring and txn.is_recurring:
                false_negatives += 1
        
        # Count totals by pattern type
        if txn.pattern_type == "variable" or txn.pattern_type == "seasonal":
            variable_total += 1
        elif txn.pattern_type == "simple":
            simple_total += 1
        
        merchant_total += 1
        
        # Check merchant normalization (if patterns found and LLM was enabled)
        if patterns and hasattr(patterns[0], "merchant"):
            predicted_canonical = patterns[0].merchant.lower()
            expected_canonical = txn.canonical_merchant.lower()
            if expected_canonical in predicted_canonical or predicted_canonical in expected_canonical:
                merchant_correct += 1
    
    # Calculate metrics
    total = len(dataset)
    accuracy = correct / total if total > 0 else 0.0
    fp_rate = false_positives / total if total > 0 else 0.0
    fn_rate = false_negatives / total if total > 0 else 0.0
    
    merchant_acc = merchant_correct / merchant_total if merchant_total > 0 else 0.0
    variable_acc = variable_correct / variable_total if variable_total > 0 else 0.0
    simple_acc = simple_correct / simple_total if simple_total > 0 else 0.0
    
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
    
    return BenchmarkResult(
        version=version,
        total_transactions=total,
        correct_predictions=correct,
        accuracy=accuracy,
        false_positives=false_positives,
        false_negatives=false_negatives,
        false_positive_rate=fp_rate,
        false_negative_rate=fn_rate,
        merchant_grouping_accuracy=merchant_acc,
        variable_detection_accuracy=variable_acc,
        simple_pattern_accuracy=simple_acc,
        avg_processing_time_ms=avg_time,
        total_cost_usd=total_cost,
    )


def print_results(result: BenchmarkResult, baseline: BenchmarkResult = None) -> None:
    """Print benchmark results in readable format.
    
    Args:
        result: Benchmark result to display
        baseline: Optional baseline for comparison
    """
    print(f"\n{'='*60}")
    print(f"  {result.version} Benchmark Results")
    print(f"{'='*60}")
    print(f"Total Transactions:     {result.total_transactions}")
    print(f"Correct Predictions:    {result.correct_predictions}")
    print(f"Overall Accuracy:       {result.accuracy:.1%}")
    print(f"False Positives:        {result.false_positives} ({result.false_positive_rate:.1%})")
    print(f"False Negatives:        {result.false_negatives} ({result.false_negative_rate:.1%})")
    print()
    print(f"Breakdown by Category:")
    print(f"  Merchant Grouping:    {result.merchant_grouping_accuracy:.1%}")
    print(f"  Variable Detection:   {result.variable_detection_accuracy:.1%}")
    print(f"  Simple Patterns:      {result.simple_pattern_accuracy:.1%}")
    print()
    print(f"Performance:")
    print(f"  Avg Processing Time:  {result.avg_processing_time_ms:.2f} ms")
    print(f"  Total Cost:           ${result.total_cost_usd:.4f}")
    
    if baseline:
        print(f"\nComparison vs {baseline.version}:")
        acc_delta = result.accuracy - baseline.accuracy
        fp_delta = result.false_positive_rate - baseline.false_positive_rate
        merchant_delta = result.merchant_grouping_accuracy - baseline.merchant_grouping_accuracy
        variable_delta = result.variable_detection_accuracy - baseline.variable_detection_accuracy
        
        print(f"  Accuracy:             {acc_delta:+.1%}")
        print(f"  False Positive Rate:  {fp_delta:+.1%}")
        print(f"  Merchant Grouping:    {merchant_delta:+.1%}")
        print(f"  Variable Detection:   {variable_delta:+.1%}")
    
    print(f"{'='*60}\n")


def main():
    """Run accuracy benchmarks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark recurring detection accuracy")
    parser.add_argument("--dataset", help="Path to custom labeled dataset JSON")
    parser.add_argument("--compare", action="store_true", help="Compare V1 vs V2")
    parser.add_argument("--v1-only", action="store_true", help="Test V1 only")
    parser.add_argument("--v2-only", action="store_true", help="Test V2 only")
    args = parser.parse_args()
    
    # Load dataset
    if args.dataset:
        with open(args.dataset) as f:
            data = json.load(f)
            dataset = [LabeledTransaction(**item) for item in data]
    else:
        dataset = load_default_dataset()
    
    print(f"\n📊 Recurring Detection Accuracy Benchmark")
    print(f"Dataset: {len(dataset)} labeled transactions\n")
    
    results = {}
    
    # Test V1 (pattern-only)
    if not args.v2_only:
        print("Testing V1 (pattern-only)...")
        v1_detector = easy_recurring_detection(enable_llm=False)
        v1_result = benchmark_version("V1", v1_detector, dataset)
        results["V1"] = v1_result
        print_results(v1_result)
    
    # Test V2 (with LLM)
    if not args.v1_only and os.getenv("GOOGLE_API_KEY"):
        print("Testing V2 (LLM-enhanced)...")
        v2_detector = easy_recurring_detection(
            enable_llm=True,
            llm_provider="google",
            llm_model="gemini-2.0-flash-exp",
        )
        v2_result = benchmark_version("V2", v2_detector, dataset)
        results["V2"] = v2_result
        
        baseline = results.get("V1")
        print_results(v2_result, baseline=baseline)
    elif not args.v1_only:
        print("\n⚠️  Skipping V2 test (GOOGLE_API_KEY not set)")
    
    # Verify targets
    if "V1" in results and "V2" in results:
        v1 = results["V1"]
        v2 = results["V2"]
        
        print(f"{'='*60}")
        print(f"  Target Verification")
        print(f"{'='*60}")
        
        # V1 targets: 85% accuracy, 8% FP
        v1_acc_pass = v1.accuracy >= 0.85
        v1_fp_pass = v1.false_positive_rate <= 0.08
        print(f"V1 Targets:")
        print(f"  Accuracy ≥85%:        {v1.accuracy:.1%} {'✓' if v1_acc_pass else '✗'}")
        print(f"  False Positives ≤8%:  {v1.false_positive_rate:.1%} {'✓' if v1_fp_pass else '✗'}")
        
        # V2 targets: 92% accuracy, <5% FP
        v2_acc_pass = v2.accuracy >= 0.92
        v2_fp_pass = v2.false_positive_rate < 0.05
        v2_variable_pass = v2.variable_detection_accuracy >= 0.88
        v2_merchant_pass = v2.merchant_grouping_accuracy >= 0.95
        print(f"\nV2 Targets:")
        print(f"  Accuracy ≥92%:        {v2.accuracy:.1%} {'✓' if v2_acc_pass else '✗'}")
        print(f"  False Positives <5%:  {v2.false_positive_rate:.1%} {'✓' if v2_fp_pass else '✗'}")
        print(f"  Variable Detection ≥88%: {v2.variable_detection_accuracy:.1%} {'✓' if v2_variable_pass else '✗'}")
        print(f"  Merchant Grouping ≥95%:  {v2.merchant_grouping_accuracy:.1%} {'✓' if v2_merchant_pass else '✗'}")
        
        print(f"{'='*60}\n")
        
        # Exit code based on targets
        all_pass = v1_acc_pass and v1_fp_pass and v2_acc_pass and v2_fp_pass and v2_variable_pass and v2_merchant_pass
        sys.exit(0 if all_pass else 1)
    

if __name__ == "__main__":
    main()
