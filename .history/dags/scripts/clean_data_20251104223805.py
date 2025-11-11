"""
Data Cleaning and Quality Improvement Script
Cleans and standardizes data based on quality metrics.
"""

import os
import pandas as pd
import re
from pathlib import Path


def clean_postal_code(code):
    """Clean and standardize postal code to 5 digits."""
    if pd.isna(code):
        return None
    
    code_str = str(code).strip()
    # Remove spaces and non-digits
    code_str = re.sub(r'\D', '', code_str)
    
    # Take first 5 digits
    if len(code_str) >= 5:
        return code_str[:5]
    
    return None


def normalize_kw_to_kwh_per_day(value):
    """
    Normalize consumption values to kWh/day.
    Values > 1000 are assumed to be in Wh/day and converted to kWh/day.
    """
    if pd.isna(value):
        return None
    
    try:
        val = float(value)
        if val < 0:
            return None
        
        # If value > 1000, assume it's in Wh and convert to kWh
        if val > 1000:
            return round(val / 1000, 2)
        
        return round(val, 2)
    except (ValueError, TypeError):
        return None


def standardize_address_paris(address):
    """
    Standardize Paris address to format: "Paris, [number] rue [street]"
    """
    if pd.isna(address) or address == '':
        return None
    
    addr_str = str(address).strip()
    
    # Already in correct format
    if re.match(r'Paris,\s+\d+\s+rue\s+.+', addr_str):
        return addr_str
    
    # Try to fix common issues
    # Remove extra spaces after comma
    addr_str = re.sub(r'Paris,\s*', 'Paris, ', addr_str)
    
    return addr_str if re.match(r'Paris,\s+\d+\s+rue\s+.+', addr_str) else None


def standardize_address_evry(address):
    """
    Standardize Evry address to format: "Evry-Courcouronnes, [number] [street type] [street]"
    """
    if pd.isna(address) or address == '':
        return None
    
    addr_str = str(address).strip()
    
    # Remove postal code if present (e.g., ", 91000,")
    addr_str = re.sub(r',\s*\d{5}\s*,', ',', addr_str)
    
    # Ensure "Evry-Courcouronnes" format at start
    addr_str = re.sub(r'^Evry[^,]*', 'Evry-Courcouronnes', addr_str, flags=re.IGNORECASE)
    
    # Normalize spacing around comma
    addr_str = re.sub(r'\s*,\s*', ', ', addr_str)
    
    # Check if matches expected format (number + street type + street name)
    # Accept various street types with case-insensitive matching
    if re.search(r'\d+\s+(rue|boulevard|bd|allée|allee|square|place|avenue|av)\s+\w+', addr_str, re.IGNORECASE):
        return addr_str
    
    # If it has Evry-Courcouronnes and some content, keep it
    if 'Evry-Courcouronnes' in addr_str and len(addr_str) > 20:
        return addr_str
    
    return None


