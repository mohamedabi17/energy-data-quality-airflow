"""
Metrics Comparison Script
Compare data quality metrics across pipeline stages (raw vs cleaned).
"""

import pandas as pd
import os
from pathlib import Path


def load_metrics(file_path):
    """Load metrics from CSV file."""
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path, sep=';')
    return df.iloc[0] if len(df) > 0 else None


def compare_metrics(raw_file, cleaned_file):
    """Compare metrics between raw and cleaned data."""
    
    # Load both metric files
    raw_metrics = load_metrics(raw_file)
    cleaned_metrics = load_metrics(cleaned_file)
    
    if raw_metrics is None:
        print(f"❌ Could not load raw metrics from: {raw_file}")
        return
    
    if cleaned_metrics is None:
        print(f"❌ Could not load cleaned metrics from: {cleaned_file}")
        return
    
    print("\n" + "="*80)
    print("DATA QUALITY IMPROVEMENT COMPARISON")
    print("="*80)
    print(f"\nRAW Stage: {raw_metrics['pipeline_stage']} ({raw_metrics['timestamp']})")
    print(f"CLEANED Stage: {cleaned_metrics['pipeline_stage']} ({cleaned_metrics['timestamp']})")
    print("\n" + "-"*80)
    
    # Key metrics to compare
    comparison_metrics = [
        # Paris Consumption
        ('pct_CP_invalid_cons_paris', 'Invalid Postal Codes - Paris Consumption', '%'),
        ('pct_NB_KW_Jour_invalid_cons_paris', 'Invalid Consumption Values - Paris', '%'),
        ('pct_invalid_kw_cons_paris_unit', 'Unit Errors (>1000) - Paris', '%'),
        ('invalid_rate_cons_paris', 'Overall Invalid Rate - Paris', '%'),
        
        # Evry Consumption
        ('pct_CP_invalid_cons_evry', 'Invalid Postal Codes - Evry Consumption', '%'),
        
        # Population Paris
        ('pct_address_invalid_pop_paris', 'Invalid Addresses - Population Paris', '%'),
        ('pct_CSP_invalid_pop_paris', 'Invalid CSP - Population Paris', '%'),
        
        # Population Evry
        ('pct_address_invalid_pop_evry', 'Invalid Addresses - Population Evry', '%'),
        ('pct_CSP_invalid_pop_evry', 'Invalid CSP - Population Evry', '%'),
        
        # CSP Table
        ('completeness_salaire_csp', 'Salary Completeness - CSP', '%'),
        ('completeness_csp', 'Overall Completeness - CSP', '%'),
    ]
    
    print("\n{:<50} {:>12} {:>12} {:>12}".format("Metric", "RAW", "CLEANED", "IMPROVEMENT"))
    print("-"*80)
    
    improvements = []
    
    for metric_key, metric_name, unit in comparison_metrics:
        if metric_key in raw_metrics and metric_key in cleaned_metrics:
            raw_val = float(raw_metrics[metric_key])
            cleaned_val = float(cleaned_metrics[metric_key])
            
            # Calculate improvement (for error metrics, lower is better)
            if 'invalid' in metric_key.lower() or 'error' in metric_key.lower():
                improvement = raw_val - cleaned_val  # Reduction in errors is positive
                symbol = "✅" if improvement > 0 else ("⚠️" if improvement < 0 else "➖")
            else:  # For completeness metrics, higher is better
                improvement = cleaned_val - raw_val
                symbol = "✅" if improvement > 0 else ("⚠️" if improvement < 0 else "➖")
            
            improvements.append({
                'metric': metric_name,
                'improvement': improvement,
                'symbol': symbol
            })
            
            print(f"{metric_name:<50} {raw_val:>11.2f}{unit} {cleaned_val:>11.2f}{unit} {symbol} {improvement:>+9.2f}{unit}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    significant_improvements = [m for m in improvements if abs(m['improvement']) > 1]
    if significant_improvements:
        print(f"\n✅ {len(significant_improvements)} metrics showed significant improvement (>1%):")
        for m in sorted(significant_improvements, key=lambda x: abs(x['improvement']), reverse=True):
            print(f"   • {m['metric']}: {m['improvement']:+.2f}%")
    
    no_change = [m for m in improvements if abs(m['improvement']) < 0.01]
    if no_change:
        print(f"\n➖ {len(no_change)} metrics unchanged")
    
    degraded = [m for m in improvements if m['improvement'] < -0.01]
    if degraded:
        print(f"\n⚠️ {len(degraded)} metrics degraded (may need investigation):")
        for m in degraded:
            print(f"   • {m['metric']}: {m['improvement']:.2f}%")


def main():
    """Main comparison function."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent
    metadata_dir = os.path.join(base_path, 'metadata')
    
    # Use latest files
    raw_file = os.path.join(metadata_dir, 'metadata_qd_raw_latest.csv')
    cleaned_file = os.path.join(metadata_dir, 'metadata_qd_cleaned_latest.csv')
    
    compare_metrics(raw_file, cleaned_file)
    
    print("\n" + "="*80)
    print("Comparison complete!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
