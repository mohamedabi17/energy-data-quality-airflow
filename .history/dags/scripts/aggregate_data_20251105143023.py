"""
Data Aggregation Script
Creates target schema tables with aggregated consumption data.
"""

import os
import pandas as pd
import re
from pathlib import Path


def extract_street_from_address(address):
    """Extract street name from address."""
    if pd.isna(address):
        return None
    
    # Pattern to extract street name after "rue", "boulevard", etc.
    match = re.search(r'(?:rue|boulevard|allée|allee|square|place)\s+(.+)$', str(address), re.IGNORECASE)
    if match:
        return match.group(1).strip().upper()
    return None


def map_address_to_iris(street_name, iris_df, city):
    """Map street name to IRIS code."""
    if pd.isna(street_name):
        return None
    
    # Filter by city
    city_iris = iris_df[iris_df['ID_Ville'] == city]
    
    # Try to match street name (case insensitive)
    for _, row in city_iris.iterrows():
        if str(row['ID_Rue']).upper() in street_name.upper() or street_name.upper() in str(row['ID_Rue']).upper():
            return row['ID_IRIS']
    
    return None


def map_csp_to_id(csp_desc, csp_df):
    """Map CSP description to ID_CSP."""
    if pd.isna(csp_desc):
        return None
    
    csp_str = str(csp_desc).strip().lower()
    
    for _, row in csp_df.iterrows():
        if str(row['Desc']).strip().lower() in csp_str or csp_str in str(row['Desc']).strip().lower():
            return row['ID_CSP']
    
    return None


def create_consommation_iris_paris(base_path):
    """
    Create Consommation_IRIS_Paris(ID_IRIS, Conso_moyenne_annuelle)
    """
    print("Creating Consommation_IRIS_Paris...")
    
    # Load cleaned data
    cons_file = os.path.join(base_path, 'cleaned_data', 'Consommation_Paris_cleaned.csv')
    iris_file = os.path.join(base_path, 'input_data', 'IRIS.csv')
    
    cons_df = pd.read_csv(cons_file)
    iris_df = pd.read_csv(iris_file)
    
    # Extract street names from consumption data
    cons_df['Street'] = cons_df['Nom_Rue'].str.strip().str.upper()
    
    # Map to IRIS
    cons_df['ID_IRIS'] = cons_df['Street'].apply(
        lambda x: map_address_to_iris(x, iris_df, 'Paris')
    )
    
    # Remove rows without IRIS mapping
    cons_df = cons_df.dropna(subset=['ID_IRIS'])
    
    # Standardize IRIS codes to uppercase (fix case sensitivity issues)
    cons_df['ID_IRIS'] = cons_df['ID_IRIS'].str.upper()
    
    # Calculate annual consumption (daily * 365)
    cons_df['Conso_annuelle'] = cons_df['NB_KW_Jour'] * 365
    
    # Aggregate by IRIS (now case-insensitive due to uppercase standardization)
    result = cons_df.groupby('ID_IRIS').agg({
        'Conso_annuelle': 'mean'
    }).reset_index()
    
    result.columns = ['ID_IRIS', 'Conso_moyenne_annuelle']
    result['Conso_moyenne_annuelle'] = result['Conso_moyenne_annuelle'].round(2)
    
    # Save to target_schemas directory
    output_dir = os.path.join(base_path, 'target_schemas')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'Consommation_IRIS_Paris.csv')
    result.to_csv(output_file, index=False)
    
    print(f"  ✓ Created {len(result)} IRIS groups")
    print(f"  ✓ Saved to: {output_file}")
    
    return result