def standardize_csp_value(csp_value, return_id=False):
    """
    Comprehensive CSP standardization to match CSP.csv reference.
    Handles:
    - Numeric codes (1-6) from Population_Evry
    - Various text formats from Population_Paris (Cadre, Employé, Ouvrier, etc.)
    - Singular/plural variations
    - Case variations (lowercase, uppercase, mixed)
    - Non-standard values (Etudiant, Retraitée) -> mapped to closest category or None
    
    Args:
        csp_value: The CSP value to standardize
        return_id: If True, returns ID_CSP (1-6), otherwise returns full description text
    """
    if pd.isna(csp_value):
        return None
    
    # Standard CSP mapping to ID_CSP
    csp_mapping_numeric = {
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 4,
        '5': 5,
        '6': 6
    }
    
    # CSP descriptions for reference (used when return_id=False)
    csp_descriptions = {
        1: 'Agriculteurs exploitants / algricultrices exploitantes',
        2: 'Artisans / artisanes, commerçants / commerçantes et chefs / cheffes d\'entreprise',
        3: 'Cadres et professions intellectuelles supérieures',
        4: 'Professions intermédiaires',
        5: 'Employés / employées',
        6: 'Ouvriers / ouvrières'
    }
    
    # Try numeric conversion first (for Population_Evry: 1,2,3,4,5,6)
    value_str_raw = str(csp_value).strip()
    if value_str_raw in csp_mapping_numeric:
        id_csp = csp_mapping_numeric[value_str_raw]
        return id_csp if return_id else csp_descriptions[id_csp]
    
    # Text standardization (for Population_Paris variations)
    value_lower = value_str_raw.lower()
    
    # Category 1: Agriculteurs
    if any(word in value_lower for word in ['agricult', 'exploitant']):
        return 1 if return_id else csp_descriptions[1]
    
    # Category 2: Artisans/Commerçants (check before "cadre" to avoid confusion)
    if any(word in value_lower for word in ['artisan', 'commerçant', 'commercant', "chef d'entreprise", "chefs d'entreprise"]):
        return 2 if return_id else csp_descriptions[2]
    
    # Category 3: Cadres (must check full phrase first to distinguish from "Professions intermédiaires")
    if ('cadre' in value_lower and 'professions intellectuelles' in value_lower) or \
       ('cadres et professions intellectuelles' in value_lower):
        return 3 if return_id else csp_descriptions[3]
    
    # Check for "Cadre" alone (short form)
    if value_lower == 'cadre' or value_lower == 'cadres':
        return 3 if return_id else csp_descriptions[3]
    
    # Category 4: Professions intermédiaires (check after Cadres)
    if 'professions intermédiaires' in value_lower or 'profession intermédiaire' in value_lower or \
       'professions intermediaires' in value_lower:
        return 4 if return_id else csp_descriptions[4]
    
    # Category 5: Employés
    if 'employ' in value_lower:
        return 5 if return_id else csp_descriptions[5]
    
    # Category 6: Ouvriers
    if 'ouvri' in value_lower:
        return 6 if return_id else csp_descriptions[6]
    
    # Special cases: Map to valid CSP categories
    # Note: Etudiant and Retraité are not official INSEE CSP categories
    # but we should preserve the data rather than lose it
    if 'etudiant' in value_lower or 'étudiant' in value_lower or 'student' in value_lower:
        # Students often have part-time jobs -> map to Employés as closest match
        return 5 if return_id else csp_descriptions[5]
    
    if 'retraite' in value_lower or 'retraité' in value_lower or 'retraitée' in value_lower or 'pension' in value_lower:
        # Retirees had a previous profession, but current CSP is "Retraités"
        # Since we don't have a CSP code for retirees, keep original value for traceability
        # Don't return None to avoid data loss
        return value_str_raw if not return_id else None  # Keep original text, or None for ID
    
    # If no match found, keep original value (for traceability in quality reports)
    # Don't silently convert to None which causes data loss
    return value_str_raw if not return_id else None


def map_csp_numeric_to_text(csp_code):
    """
    DEPRECATED: Use standardize_csp_value() instead.
    Kept for backward compatibility with existing code.
    """
    return standardize_csp_value(csp_code)


