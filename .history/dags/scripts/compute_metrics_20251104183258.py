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


def is_valid_address_format_paris(address):
    """
    Check if address respects Paris format.
    Expected format: "Paris, Numéro rue ...", e.g., "Paris, 20 rue Arthur Groussier"
    Regex: Paris,\s+\d+\s+rue\s+.+
    """
    if pd.isna(address) or address == '':
        return False
    
    pattern = r'Paris,\s+\d+\s+rue\s+.+'
    return bool(re.match(pattern, str(address)))


def is_valid_address_format_evry(address):
    """
    Check if address respects Evry format.
    Expected format: "Evry, Numéro rue ...", e.g., "Evry-Courcouronnes, 19 rue..."
    Regex: Evry,\s+\d+\s+rue\s+.+
    """
    if pd.isna(address) or address == '':
        return False
    
    # Also accept "Evry-Courcouronnes" as it's the actual city name
    pattern = r'Evry(-Courcouronnes)?,\s+\d+\s+(rue|boulevard|allée|square|place)\s+.+'
    return bool(re.match(pattern, str(address), re.IGNORECASE))


def is_valid_consumption(value):
    """Check if consumption value is a valid positive number."""
    if pd.isna(value):
        return False
    try:
        val = float(value)
        return val >= 0
    except (ValueError, TypeError):
        return False


def is_valid_csp(csp_value, valid_csp_list):
    """Check if CSP value belongs to predefined list."""
    if pd.isna(csp_value):
        return False
    
    csp_str = str(csp_value).strip().lower()
    valid_list_lower = [str(v).strip().lower() for v in valid_csp_list]
    
    return csp_str in valid_list_lower


def is_valid_salary(salary):
    """Check if salary is numeric and within realistic range [0, 1000000]."""
    if pd.isna(salary):
        return False
    try:
        val = float(salary)
        return 0 <= val <= 1000000
    except (ValueError, TypeError):
        return False


def calculate_tuple_completeness(row):
    """Calculate completeness of a tuple (row): % of non-null values."""
    total_fields = len(row)
    non_null_fields = row.notna().sum()
    return (non_null_fields / total_fields * 100) if total_fields > 0 else 0


def calculate_relation_completeness(df):
    """Calculate completeness of entire relation (table)."""
    total_cells = df.shape[0] * df.shape[1]
    non_null_cells = df.notna().sum().sum()
    return (non_null_cells / total_cells * 100) if total_cells > 0 else 0


def compute_evry_metrics(base_path):
    """Compute data quality metrics for Evry consumption data."""
    evry_file = os.path.join(base_path, 'Consommation_Evry.csv')
    
    if not os.path.exists(evry_file):
        raise FileNotFoundError(f"File not found: {evry_file}")
    
    df = pd.read_csv(evry_file)
    total_rows = len(df)
    
    # Validate postal codes (conformité)
    df['valid_cp'] = df['Code_Postal'].apply(is_valid_postal_code)
    valid_cp = df['valid_cp'].sum()
    pct_valid_cp = (valid_cp / total_rows * 100) if total_rows > 0 else 0
    pct_invalid_cp = 100 - pct_valid_cp
    
    # Validate addresses (N and Nom_Rue combined)
    df['valid_address'] = df.apply(
        lambda row: is_valid_address(row['N']) and is_valid_address(row['Nom_Rue']), 
        axis=1
    )
    valid_address = df['valid_address'].sum()
    pct_valid_address = (valid_address / total_rows * 100) if total_rows > 0 else 0
    
    # Validate consumption (NB_KW_Jour) - conformité
    df['valid_conso'] = df['NB_KW_Jour'].apply(is_valid_consumption)
    valid_conso = df['valid_conso'].sum()
    pct_valid_conso = (valid_conso / total_rows * 100) if total_rows > 0 else 0
    pct_invalid_conso = 100 - pct_valid_conso
    
    # Completeness metrics
    relation_completeness = calculate_relation_completeness(df)
    
    # Tuple completeness distribution
    df['tuple_completeness'] = df.apply(calculate_tuple_completeness, axis=1)
    tuples_below_50 = (df['tuple_completeness'] < 50).sum()
    tuples_50_to_100 = ((df['tuple_completeness'] >= 50) & (df['tuple_completeness'] < 100)).sum()
    tuples_100 = (df['tuple_completeness'] == 100).sum()
    
    # Overall valid rows (all fields valid)
    df['all_valid'] = df['valid_cp'] & df['valid_address'] & df['valid_conso']
    valid_rows = df['all_valid'].sum()
    invalid_rate = ((total_rows - valid_rows) / total_rows * 100) if total_rows > 0 else 0
    
    return {
        'total_rows_Cons_Evry': total_rows,
        'valid_rows_Cons_Evry': valid_rows,
        'invalid_rate_Cons_Evry': round(invalid_rate, 2),
        'pct_invalid_CP_Cons_Evry': round(pct_invalid_cp, 2),
        'pct_valid_Adresse_Cons_Evry': round(pct_valid_address, 2),
        'pct_invalid_Conso_Evry': round(pct_invalid_conso, 2),
        'completeness_Cons_Evry': round(relation_completeness, 2),
        'tuples_below_50_Cons_Evry': tuples_below_50,
        'tuples_50_to_100_Cons_Evry': tuples_50_to_100,
        'tuples_100_Cons_Evry': tuples_100
    }


