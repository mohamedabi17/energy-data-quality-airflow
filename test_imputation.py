import pandas as pd
import sys
sys.path.insert(0, 'dags/scripts')
from clean_data import standardize_csp_value

# Load data
conso = pd.read_csv('input_data/Consommation_Evry.csv')
pop = pd.read_csv('input_data/Population_Evry.csv')
csp = pd.read_csv('input_data/CSP.csv')

print("=== CONSUMPTION DATA ===")
print(conso[['ID_Adr', 'N', 'Nom_Rue', 'NB_KW_Jour']].head(6))

print("\n=== POPULATION DATA ===")
print(pop[['ID_Personne', 'Adresse', 'CSP']].head(6))

# Create address keys
conso['key'] = conso['N'].astype(str) + ' ' + conso['Nom_Rue'].str.upper().str.strip()
pop['key'] = pop['Adresse'].apply(lambda x: str(x).split(',')[-1].strip().upper() if pd.notna(x) and x != '' else None)

print("\n=== ADDRESS KEYS COMPARISON ===")
print("Consumption keys:")
print(conso[['key', 'NB_KW_Jour']].head(6))
print("\nPopulation keys:")
print(pop[['key', 'CSP']].head(6))

# For each consumption address, take the FIRST matching person's CSP
# (since consumption is per address, not per person)
pop_unique = pop.drop_duplicates(subset=['key'], keep='first')

merged = conso.merge(
    pop_unique[['key', 'CSP']].dropna(subset=['key']),
    on='key',
    how='left'
)

print("\n=== AFTER MERGE (unique addresses) ===")
print(f"Shape: {merged.shape}")
print(merged[['N', 'Nom_Rue', 'CSP', 'NB_KW_Jour']].head(6))

# Convert CSP to numeric ID
merged['CSP_numeric'] = merged['CSP'].apply(
    lambda x: standardize_csp_value(x, return_id=True) if pd.notna(x) else None
)
merged['CSP_numeric'] = pd.to_numeric(merged['CSP_numeric'], errors='coerce')

# Merge with salary data
merged = merged.merge(
    csp[['ID_CSP', 'Salaire_Min', 'Salaire_Max']],
    left_on='CSP_numeric',
    right_on='ID_CSP',
    how='left'
)

print("\n=== AFTER CSP SALARY MERGE ===")
print(merged[['N', 'Nom_Rue', 'CSP_numeric', 'Salaire_Min', 'Salaire_Max', 'NB_KW_Jour']].head(6))

# Calculate imputation
missing_mask = merged['NB_KW_Jour'].isna()
has_salary_data = merged['Salaire_Max'].notna() & merged['Salaire_Min'].notna()
impute_mask = missing_mask & has_salary_data

print(f"\n=== IMPUTATION ===")
print(f"Rows with missing NB_KW_Jour: {missing_mask.sum()}")
print(f"Rows with salary data: {has_salary_data.sum()}")
print(f"Rows to impute: {impute_mask.sum()}")

if impute_mask.sum() > 0:
    print("\nRows being imputed:")
    print(merged[impute_mask][['N', 'Nom_Rue', 'CSP_numeric', 'Salaire_Min', 'Salaire_Max']])
    
    merged.loc[impute_mask, 'NB_KW_Jour'] = (
        (merged.loc[impute_mask, 'Salaire_Max'] - merged.loc[impute_mask, 'Salaire_Min']) / 2
    )
    
    print("\nAfter imputation:")
    print(merged[['N', 'Nom_Rue', 'CSP_numeric', 'NB_KW_Jour']].head(6))