def clean_consommation_evry(base_path):
    """Clean Consommation_Evry data."""
    input_file = os.path.join(base_path, 'input_data', 'Consommation_Evry.csv')
    output_dir = os.path.join(base_path, 'cleaned_data')
    output_file = os.path.join(output_dir, 'Consommation_Evry_cleaned.csv')
    
    print("Cleaning Consommation_Evry...")
    df = pd.read_csv(input_file)
    
    initial_rows = len(df)
    
    # Clean postal codes
    df['Code_Postal'] = df['Code_Postal'].apply(clean_postal_code)
    
    # Normalize consumption units FIRST (before imputation)
    df['NB_KW_Jour'] = df['NB_KW_Jour'].apply(normalize_kw_to_kwh_per_day)
    
    # Impute missing NB_KW_Jour using column average
    missing_count = df['NB_KW_Jour'].isna().sum()
    if missing_count > 0:
        # Calculate average of non-null values
        avg_consumption = df['NB_KW_Jour'].mean()
        if pd.notna(avg_consumption):
            df['NB_KW_Jour'].fillna(avg_consumption, inplace=True)
            print(f"  ℹ Imputed {missing_count} missing NB_KW_Jour values with column average: {avg_consumption:.2f} kWh")
    
    # Remove rows with invalid critical fields
    df = df.dropna(subset=['Code_Postal', 'N', 'Nom_Rue'])
    
    # Remove duplicates based on address
    df = df.drop_duplicates(subset=['N', 'Nom_Rue', 'Code_Postal'], keep='first')
    
    final_rows = len(df)
    
    # Save cleaned data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"  ✓ Rows: {initial_rows} → {final_rows} (removed {initial_rows - final_rows})")
    print(f"  ✓ Saved to: {output_file}")
    
    return df


def clean_consommation_paris(base_path):
    """Clean Consommation_Paris data."""
    input_file = os.path.join(base_path, 'input_data', 'Consommation_Paris.csv')
    output_dir = os.path.join(base_path, 'cleaned_data')
    output_file = os.path.join(output_dir, 'Consommation_Paris_cleaned.csv')
    
    print("Cleaning Consommation_Paris...")
    df = pd.read_csv(input_file)
    
    initial_rows = len(df)
    
    # Clean postal codes
    df['Code_Postal'] = df['Code_Postal'].apply(clean_postal_code)
    
    # Normalize consumption units (Wh to kWh) FIRST
    df['NB_KW_Jour'] = df['NB_KW_Jour'].apply(normalize_kw_to_kwh_per_day)
    
    # Impute missing NB_KW_Jour using column average
    missing_count = df['NB_KW_Jour'].isna().sum()
    if missing_count > 0:
        # Calculate average of non-null values
        avg_consumption = df['NB_KW_Jour'].mean()
        if pd.notna(avg_consumption):
            df['NB_KW_Jour'].fillna(avg_consumption, inplace=True)
            print(f"  ℹ Imputed {missing_count} missing NB_KW_Jour values with column average: {avg_consumption:.2f} kWh")
    
    # Remove rows with invalid critical fields
    df = df.dropna(subset=['Code_Postal', 'N', 'Nom_Rue'])
    
    # Remove duplicates based on address
    df = df.drop_duplicates(subset=['N', 'Nom_Rue', 'Code_Postal'], keep='first')
    
    final_rows = len(df)
    
    # Save cleaned data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"  ✓ Rows: {initial_rows} → {final_rows} (removed {initial_rows - final_rows})")
    print(f"  ✓ Saved to: {output_file}")
    
    return df


def clean_population_paris(base_path):
    """Clean Population_Paris data."""
    input_file = os.path.join(base_path, 'input_data', 'Population_Paris.csv')
    output_dir = os.path.join(base_path, 'cleaned_data')
    output_file = os.path.join(output_dir, 'Population_Paris_cleaned.csv')
    
    print("Cleaning Population_Paris...")
    df = pd.read_csv(input_file)
    
    initial_rows = len(df)
    
    # Standardize addresses only for non-null values
    df['Adresse'] = df['Adresse'].apply(lambda x: standardize_address_paris(x) if pd.notna(x) and str(x).strip() != '' else x)
    
    # Standardize CSP values to ID_CSP (foreign key to CSP table)
    if 'CSP' in df.columns:
        df['ID_CSP'] = df['CSP'].apply(lambda x: standardize_csp_value(x, return_id=True))
        df = df.drop(columns=['CSP'])  # Remove old CSP column
    
    # Don't drop rows with null addresses - keep all data
    # df = df.dropna(subset=['Adresse'])
    
    # Remove duplicates based on ID
    df = df.drop_duplicates(subset=['ID_Personne'], keep='first')
    
    final_rows = len(df)
    
    # Save cleaned data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"  ✓ Rows: {initial_rows} → {final_rows} (removed {initial_rows - final_rows})")
    print(f"  ✓ Saved to: {output_file}")
    
    return df


