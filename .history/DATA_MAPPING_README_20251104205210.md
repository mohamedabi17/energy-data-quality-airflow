# Data Mapping & Aggregation Documentation

## Overview
This document explains how source data is transformed and joined to create the target schemas (output tables) in the data quality pipeline.

---

## 📊 Source Tables (Input)

### 1. **Consommation_Paris.csv** (13 rows)
- **Primary Key**: `ID_Conso`
- **Key Columns**: `CP` (postal code), `Nom_Rue` (street name), `NB_KW_Jour` (daily consumption in kW or Wh)
- **Purpose**: Energy consumption data for Paris addresses

### 2. **Consommation_Evry.csv** (12 rows)
- **Primary Key**: `ID_Conso`
- **Key Columns**: `CP`, `Nom_Rue`, `NB_KW_Jour`
- **Purpose**: Energy consumption data for Evry-Courcouronnes addresses

### 3. **Population_Paris.csv** (12 rows)
- **Primary Key**: `ID_Personne`
- **Key Columns**: `Adresse` (full address), `CSP` (socio-professional category)
- **Purpose**: Population demographics for Paris residents

### 4. **Population_Evry.csv** (12 rows)
- **Primary Key**: `ID_Personne`
- **Key Columns**: `Adresse`, `CSP` (numeric codes 1-6)
- **Purpose**: Population demographics for Evry residents

### 5. **IRIS.csv** (11 rows)
- **Primary Key**: `ID_IRIS`
- **Key Columns**: `ID_Ville` (city), `ID_Rue` (street name), `ID_IRIS` (geographic zone code)
- **Purpose**: Geographic mapping reference - maps streets to IRIS zones

### 6. **CSP.csv** (6 rows)
- **Primary Key**: `ID_CSP`
- **Key Columns**: `ID_CSP` (1-6), `Desc` (description), `Salaire_Moyen` (average salary)
- **Purpose**: Reference table for socio-professional categories

---

## 🎯 Target Tables (Output)

### Target 1: **Consommation_IRIS_Paris.csv**
**Schema**: `(ID_IRIS, Conso_moyenne_annuelle)`

#### Mapping Logic:
```
STEP 1: Load Data
   - Source: Consommation_Paris_cleaned.csv
   - Reference: IRIS.csv

STEP 2: Extract Street Names
   - From: Nom_Rue column (e.g., "rue Arthur Groussier")
   - Transform: Uppercase for matching

STEP 3: Join with IRIS
   - Join Type: LEFT JOIN
   - Join Key: Street name (fuzzy match)
   - Condition: 
     * cons.Nom_Rue CONTAINS iris.ID_Rue 
     * AND iris.ID_Ville = 'Paris'
   - Result: Each consumption record gets an ID_IRIS

STEP 4: Calculate Annual Consumption
   - Formula: Conso_annuelle = NB_KW_Jour × 365
   - Unit: kWh per year

STEP 5: Aggregate by IRIS
   - Group By: ID_IRIS
   - Aggregation: AVG(Conso_annuelle)
   - Output: One row per IRIS zone
```

**Output**: 5 IRIS zones for Paris

---

### Target 2: **Consommation_IRIS_Evry.csv**
**Schema**: `(ID_IRIS, Conso_moyenne_annuelle)`

#### Mapping Logic:
```
STEP 1: Load Data
   - Source: Consommation_Evry_cleaned.csv
   - Reference: IRIS.csv

STEP 2: Extract Street Names
   - From: Nom_Rue column
   - Transform: Uppercase

STEP 3: Join with IRIS
   - Join Type: LEFT JOIN
   - Join Key: Street name (fuzzy match)
   - Condition:
     * cons.Nom_Rue CONTAINS iris.ID_Rue
     * AND iris.ID_Ville = 'Evry-Courcouronnes'
   - Result: Each consumption record gets an ID_IRIS

STEP 4: Calculate Annual Consumption
   - Formula: Conso_annuelle = NB_KW_Jour × 365
   - Unit: kWh per year

STEP 5: Aggregate by IRIS
   - Group By: ID_IRIS
   - Aggregation: AVG(Conso_annuelle)
   - Output: One row per IRIS zone
```

**Output**: 6 IRIS zones for Evry-Courcouronnes

---

### Target 3: **Consommation_CSP.csv**
**Schema**: `(ID_CSP, Conso_moyenne_annuelle, Salaire_Moyen)`