def compute_paris_metrics(base_path):
    """Compute data quality metrics for Paris consumption data."""
    paris_file = os.path.join(base_path, 'Consommation_Paris.csv')
    
    if not os.path.exists(paris_file):
        raise FileNotFoundError(f"File not found: {paris_file}")
    
    df = pd.read_csv(paris_file)
    total_rows = len(df)
    
    # Validate postal codes (conformité)
    df['valid_cp'] = df['Code_Postal'].apply(is_valid_postal_code)
    valid_cp = df['valid_cp'].sum()
    pct_valid_cp = (valid_cp / total_rows * 100) if total_rows > 0 else 0
    pct_invalid_cp = 100 - pct_valid_cp
    
    # Validate addresses
    df['valid_address'] = df.apply(
        lambda row: is_valid_address(row['N']) and is_valid_address(row['Nom_Rue']), 
        axis=1
    )
    valid_address = df['valid_address'].sum()
    pct_valid_address = (valid_address / total_rows * 100) if total_rows > 0 else 0
    
    # Validate consumption (conformité)
    df['valid_conso'] = df['NB_KW_Jour'].apply(is_valid_consumption)
    valid_conso = df['valid_conso'].sum()
    pct_valid_conso = (valid_conso / total_rows * 100) if total_rows > 0 else 0
    pct_invalid_conso = 100 - pct_valid_conso
    
    # Completeness metrics
    relation_completeness = calculate_relation_completeness(df)
    
    # Tuple completeness distribution
    df['tuple_completeness'] = df.apply(calculate_tuple_completeness, axis=1)
    tuples_below_50 = (df['tuple_completeness'] < 50).sum()
    tuples_50_to_100 = ((df['tuple_completeness'] >= 50) & (df['tuple_completeness'] < 100)).sum()
    tuples_100 = (df['tuple_completeness'] == 100).sum()
    
    # Overall valid rows
    df['all_valid'] = df['valid_cp'] & df['valid_address'] & df['valid_conso']
    valid_rows = df['all_valid'].sum()
    invalid_rate = ((total_rows - valid_rows) / total_rows * 100) if total_rows > 0 else 0
    
    return {
        'total_rows_Cons_Paris': total_rows,
        'valid_rows_Cons_Paris': valid_rows,
        'invalid_rate_Cons_Paris': round(invalid_rate, 2),
        'pct_invalid_CP_Cons_Paris': round(pct_invalid_cp, 2),
        'pct_valid_Adresse_Cons_Paris': round(pct_valid_address, 2),
        'pct_invalid_Conso_Paris': round(pct_invalid_conso, 2),
        'completeness_Cons_Paris': round(relation_completeness, 2),
        'tuples_below_50_Cons_Paris': tuples_below_50,
        'tuples_50_to_100_Cons_Paris': tuples_50_to_100,
        'tuples_100_Cons_Paris': tuples_100
    }


