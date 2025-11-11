"""
Data Quality Metrics Calculator
Validates CSV data and computes quality metrics for the metadata file.
"""

import os
import pandas as pd
import re
from pathlib import Path


def is_valid_postal_code(code):
    """Check if postal code is valid (5 digits)."""
    if pd.isna(code):
        return False
    code_str = str(code).strip()
    return bool(re.match(r'^\d{5}$', code_str))


def is_valid_address(address):
    """Check if address is non-empty and properly formatted."""
    if pd.isna(address) or address == '':
        return False
    return True


def is_valid_consumption(value):
    """Check if consumption value is a valid positive number."""
    if pd.isna(value):
        return False
    try:
        val = float(value)
        return val >= 0
    except (ValueError, TypeError):
        return False


def compute_evry_metrics(base_path):
    """Compute data quality metrics for Evry consumption data."""
    evry_file = os.path.join(base_path, 'Consommation_Evry.csv')
    
    if not os.path.exists(evry_file):
        raise FileNotFoundError(f"File not found: {evry_file}")
    
    df = pd.read_csv(evry_file)
    total_rows = len(df)
    
    # Validate postal codes
    df['valid_cp'] = df['Code_Postal'].apply(is_valid_postal_code)
    valid_cp = df['valid_cp'].sum()
    pct_valid_cp = (valid_cp / total_rows * 100) if total_rows > 0 else 0
    
    # Validate addresses (N and Nom_Rue combined)
    df['valid_address'] = df.apply(
        lambda row: is_valid_address(row['N']) and is_valid_address(row['Nom_Rue']), 
        axis=1
    )
    valid_address = df['valid_address'].sum()
    pct_valid_address = (valid_address / total_rows * 100) if total_rows > 0 else 0
    
    # Validate consumption (NB_KW_Jour)
    df['valid_conso'] = df['NB_KW_Jour'].apply(is_valid_consumption)
    valid_conso = df['valid_conso'].sum()
    pct_valid_conso = (valid_conso / total_rows * 100) if total_rows > 0 else 0
    
    # Overall valid rows (all fields valid)
    df['all_valid'] = df['valid_cp'] & df['valid_address'] & df['valid_conso']
    valid_rows = df['all_valid'].sum()
    invalid_rate = ((total_rows - valid_rows) / total_rows * 100) if total_rows > 0 else 0
    
    return {
        'total_rows_KW_Conso_Evry': total_rows,
        'valid_rows_KW_Conso_Evry': valid_rows,
        'invalid_rate_KW_Conso_Evry': round(invalid_rate, 2),
        'pct_valid_CP_Cons_Evry': round(pct_valid_cp, 2),
        'pct_valid_Adresse_Cons_Evry': round(pct_valid_address, 2),
        'pct_valid_Conso_Evry': round(pct_valid_conso, 2)
    }


def compute_paris_metrics(base_path):
    """Compute data quality metrics for Paris consumption data."""
    paris_file = os.path.join(base_path, 'Consommation_Paris.csv')
    
    if not os.path.exists(paris_file):
        raise FileNotFoundError(f"File not found: {paris_file}")
    
    df = pd.read_csv(paris_file)
    total_rows = len(df)
    
    # Validate postal codes
    df['valid_cp'] = df['Code_Postal'].apply(is_valid_postal_code)
    
    # Validate addresses
    df['valid_address'] = df.apply(
        lambda row: is_valid_address(row['N']) and is_valid_address(row['Nom_Rue']), 
        axis=1
    )
    
    # Validate consumption
    df['valid_conso'] = df['NB_KW_Jour'].apply(is_valid_consumption)
    
    # Overall valid rows
    df['all_valid'] = df['valid_cp'] & df['valid_address'] & df['valid_conso']
    valid_rows = df['all_valid'].sum()
    invalid_rate = ((total_rows - valid_rows) / total_rows * 100) if total_rows > 0 else 0
    
    return {
        'total_rows_KW_Conso_Paris': total_rows,
        'valid_rows_KW_Conso_Paris': valid_rows,
        'invalid_rate_KW_Conso_Paris': round(invalid_rate, 2)
    }


def write_metadata_file(metrics, output_path):
    """Write metrics to semicolon-separated metadata file."""
    # Define the order of columns as requested
    columns = [
        'total_rows_KW_Conso_Evry',
        'valid_rows_KW_Conso_Evry',
        'invalid_rate_KW_Conso_Evry',
        'total_rows_KW_Conso_Paris',
        'valid_rows_KW_Conso_Paris',
        'invalid_rate_KW_Conso_Paris',
        'pct_valid_CP_Cons_Evry',
        'pct_valid_Adresse_Cons_Evry',
        'pct_valid_Conso_Evry'
    ]
    
    # Create header
    header = ';'.join(columns)
    
    # Create values row
    values = ';'.join([str(metrics.get(col, '')) for col in columns])
    
    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header + '\n')
        f.write(values + '\n')
    
    print(f"Metadata file written to: {output_path}")
    print(f"Metrics: {metrics}")


def main():
    """Main function to compute all metrics and write metadata."""
    # Get the base directory (parent of dags folder)
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent
    
    print(f"Base path: {base_path}")
    
    # Compute metrics
    print("Computing Evry metrics...")
    evry_metrics = compute_evry_metrics(base_path)
    
    print("Computing Paris metrics...")
    paris_metrics = compute_paris_metrics(base_path)
    
    # Combine all metrics
    all_metrics = {**evry_metrics, **paris_metrics}
    
    # Write to metadata file
    metadata_path = os.path.join(base_path, 'metadata', 'metadata_qd.csv')
    write_metadata_file(all_metrics, metadata_path)
    
    print("\n=== Data Quality Metrics Summary ===")
    for key, value in all_metrics.items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    main()