def create_consommation_iris_evry(base_path):
    """
    Create Consommation_IRIS_Evry(ID_IRIS, Conso_moyenne_annuelle)
    """
    print("Creating Consommation_IRIS_Evry...")
    
    # Load cleaned data
    cons_file = os.path.join(base_path, 'cleaned_data', 'Consommation_Evry_cleaned.csv')
    iris_file = os.path.join(base_path, 'input_data', 'IRIS.csv')
    
    cons_df = pd.read_csv(cons_file)
    iris_df = pd.read_csv(iris_file)
    
    # Extract street names from consumption data
    cons_df['Street'] = cons_df['Nom_Rue'].str.strip().str.upper()
    
    # Map to IRIS
    cons_df['ID_IRIS'] = cons_df['Street'].apply(
        lambda x: map_address_to_iris(x, iris_df, 'Evry-Courcouronnes')
    )
    
    # Remove rows without IRIS mapping
    cons_df = cons_df.dropna(subset=['ID_IRIS'])
    
    # Standardize IRIS codes to uppercase (fix case sensitivity issues)
    # This prevents duplicates like "AGUADO" vs "Aguado"
    cons_df['ID_IRIS'] = cons_df['ID_IRIS'].str.upper()
    
    # Calculate annual consumption (daily * 365)
    cons_df['Conso_annuelle'] = cons_df['NB_KW_Jour'] * 365
    
    # Aggregate by IRIS (now case-insensitive due to uppercase standardization)
    result = cons_df.groupby('ID_IRIS').agg({
        'Conso_annuelle': 'mean'
    }).reset_index()
    
    result.columns = ['ID_IRIS', 'Conso_moyenne_annuelle']
    result['Conso_moyenne_annuelle'] = result['Conso_moyenne_annuelle'].round(2)
    
    # Save to target_schemas directory
    output_dir = os.path.join(base_path, 'target_schemas')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'Consommation_IRIS_Evry.csv')
    result.to_csv(output_file, index=False)
    
    print(f"  ✓ Created {len(result)} IRIS groups (case-insensitive)")
    print(f"  ✓ Saved to: {output_file}")
    
    return result


def create_consommation_csp(base_path):
    """
    Create Consommation_CSP(ID_CSP, Conso_moyenne_annuelle, Salaire_Moyen)
    """
    print("Creating Consommation_CSP...")
    
    # Load cleaned data
    pop_paris_file = os.path.join(base_path, 'cleaned_data', 'Population_Paris_cleaned.csv')
    pop_evry_file = os.path.join(base_path, 'cleaned_data', 'Population_Evry_cleaned.csv')
    cons_paris_file = os.path.join(base_path, 'cleaned_data', 'Consommation_Paris_cleaned.csv')
    cons_evry_file = os.path.join(base_path, 'cleaned_data', 'Consommation_Evry_cleaned.csv')
    csp_file = os.path.join(base_path, 'cleaned_data', 'CSP_cleaned.csv')
    
    pop_paris_df = pd.read_csv(pop_paris_file)
    pop_evry_df = pd.read_csv(pop_evry_file)
    cons_paris_df = pd.read_csv(cons_paris_file)
    cons_evry_df = pd.read_csv(cons_evry_file)
    csp_df = pd.read_csv(csp_file)
    
    # Combine population data (already has ID_CSP as foreign key)
    pop_df = pd.concat([pop_paris_df, pop_evry_df], ignore_index=True)
    
    # ID_CSP is already present from cleaning phase, just filter out nulls
    pop_df = pop_df.dropna(subset=['ID_CSP'])
    
    # Extract street from addresses for matching
    pop_df['Street'] = pop_df['Adresse'].apply(extract_street_from_address)
    cons_paris_df['Street'] = cons_paris_df['Nom_Rue'].str.strip().str.upper()
    cons_evry_df['Street'] = cons_evry_df['Nom_Rue'].str.strip().str.upper()
    
    # Combine consumption data
    cons_df = pd.concat([cons_paris_df, cons_evry_df], ignore_index=True)
    
    # Join population with consumption on street name
    merged = pop_df.merge(cons_df, on='Street', how='inner')
    
    # Calculate annual consumption
    merged['Conso_annuelle'] = merged['NB_KW_Jour'] * 365
    
    # Aggregate by CSP
    csp_consumption = merged.groupby('ID_CSP').agg({
        'Conso_annuelle': 'mean'
    }).reset_index()
    
    # Merge with CSP table to get Salaire_Moyen
    result = csp_consumption.merge(
        csp_df[['ID_CSP', 'Salaire_Moyen']], 
        on='ID_CSP', 
        how='left'
    )
    
    result.columns = ['ID_CSP', 'Conso_moyenne_annuelle', 'Salaire_Moyen']
    result['Conso_moyenne_annuelle'] = result['Conso_moyenne_annuelle'].round(2)
    
    # Save to target_schemas directory
    output_dir = os.path.join(base_path, 'target_schemas')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'Consommation_CSP.csv')
    result.to_csv(output_file, index=False)
    
    print(f"  ✓ Created {len(result)} CSP groups")
    print(f"  ✓ Saved to: {output_file}")
    
    return result


def main():
    """Main aggregation function."""
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent
    
    print("\n" + "="*60)
    print("DATA AGGREGATION PIPELINE")
    print("="*60 + "\n")
    
    # Create target schemas
    create_consommation_iris_paris(base_path)
    create_consommation_iris_evry(base_path)
    create_consommation_csp(base_path)
    
    print("\n" + "="*60)
    print("✓ DATA AGGREGATION COMPLETED")
    print("="*60)


if __name__ == '__main__':
    main()