def compute_population_paris_metrics(base_path, csp_reference):
    """Compute data quality metrics for Paris population data."""
    paris_file = os.path.join(base_path, 'Population_Paris.csv')
    
    if not os.path.exists(paris_file):
        raise FileNotFoundError(f"File not found: {paris_file}")
    
    df = pd.read_csv(paris_file)
    total_rows = len(df)
    
    # Validate address format (Ville, Numéro, NomRue)
    df['valid_address_format'] = df['Adresse'].apply(is_valid_address_format)
    valid_address = df['valid_address_format'].sum()
    pct_invalid_address = ((total_rows - valid_address) / total_rows * 100) if total_rows > 0 else 0
    
    # Validate CSP
    df['valid_csp'] = df['CSP'].apply(lambda x: is_valid_csp(x, csp_reference))
    valid_csp = df['valid_csp'].sum()
    pct_invalid_csp = ((total_rows - valid_csp) / total_rows * 100) if total_rows > 0 else 0
    
    # Completeness metrics
    relation_completeness = calculate_relation_completeness(df)
    
    # Tuple completeness distribution
    df['tuple_completeness'] = df.apply(calculate_tuple_completeness, axis=1)
    tuples_below_50 = (df['tuple_completeness'] < 50).sum()
    tuples_50_to_100 = ((df['tuple_completeness'] >= 50) & (df['tuple_completeness'] < 100)).sum()
    tuples_100 = (df['tuple_completeness'] == 100).sum()
    
    return {
        'total_rows_Pop_Paris': total_rows,
        'pct_invalid_address_Pop_Paris': round(pct_invalid_address, 2),
        'pct_invalid_CSP_Pop_Paris': round(pct_invalid_csp, 2),
        'completeness_Pop_Paris': round(relation_completeness, 2),
        'tuples_below_50_Pop_Paris': tuples_below_50,
        'tuples_50_to_100_Pop_Paris': tuples_50_to_100,
        'tuples_100_Pop_Paris': tuples_100
    }


def compute_population_evry_metrics(base_path, csp_reference):
    """Compute data quality metrics for Evry population data."""
    evry_file = os.path.join(base_path, 'Population_Evry.csv')
    
    if not os.path.exists(evry_file):
        raise FileNotFoundError(f"File not found: {evry_file}")
    
    df = pd.read_csv(evry_file)
    total_rows = len(df)
    
    # Validate address format (Ville, Numéro, NomRue)
    df['valid_address_format'] = df['Adresse'].apply(is_valid_address_format)
    valid_address = df['valid_address_format'].sum()
    pct_invalid_address = ((total_rows - valid_address) / total_rows * 100) if total_rows > 0 else 0
    
    # Validate CSP
    df['valid_csp'] = df['CSP'].apply(lambda x: is_valid_csp(x, csp_reference))
    valid_csp = df['valid_csp'].sum()
    pct_invalid_csp = ((total_rows - valid_csp) / total_rows * 100) if total_rows > 0 else 0
    
    # Completeness metrics
    relation_completeness = calculate_relation_completeness(df)
    
    # Tuple completeness distribution
    df['tuple_completeness'] = df.apply(calculate_tuple_completeness, axis=1)
    tuples_below_50 = (df['tuple_completeness'] < 50).sum()
    tuples_50_to_100 = ((df['tuple_completeness'] >= 50) & (df['tuple_completeness'] < 100)).sum()
    tuples_100 = (df['tuple_completeness'] == 100).sum()
    
    return {
        'total_rows_Pop_Evry': total_rows,
        'pct_invalid_address_Pop_Evry': round(pct_invalid_address, 2),
        'pct_invalid_CSP_Pop_Evry': round(pct_invalid_csp, 2),
        'completeness_Pop_Evry': round(relation_completeness, 2),
        'tuples_below_50_Pop_Evry': tuples_below_50,
        'tuples_50_to_100_Pop_Evry': tuples_50_to_100,
        'tuples_100_Pop_Evry': tuples_100
    }