def clean_population_evry(base_path):
    """Clean Population_Evry data."""
    input_file = os.path.join(base_path, 'input_data', 'Population_Evry.csv')
    output_dir = os.path.join(base_path, 'cleaned_data')
    output_file = os.path.join(output_dir, 'Population_Evry_cleaned.csv')
    
    print("Cleaning Population_Evry...")
    df = pd.read_csv(input_file)
    
    initial_rows = len(df)
    
    # Map numeric CSP codes to ID_CSP (keep as foreign key)
    df['ID_CSP'] = df['CSP'].apply(lambda x: standardize_csp_value(x, return_id=True))
    df = df.drop(columns=['CSP'])  # Remove old CSP column
    
    # Standardize addresses - keep original if standardization returns None
    def safe_standardize_address(addr):
        if pd.isna(addr) or str(addr).strip() == '':
            return addr
        standardized = standardize_address_evry(addr)
        # If standardization fails, keep the original address
        return standardized if standardized is not None else addr
    
    df['Adresse'] = df['Adresse'].apply(safe_standardize_address)
    
    # Don't drop rows with null addresses - keep all data
    # Some population records may not have addresses yet
    # df = df.dropna(subset=['Adresse', 'CSP'])
    
    # Remove duplicates based on ID
    df = df.drop_duplicates(subset=['ID_Personne'], keep='first')
    
    final_rows = len(df)
    
    # Save cleaned data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"  ✓ Rows: {initial_rows} → {final_rows} (removed {initial_rows - final_rows})")
    print(f"  ✓ Saved to: {output_file}")
    
    return df


def clean_csp_table(base_path):
    """Clean CSP reference table."""
    input_file = os.path.join(base_path, 'input_data', 'CSP.csv')
    output_dir = os.path.join(base_path, 'cleaned_data')
    output_file = os.path.join(output_dir, 'CSP_cleaned.csv')
    
    print("Cleaning CSP table...")
    df = pd.read_csv(input_file)
    
    initial_rows = len(df)
    
    # Handle column name variation
    salary_col = 'Salair_Moyen' if 'Salair_Moyen' in df.columns else 'Salaire_Moyen'
    
    # Impute missing Salaire_Moyen with average of Min and Max
    df[salary_col] = df.apply(
        lambda row: (float(str(row['Salaire_Min']).replace(' ', '')) + 
                     float(str(row['Salaire_Max']).replace(' ', ''))) / 2 
        if pd.isna(row[salary_col]) and pd.notna(row['Salaire_Min']) and pd.notna(row['Salaire_Max'])
        else row[salary_col], 
        axis=1
    )
    
    # Standardize salary column name
    if salary_col == 'Salair_Moyen':
        df = df.rename(columns={'Salair_Moyen': 'Salaire_Moyen'})
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['ID_CSP'], keep='first')
    
    final_rows = len(df)
    
    # Save cleaned data
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"  ✓ Rows: {initial_rows} → {final_rows} (removed {initial_rows - final_rows})")
    print(f"  ✓ Saved to: {output_file}")
    
    return df


def main():
    """Main cleaning function."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent
    
    print("\n" + "="*60)
    print("DATA CLEANING PIPELINE")
    print("="*60 + "\n")
    
    # Clean all tables
    clean_consommation_evry(base_path)
    clean_consommation_paris(base_path)
    clean_population_paris(base_path)
    clean_population_evry(base_path)
    clean_csp_table(base_path)
    
    print("\n" + "="*60)
    print("✓ DATA CLEANING COMPLETED")
    print("="*60)


if __name__ == '__main__':
    main()