#### Mapping Logic (Most Complex):
```
STEP 1: Load All Data
   - Population_Paris_cleaned.csv
   - Population_Evry_cleaned.csv
   - Consommation_Paris_cleaned.csv
   - Consommation_Evry_cleaned.csv
   - CSP_cleaned.csv

STEP 2: Combine Population Data
   - Union: Population_Paris + Population_Evry
   - Result: 24 people total (12 + 12)

STEP 3: Map CSP to ID_CSP
   - From: CSP text/code (e.g., "Cadre", "3", "Employés / employées")
   - To: ID_CSP (1-6)
   - Method: Fuzzy matching with CSP.csv Desc column
   - Example:
     * "Cadre" → ID_CSP = 3 ("Cadres et professions intellectuelles supérieures")
     * "5" → ID_CSP = 5 ("Employés / employées")

STEP 4: Extract Street from Population Addresses
   - From: "Paris, 20 rue Arthur Groussier" 
   - Extract: "ARTHUR GROUSSIER" (street name only)
   - Regex: /(?:rue|boulevard|allée|square)\s+(.+)$/

STEP 5: Extract Street from Consumption Data
   - From: Nom_Rue column
   - Transform: Uppercase

STEP 6: Combine Consumption Data
   - Union: Consommation_Paris + Consommation_Evry
   - Result: 25 consumption records (13 + 12)

STEP 7: Join Population with Consumption
   - Join Type: INNER JOIN
   - Join Key: Street name
   - Condition: pop.Street = cons.Street
   - Result: People matched with their consumption data
   - Note: Only records with matching streets are kept

STEP 8: Calculate Annual Consumption
   - Formula: Conso_annuelle = NB_KW_Jour × 365
   - Unit: kWh per year

STEP 9: Aggregate by CSP
   - Group By: ID_CSP
   - Aggregation: AVG(Conso_annuelle)
   - Result: Average consumption per CSP category

STEP 10: Join with CSP Table for Salary
   - Join Type: LEFT JOIN
   - Join Key: ID_CSP
   - Columns: ID_CSP, Salaire_Moyen
   - Result: Each CSP category now has avg consumption + avg salary
```

**Output**: 6 CSP categories (1-6)

---

## 🔗 Join Relationships Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                    TARGET 1 & 2: IRIS Tables                   │
└────────────────────────────────────────────────────────────────┘

Consommation_Paris/Evry              IRIS.csv
┌─────────────────────┐            ┌──────────────────┐
│ ID_Conso            │            │ ID_IRIS (PK)     │
│ Nom_Rue ──────────────(fuzzy)────▶ ID_Rue          │
│ NB_KW_Jour          │            │ ID_Ville         │
│ CP                  │            └──────────────────┘
└─────────────────────┘                    │
         │                                 │
         └──── GROUP BY ID_IRIS ───────────┘
                      ↓
         ┌────────────────────────────┐
         │ Consommation_IRIS_Paris/   │
         │         Evry               │
         │ ─────────────────────────  │
         │ ID_IRIS                    │
         │ Conso_moyenne_annuelle     │
         └────────────────────────────┘


┌────────────────────────────────────────────────────────────────┐
│                    TARGET 3: CSP Table                         │
└────────────────────────────────────────────────────────────────┘

Population_Paris/Evry              CSP.csv
┌─────────────────────┐          ┌──────────────────┐
│ ID_Personne         │          │ ID_CSP (PK)      │
│ Adresse             │          │ Desc             │
│ CSP ────────────(match)────────▶ Salaire_Moyen   │
└─────────────────────┘          └──────────────────┘
         │                                 │
    (extract street)                       │
         │                                 │
         ↓                                 │
┌─────────────────────┐                   │
│ Street (derived)    │                   │
└─────────────────────┘                   │
         │                                 │
         │     Consommation_Paris/Evry     │
         │     ┌─────────────────────┐     │
         │     │ Nom_Rue             │     │
         └──(join)──▶ NB_KW_Jour     │     │
               └─────────────────────┘     │
                        │                  │
              GROUP BY ID_CSP              │
                        │                  │
                        └───(join)─────────┘
                                ↓
                ┌──────────────────────────┐
                │   Consommation_CSP       │
                │ ───────────────────────  │
                │ ID_CSP                   │
                │ Conso_moyenne_annuelle   │
                │ Salaire_Moyen            │
                └──────────────────────────┘