def compute_csp_metrics(base_path):
    """Compute data quality metrics for CSP reference table."""
    csp_file = os.path.join(base_path, 'CSP.csv')
    
    if not os.path.exists(csp_file):
        raise FileNotFoundError(f"File not found: {csp_file}")
    
    df = pd.read_csv(csp_file)
    total_rows = len(df)
    
    # Handle column name (might be Salair_Moyen or Salaire_Moyen)
    salary_col = 'Salair_Moyen' if 'Salair_Moyen' in df.columns else 'Salaire_Moyen'
    
    # Handle missing Salaire_Moyen: impute with average of Min and Max
    df['Salaire_Moyen_original'] = df[salary_col].copy()
    df['Salaire_Moyen'] = df.apply(
        lambda row: (float(str(row['Salaire_Min']).replace(' ', '')) + float(str(row['Salaire_Max']).replace(' ', ''))) / 2 
        if pd.isna(row[salary_col]) and pd.notna(row['Salaire_Min']) and pd.notna(row['Salaire_Max'])
        else row[salary_col], 
        axis=1
    )
    
    # Validate Salaire_Moyen (must be numeric and in range [0, 1000000])
    df['valid_salary'] = df['Salaire_Moyen'].apply(is_valid_salary)
    valid_salary = df['valid_salary'].sum()
    pct_invalid_salary = ((total_rows - valid_salary) / total_rows * 100) if total_rows > 0 else 0
    
    # Calculate completeness of Salaire_Moyen attribute before imputation
    non_null_salaries = df['Salaire_Moyen_original'].notna().sum()
    completeness_salaire = (non_null_salaries / total_rows * 100) if total_rows > 0 else 0
    
    # Overall completeness (use original data)
    cols_to_check = ['ID_CSP', 'Desc', salary_col, 'Salaire_Min', 'Salaire_Max']
    relation_completeness = calculate_relation_completeness(df[cols_to_check])
    
    return {
        'total_rows_CSP': total_rows,
        'pct_invalid_salary_CSP': round(pct_invalid_salary, 2),
        'completeness_salaire_CSP': round(completeness_salaire, 2),
        'completeness_CSP': round(relation_completeness, 2)
    }


def get_csp_reference_list(base_path):
    """Load valid CSP values from CSP table."""
    csp_file = os.path.join(base_path, 'CSP.csv')
    
    if not os.path.exists(csp_file):
        # Return default list if file not found
        return ['Agriculteurs', 'Artisans', 'Commerçants', 'Cadres', 
                'Professions intermédiaires', 'Employés', 'Ouvriers', 
                'Retraités', 'Etudiants', 'Cadre', 'Employé', 'Ouvrier',
                'Commerçant', 'Artisan', 'Retraitée', 'Etudiant', 'Agriculteur',
                'cadres et professions intellectuelles supérieures',
                'Agriculteurs exploitants', 'algricultrices exploitantes']
    
    df = pd.read_csv(csp_file)
    # Extract CSP categories from description
    csp_list = df['Desc'].dropna().tolist()
    
    # Add common variations
    csp_list.extend(['1', '2', '3', '4', '5', '6', 
                     'Cadre', 'Employé', 'Ouvrier', 'Commerçant', 
                     'Artisan', 'Retraitée', 'Etudiant', 'Agriculteur',
                     'cadres et professions intellectuelles supérieures',
                     'Professions intermédiaires'])
    
    return csp_list


