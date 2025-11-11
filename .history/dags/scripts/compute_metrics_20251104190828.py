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
    Regex: Paris,\\s+\\d+\\s+rue\\s+.+
    """
    if pd.isna(address) or address == '':
        return False
    
    pattern = r'Paris,\s+\d+\s+rue\s+.+'
    return bool(re.match(pattern, str(address)))


def is_valid_address_format_evry(address):
    """
    Check if address respects Evry format.
    Expected format: "Evry, Numéro rue ...", e.g., "Evry-Courcouronnes, 19 rue..."
    Regex: Evry,\\s+\\d+\\s+rue\\s+.+
    """
    if pd.isna(address) or address == '':
        return False
    
    # Also accept "Evry-Courcouronnes" as it's the actual city name
    pattern = r'Evry(-Courcouronnes)?,\s+\d+\s+(rue|boulevard|allée|square|place)\s+.+'
    return bool(re.match(pattern, str(address), re.IGNORECASE))


def is_valid_consumption(value):
    """
    Check if consumption value is valid.
    Invalid if: NB_KW_Jour < 0 OR NB_KW_Jour > 1000 OR NB_KW_Jour = null
    """
    if pd.isna(value):
        return False
    try:
        val = float(value)
        return 0 <= val <= 1000
    except (ValueError, TypeError):
        return False


def is_valid_csp(csp_value):
    """
    Check if CSP value belongs to the exact predefined list.
    Uses case-insensitive comparison.
    """
    if pd.isna(csp_value) or csp_value == '':
        return False
    
    # Exact list of valid CSP values (52 values)
    valid_csp_list = [
        "Agriculteur",
        "Agriculteurs",
        "Agriculteurs exploitants",
        "Agriculteurs exploitants / algricultrices exploitantes",
        "Agricultrice",
        "Agricultrices",
        "Algricultrices exploitantes",
        "Artisan",
        "Artisan / Commerçant",
        "Artisane",
        "Artisanes",
        "Artisans",
        "Artisans / artisanes, commerçants / commerçantes et chefs / cheffes d'entreprise",
        "Autres personnes sans activité professionnelle",
        "Cadre",
        "Cadre supérieur",
        "Cadres",
        "Cadres et professions intellectuelles supérieures",
        "Cadres supérieurs",
        "Chef d'entreprise",
        "Cheffe d'entreprise",
        "Cheffes d'entreprise",
        "Chefs d'entreprise",
        "Commerçant",
        "Commerçant / Artisan",
        "Commerçante",
        "Commerçantes",
        "Commerçants",
        "Employe",
        "Employé",
        "Employée",
        "Employées",
        "Employés",
        "Employés / employées",
        "Etudiant",
        "Etudiante",
        "Ouvrier",
        "Ouvriers",
        "Ouvriers / ouvrières",
        "Ouvrière",
        "Ouvrières",
        "Profession intermédiaire",
        "Professions intellectuelles supérieures",
        "Professions intermediaires",
        "Professions intermédiaires",
        "Retraité",
        "Retraitée",
        "Retraitées",
        "Retraités",
        "Sans activité professionnelle",
        "cadres et professions intellectuelles supérieures",
        "Étudiante",
        "Étudiants"
    ]
    
    csp_str = str(csp_value).strip()
    
    # Case-insensitive comparison
    for valid_csp in valid_csp_list:
        if valid_csp.lower() == csp_str.lower():
            return True
    
    return False


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
    
    # Check for consumption > 1000 (unit validation)
    def is_kw_unit_valid(value):
        if pd.isna(value):
            return False
        try:
            val = float(value)
            return val <= 1000
        except (ValueError, TypeError):
            return False
    
    df['valid_kw_unit'] = df['NB_KW_Jour'].apply(is_kw_unit_valid)
    valid_kw_unit = df['valid_kw_unit'].sum()
    pct_invalid_kw_unit = ((total_rows - valid_kw_unit) / total_rows * 100) if total_rows > 0 else 0
    
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
        'total_rows_cons_evry': total_rows,
        'valid_rows_cons_evry': valid_rows,
        'invalid_rate_cons_evry': round(invalid_rate, 2),
        'pct_CP_invalid_cons_evry': round(pct_invalid_cp, 2),
        'pct_address_valid_cons_evry': round(pct_valid_address, 2),
        'pct_NB_KW_Jour_invalid_cons_evry': round(pct_invalid_conso, 2),
        'pct_invalid_kw_cons_evry_unit': round(pct_invalid_kw_unit, 2),
        'completeness_cons_evry': round(relation_completeness, 2),
        'tuples_below_50_cons_evry': tuples_below_50,
        'tuples_50_to_100_cons_evry': tuples_50_to_100,
        'tuples_100_cons_evry': tuples_100
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
        'total_rows_cons_paris': total_rows,
        'valid_rows_cons_paris': valid_rows,
        'invalid_rate_cons_paris': round(invalid_rate, 2),
        'pct_CP_invalid_cons_paris': round(pct_invalid_cp, 2),
        'pct_address_valid_cons_paris': round(pct_valid_address, 2),
        'pct_NB_KW_Jour_invalid_cons_paris': round(pct_invalid_conso, 2),
        'completeness_cons_paris': round(relation_completeness, 2),
        'tuples_below_50_cons_paris': tuples_below_50,
        'tuples_50_to_100_cons_paris': tuples_50_to_100,
        'tuples_100_cons_paris': tuples_100
    }


def compute_population_paris_metrics(base_path):
    """Compute data quality metrics for Paris population data."""
    paris_file = os.path.join(base_path, 'Population_Paris.csv')
    
    if not os.path.exists(paris_file):
        raise FileNotFoundError(f"File not found: {paris_file}")
    
    df = pd.read_csv(paris_file)
    total_rows = len(df)
    
    # Validate address format using Paris-specific regex: Paris,\s+\d+\s+rue\s+.+
    df['valid_address_format'] = df['Adresse'].apply(is_valid_address_format_paris)
    valid_address = df['valid_address_format'].sum()
    pct_invalid_address = ((total_rows - valid_address) / total_rows * 100) if total_rows > 0 else 0
    
    # Validate CSP using exact list
    df['valid_csp'] = df['CSP'].apply(is_valid_csp)
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
        'total_rows_pop_paris': total_rows,
        'pct_address_invalid_pop_paris': round(pct_invalid_address, 2),
        'pct_CSP_invalid_pop_paris': round(pct_invalid_csp, 2),
        'completeness_pop_paris': round(relation_completeness, 2),
        'tuples_below_50_pop_paris': tuples_below_50,
        'tuples_50_to_100_pop_paris': tuples_50_to_100,
        'tuples_100_pop_paris': tuples_100
    }


def compute_population_evry_metrics(base_path):
    """Compute data quality metrics for Evry population data."""
    evry_file = os.path.join(base_path, 'Population_Evry.csv')
    
    if not os.path.exists(evry_file):
        raise FileNotFoundError(f"File not found: {evry_file}")
    
    df = pd.read_csv(evry_file)
    total_rows = len(df)
    
    # Validate address format using Evry-specific regex: Evry,\s+\d+\s+rue\s+.+
    df['valid_address_format'] = df['Adresse'].apply(is_valid_address_format_evry)
    valid_address = df['valid_address_format'].sum()
    pct_invalid_address = ((total_rows - valid_address) / total_rows * 100) if total_rows > 0 else 0
    
    # Validate CSP using exact list
    df['valid_csp'] = df['CSP'].apply(is_valid_csp)
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
        'total_rows_pop_evry': total_rows,
        'pct_address_invalid_pop_evry': round(pct_invalid_address, 2),
        'pct_CSP_invalid_pop_evry': round(pct_invalid_csp, 2),
        'completeness_pop_evry': round(relation_completeness, 2),
        'tuples_below_50_pop_evry': tuples_below_50,
        'tuples_50_to_100_pop_evry': tuples_50_to_100,
        'tuples_100_pop_evry': tuples_100
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
        'total_rows_csp': total_rows,
        'pct_salary_invalid_csp': round(pct_invalid_salary, 2),
        'completeness_salaire_csp': round(completeness_salaire, 2),
        'completeness_csp': round(relation_completeness, 2)
    }


def write_metadata_file(metrics, output_path):
    """Write metrics to semicolon-separated metadata file."""
    # Define the order of columns - comprehensive list of all metrics
    columns = [
        # Consommation Evry
        'total_rows_cons_evry',
        'valid_rows_cons_evry',
        'invalid_rate_cons_evry',
        'pct_CP_invalid_cons_evry',
        'pct_address_valid_cons_evry',
        'pct_NB_KW_Jour_invalid_cons_evry',
        'completeness_cons_evry',
        'tuples_below_50_cons_evry',
        'tuples_50_to_100_cons_evry',
        'tuples_100_cons_evry',
        
        # Consommation Paris
        'total_rows_cons_paris',
        'valid_rows_cons_paris',
        'invalid_rate_cons_paris',
        'pct_CP_invalid_cons_paris',
        'pct_address_valid_cons_paris',
        'pct_NB_KW_Jour_invalid_cons_paris',
        'completeness_cons_paris',
        'tuples_below_50_cons_paris',
        'tuples_50_to_100_cons_paris',
        'tuples_100_cons_paris',
        
        # Population Paris
        'total_rows_pop_paris',
        'pct_address_invalid_pop_paris',
        'pct_CSP_invalid_pop_paris',
        'completeness_pop_paris',
        'tuples_below_50_pop_paris',
        'tuples_50_to_100_pop_paris',
        'tuples_100_pop_paris',
        
        # Population Evry
        'total_rows_pop_evry',
        'pct_address_invalid_pop_evry',
        'pct_CSP_invalid_pop_evry',
        'completeness_pop_evry',
        'tuples_below_50_pop_evry',
        'tuples_50_to_100_pop_evry',
        'tuples_100_pop_evry',
        
        # CSP
        'total_rows_csp',
        'pct_salary_invalid_csp',
        'completeness_salaire_csp',
        'completeness_csp'
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
    
    # Compute metrics for all tables
    print("\n1. Computing Consommation Evry metrics...")
    evry_cons_metrics = compute_evry_metrics(base_path)
    print(f"   ✓ Computed {len(evry_cons_metrics)} metrics")
    
    print("\n2. Computing Consommation Paris metrics...")
    paris_cons_metrics = compute_paris_metrics(base_path)
    print(f"   ✓ Computed {len(paris_cons_metrics)} metrics")
    
    print("\n3. Computing Population Paris metrics...")
    paris_pop_metrics = compute_population_paris_metrics(base_path)
    print(f"   ✓ Computed {len(paris_pop_metrics)} metrics")
    
    print("\n4. Computing Population Evry metrics...")
    evry_pop_metrics = compute_population_evry_metrics(base_path)
    print(f"   ✓ Computed {len(evry_pop_metrics)} metrics")
    
    print("\n5. Computing CSP table metrics...")
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
    print("\n6. Writing metadata file...")
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
