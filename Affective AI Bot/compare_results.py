#!/usr/bin/env python3
"""
Compare two benchmark results to see improvements.
"""

import json
import sys
from pathlib import Path


def load_results(filepath):
    """Load benchmark results from JSON."""
    with open(filepath, 'r') as f:
        return json.load(f)


def compare_results(baseline_file, improved_file):
    """Compare two result files and show improvements."""
    
    print("\n" + "="*70)
    print("📊 PERFORMANCE COMPARISON")
    print("="*70 + "\n")
    
    # Load results
    baseline = load_results(baseline_file)
    improved = load_results(improved_file)
    
    b_metrics = baseline['metrics']
    i_metrics = improved['metrics']
    
    # Overall metrics
    print("📈 Overall Performance:")
    print(f"   Baseline file: {baseline_file}")
    print(f"   Improved file: {improved_file}")
    print()
    
    # Accuracy
    if 'accuracy' in b_metrics and 'accuracy' in i_metrics:
        b_acc = b_metrics['accuracy'] * 100
        i_acc = i_metrics['accuracy'] * 100
        diff = i_acc - b_acc
        arrow = "⬆️" if diff > 0 else "⬇️" if diff < 0 else "➡️"
        
        print(f"   Accuracy:")
        print(f"      Baseline: {b_acc:.1f}%")
        print(f"      Improved: {i_acc:.1f}%")
        print(f"      Change:   {arrow} {diff:+.1f}%")
        print()
    
    # Latency
    b_lat = b_metrics.get('avg_latency', 0)
    i_lat = i_metrics.get('avg_latency', 0)
    lat_diff = i_lat - b_lat
    lat_arrow = "⬇️" if lat_diff < 0 else "⬆️" if lat_diff > 0 else "➡️"
    
    print(f"   Avg Latency:")
    print(f"      Baseline: {b_lat:.3f}s")
    print(f"      Improved: {i_lat:.3f}s")
    print(f"      Change:   {lat_arrow} {lat_diff:+.3f}s")
    print()
    
    # Confidence
    b_conf = b_metrics.get('avg_confidence', 0) * 100
    i_conf = i_metrics.get('avg_confidence', 0) * 100
    conf_diff = i_conf - b_conf
    conf_arrow = "⬆️" if conf_diff > 0 else "⬇️" if conf_diff < 0 else "➡️"
    
    print(f"   Avg Confidence:")
    print(f"      Baseline: {b_conf:.1f}%")
    print(f"      Improved: {i_conf:.1f}%")
    print(f"      Change:   {conf_arrow} {conf_diff:+.1f}%")
    print()
    
    # Per-emotion comparison
    if 'per_emotion' in b_metrics and 'per_emotion' in i_metrics:
        print("📊 Per-Emotion F1 Scores:")
        print(f"\n   {'Emotion':<12} {'Baseline':>10} {'Improved':>10} {'Change':>10}")
        print(f"   {'-'*12} {'-'*10} {'-'*10} {'-'*10}")
        
        all_emotions = set(b_metrics['per_emotion'].keys()) | set(i_metrics['per_emotion'].keys())
        
        for emotion in sorted(all_emotions):
            b_f1 = b_metrics['per_emotion'].get(emotion, {}).get('f1', 0)
            i_f1 = i_metrics['per_emotion'].get(emotion, {}).get('f1', 0)
            diff = i_f1 - b_f1
            
            arrow = "⬆️" if diff > 0 else "⬇️" if diff < 0 else "➡️"
            
            print(f"   {emotion:<12} {b_f1:>9.1%} {i_f1:>9.1%} {arrow} {diff:>+7.1%}")
    
    print("\n" + "="*70)
    
    # Summary
    if 'accuracy' in b_metrics and 'accuracy' in i_metrics:
        diff = (i_metrics['accuracy'] - b_metrics['accuracy']) * 100
        
        if diff > 5:
            print("\n🎉 Significant improvement! (+{:.1f}%)".format(diff))
        elif diff > 2:
            print("\n✅ Good improvement! (+{:.1f}%)".format(diff))
        elif diff > 0:
            print("\n📈 Small improvement (+{:.1f}%)".format(diff))
        elif diff == 0:
            print("\n➡️  No change in accuracy")
        else:
            print("\n⚠️  Performance decreased ({:.1f}%)".format(diff))
    
    print()


def main():
    if len(sys.argv) != 3:
        print("Usage: python compare_results.py <baseline.json> <improved.json>")
        print("\nExample:")
        print("  python compare_results.py v1_baseline.json v2_improved.json")
        sys.exit(1)
    
    baseline_file = sys.argv[1]
    improved_file = sys.argv[2]
    
    # Check files exist
    if not Path(baseline_file).exists():
        print(f"❌ Baseline file not found: {baseline_file}")
        sys.exit(1)
    
    if not Path(improved_file).exists():
        print(f"❌ Improved file not found: {improved_file}")
        sys.exit(1)
    
    # Compare
    compare_results(baseline_file, improved_file)


if __name__ == '__main__':
    main()