def write_metadata_file(metrics, output_path):
    """Write metrics to semicolon-separated metadata file."""
    # Define the order of columns - comprehensive list of all metrics
    columns = [
        # Consommation Evry
        'total_rows_Cons_Evry',
        'valid_rows_Cons_Evry',
        'invalid_rate_Cons_Evry',
        'pct_invalid_CP_Cons_Evry',
        'pct_valid_Adresse_Cons_Evry',
        'pct_invalid_Conso_Evry',
        'completeness_Cons_Evry',
        'tuples_below_50_Cons_Evry',
        'tuples_50_to_100_Cons_Evry',
        'tuples_100_Cons_Evry',
        
        # Consommation Paris
        'total_rows_Cons_Paris',
        'valid_rows_Cons_Paris',
        'invalid_rate_Cons_Paris',
        'pct_invalid_CP_Cons_Paris',
        'pct_valid_Adresse_Cons_Paris',
        'pct_invalid_Conso_Paris',
        'completeness_Cons_Paris',
        'tuples_below_50_Cons_Paris',
        'tuples_50_to_100_Cons_Paris',
        'tuples_100_Cons_Paris',
        
        # Population Paris
        'total_rows_Pop_Paris',
        'pct_invalid_address_Pop_Paris',
        'pct_invalid_CSP_Pop_Paris',
        'completeness_Pop_Paris',
        'tuples_below_50_Pop_Paris',
        'tuples_50_to_100_Pop_Paris',
        'tuples_100_Pop_Paris',
        
        # Population Evry
        'total_rows_Pop_Evry',
        'pct_invalid_address_Pop_Evry',
        'pct_invalid_CSP_Pop_Evry',
        'completeness_Pop_Evry',
        'tuples_below_50_Pop_Evry',
        'tuples_50_to_100_Pop_Evry',
        'tuples_100_Pop_Evry',
        
        # CSP
        'total_rows_CSP',
        'pct_invalid_salary_CSP',
        'completeness_salaire_CSP',
        'completeness_CSP'
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
    print(f"Total metrics computed: {len(metrics)}")


def main():
    """Main function to compute all metrics and write metadata."""
    # Get the base directory (parent of dags folder)
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent
    
    print(f"Base path: {base_path}")
    print("\n" + "="*60)
    print("DATA QUALITY METRICS COMPUTATION")
    print("="*60)
    
    # Get CSP reference list
    print("\n1. Loading CSP reference data...")
    csp_reference = get_csp_reference_list(base_path)
    print(f"   Loaded {len(csp_reference)} CSP categories")
    
    # Compute metrics for all tables
    print("\n2. Computing Consommation Evry metrics...")
    evry_cons_metrics = compute_evry_metrics(base_path)
    print(f"   ✓ Computed {len(evry_cons_metrics)} metrics")
    
    print("\n3. Computing Consommation Paris metrics...")
    paris_cons_metrics = compute_paris_metrics(base_path)
    print(f"   ✓ Computed {len(paris_cons_metrics)} metrics")
    
    print("\n4. Computing Population Paris metrics...")
    paris_pop_metrics = compute_population_paris_metrics(base_path, csp_reference)
    print(f"   ✓ Computed {len(paris_pop_metrics)} metrics")
    
    print("\n5. Computing Population Evry metrics...")
    evry_pop_metrics = compute_population_evry_metrics(base_path, csp_reference)
    print(f"   ✓ Computed {len(evry_pop_metrics)} metrics")
    
    print("\n6. Computing CSP table metrics...")
    csp_metrics = compute_csp_metrics(base_path)
    print(f"   ✓ Computed {len(csp_metrics)} metrics")
    
    # Combine all metrics
    all_metrics = {
        **evry_cons_metrics, 
        **paris_cons_metrics,
        **paris_pop_metrics,
        **evry_pop_metrics,
        **csp_metrics
    }
    
    # Write to metadata file
    print("\n7. Writing metadata file...")
    metadata_path = os.path.join(base_path, 'metadata', 'metadata_qd.csv')
    write_metadata_file(all_metrics, metadata_path)
    
    print("\n" + "="*60)
    print("DATA QUALITY METRICS SUMMARY")
    print("="*60)
    
    print("\n--- CONSOMMATION EVRY ---")
    for key, value in evry_cons_metrics.items():
        print(f"  {key}: {value}")
    
    print("\n--- CONSOMMATION PARIS ---")
    for key, value in paris_cons_metrics.items():
        print(f"  {key}: {value}")
    
    print("\n--- POPULATION PARIS ---")
    for key, value in paris_pop_metrics.items():
        print(f"  {key}: {value}")
    
    print("\n--- POPULATION EVRY ---")
    for key, value in evry_pop_metrics.items():
        print(f"  {key}: {value}")
    
    print("\n--- CSP TABLE ---")
    for key, value in csp_metrics.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print(f"✓ COMPLETED: {len(all_metrics)} total metrics computed")
    print("="*60)


if __name__ == '__main__':
    main()
