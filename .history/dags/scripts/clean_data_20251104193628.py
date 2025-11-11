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
    
    # Remove postal code if present
    addr_str = re.sub(r',\s*\d{5},', ',', addr_str)
    
    # Ensure "Evry-Courcouronnes" format
    addr_str = re.sub(r'^Evry[^-]*', 'Evry-Courcouronnes', addr_str, flags=re.IGNORECASE)
    
    # Check if matches expected format
    if re.match(r'Evry-Courcouronnes,\s+\d+\s+(rue|boulevard|allée|square|place)\s+.+', addr_str, re.IGNORECASE):
        return addr_str
    
    return None


def map_csp_numeric_to_text(csp_code):
    """
    Map numeric CSP codes to text descriptions.
    Based on CSP.csv ID_CSP values.
    """
    csp_mapping = {
        '1': 'Agriculteurs exploitants / algricultrices exploitantes',
        '2': 'Artisans / artisanes, commerçants / commerçantes et chefs / cheffes d\'entreprise',
        '3': 'Cadres et professions intellectuelles supérieures',
        '4': 'Professions intermédiaires',
        '5': 'Employés / employées',
        '6': 'Ouvriers / ouvrières'
    }
    
    if pd.isna(csp_code):
        return None
    
    code_str = str(csp_code).strip()
    return csp_mapping.get(code_str, csp_code)


def clean_consommation_evry(base_path):
    """Clean Consommation_Evry data."""
    input_file = os.path.join(base_path, 'Consommation_Evry.csv')
    output_dir = os.path.join(base_path, 'cleaned_data')
    output_file = os.path.join(output_dir, 'Consommation_Evry_cleaned.csv')
    
    print("Cleaning Consommation_Evry...")
    df = pd.read_csv(input_file)
    
    initial_rows = len(df)
    
    # Clean postal codes
    df['Code_Postal'] = df['Code_Postal'].apply(clean_postal_code)
    
    # Normalize consumption units
    df['NB_KW_Jour'] = df['NB_KW_Jour'].apply(normalize_kw_to_kwh_per_day)
    
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
    input_file = os.path.join(base_path, 'Consommation_Paris.csv')
    output_dir = os.path.join(base_path, 'cleaned_data')
    output_file = os.path.join(output_dir, 'Consommation_Paris_cleaned.csv')
    
    print("Cleaning Consommation_Paris...")
    df = pd.read_csv(input_file)
    
    initial_rows = len(df)
    
    # Clean postal codes
    df['Code_Postal'] = df['Code_Postal'].apply(clean_postal_code)
    
    # Normalize consumption units (Wh to kWh)
    df['NB_KW_Jour'] = df['NB_KW_Jour'].apply(normalize_kw_to_kwh_per_day)
    
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
    input_file = os.path.join(base_path, 'Population_Paris.csv')
    output_dir = os.path.join(base_path, 'cleaned_data')
    output_file = os.path.join(output_dir, 'Population_Paris_cleaned.csv')
    
    print("Cleaning Population_Paris...")
    df = pd.read_csv(input_file)
    
    initial_rows = len(df)
    
    # Standardize addresses only for non-null values
    df['Adresse'] = df['Adresse'].apply(lambda x: standardize_address_paris(x) if pd.notna(x) and str(x).strip() != '' else x)
    
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
    input_file = os.path.join(base_path, 'Population_Evry.csv')
    output_dir = os.path.join(base_path, 'cleaned_data')
    output_file = os.path.join(output_dir, 'Population_Evry_cleaned.csv')
    
    print("Cleaning Population_Evry...")
    df = pd.read_csv(input_file)
    
    initial_rows = len(df)
    
    # Map numeric CSP codes to text FIRST (before filtering)
    df['CSP'] = df['CSP'].apply(map_csp_numeric_to_text)
    
    # Standardize addresses only for non-null values
    df['Adresse'] = df['Adresse'].apply(lambda x: standardize_address_evry(x) if pd.notna(x) and str(x).strip() != '' else x)
    
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
    input_file = os.path.join(base_path, 'CSP.csv')
    output_file = os.path.join(base_path, 'cleaned_data', 'CSP_cleaned.csv')
    
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