```

---

## 🔑 Key Matching Strategies

### 1. **IRIS Mapping (Street → IRIS Zone)**
- **Method**: Fuzzy string matching
- **Algorithm**: 
  ```python
  if street_name IN iris.ID_Rue OR iris.ID_Rue IN street_name:
      return iris.ID_IRIS
  ```
- **Case Handling**: All uppercase comparison
- **City Filter**: Only match streets in correct city (Paris or Evry)
- **Unmatched**: Dropped from output

### 2. **CSP Mapping (Text/Code → ID_CSP)**
- **Method**: Text matching with CSP reference table
- **Examples**:
  - "Cadre" → matches "Cadres et professions intellectuelles supérieures" → ID_CSP = 3
  - "Employé" → matches "Employés / employées" → ID_CSP = 5
  - Numeric "5" → directly maps to ID_CSP = 5
- **Case Handling**: Lowercase comparison
- **Variations**: Handles singular/plural (Employé/Employés)

### 3. **Street Address Matching (Population ↔ Consumption)**
- **Method**: Extract street name, exact match
- **Extraction Regex**: `/(?:rue|boulevard|allée|square)\s+(.+)$/`
- **Examples**:
  - "Paris, 20 rue Arthur Groussier" → "ARTHUR GROUSSIER"
  - "Evry-Courcouronnes, 19 Boulevard Aguado" → "AGUADO"
- **Join Type**: INNER JOIN (only keep matches)
- **Limitation**: People without matching streets are excluded

---

## 📈 Data Flow Summary

```
RAW DATA (6 CSV files)
    ↓
CLEANING PHASE
    ├─ Unit normalization (Wh → kWh)
    ├─ Address standardization
    ├─ CSP code/text standardization
    └─ Duplicate removal
    ↓
CLEANED DATA (5 CSV files)
    ↓
AGGREGATION PHASE
    ├─ Join with IRIS.csv
    ├─ Join with CSP.csv
    ├─ Street name extraction
    ├─ Population ↔ Consumption matching
    └─ Group by & aggregate
    ↓
TARGET SCHEMAS (3 CSV files)
    ├─ Consommation_IRIS_Paris.csv (5 rows)
    ├─ Consommation_IRIS_Evry.csv (6 rows)
    └─ Consommation_CSP.csv (6 rows)
```

---

## 🎓 Business Logic

### IRIS Aggregation (Geographic Analysis)
**Purpose**: Analyze energy consumption by neighborhood zones (IRIS = Îlots Regroupés pour l'Information Statistique)

**Use Case**: Urban planners can identify high/low consumption zones for infrastructure planning

**Calculation**:
- Average annual consumption per IRIS = (Sum of all addresses in IRIS) / (Number of addresses)
- Each address consumption = Daily consumption × 365 days

### CSP Aggregation (Socio-Economic Analysis)
**Purpose**: Correlate energy consumption with socio-professional categories and salary levels

**Use Case**: Energy providers can tailor offers based on CSP profiles and understand consumption patterns by profession

**Calculation**:
- Average annual consumption per CSP = (Sum of all people in CSP) / (Number of people)
- Includes average salary from CSP reference table for correlation analysis

---

## ⚠️ Important Notes

### Data Quality Considerations:
1. **Street Matching**: Not all people can be matched to consumption data (different street names or missing addresses)
2. **IRIS Coverage**: Some streets may not be in IRIS.csv, resulting in dropped records
3. **CSP Standardization**: Non-standard CSP values (e.g., "Retraitée", "Etudiant") are preserved for traceability
4. **Annual Calculation**: Assumes 365-day year, no seasonal variations considered

### Cardinality:
- **One-to-Many**: One IRIS zone → Many consumption records
- **Many-to-One**: Many people → One CSP category
- **One-to-One**: One street address → One consumption record (ideally, but may have duplicates)

---

## 📝 Files Generated

### Cleaned Data Directory (`cleaned_data/`)
- `Consommation_Paris_cleaned.csv` (13 rows)
- `Consommation_Evry_cleaned.csv` (12 rows)
- `Population_Paris_cleaned.csv` (12 rows)
- `Population_Evry_cleaned.csv` (12 rows)
- `CSP_cleaned.csv` (6 rows)

### Target Schemas Directory (`target_schemas/`)
- `Consommation_IRIS_Paris.csv` (5 rows)
- `Consommation_IRIS_Evry.csv` (6 rows)
- `Consommation_CSP.csv` (6 rows)

### Metadata Directory (`metadata/`)
- `metadata_qd_raw_latest.csv` (40+ metrics on raw data)
- `metadata_qd_cleaned_latest.csv` (40+ metrics on cleaned data)

---

## 🚀 Execution Order

1. **Stage 1: Raw Metrics** → `compute_metrics.py` on `input_data/`
2. **Stage 2: Data Cleaning** → `clean_data.py` creates `cleaned_data/`
3. **Stage 3: Aggregation** → `aggregate_data.py` creates `target_schemas/`
4. **Stage 4: Cleaned Metrics** → `compute_metrics.py` on `cleaned_data/`

---

*Last Updated: November 4, 2025*
*Pipeline Version: 1.0*
