# 🧹 Clean Data Script Documentation

> **Comprehensive guide to the `clean_data.py` script - the core data cleaning and standardization module**

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Installation & Usage](#installation--usage)
3. [Functions Reference](#functions-reference)
4. [Cleaning Rules](#cleaning-rules)
5. [Input/Output Structure](#inputoutput-structure)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

**File:** `dags/scripts/clean_data.py`  
**Purpose:** Clean and standardize all raw data files (consumption, population, CSP reference)  
**Language:** Python 3.7+  
**Dependencies:** `pandas`, `re`, `pathlib`

### What It Does

```
📥 INPUT: Raw CSV files from input_data/
    ├── Consommation_Evry.csv
    ├── Consommation_Paris.csv
    ├── Population_Evry.csv
    ├── Population_Paris.csv
    └── CSP.csv

🔧 PROCESSING: Apply cleaning rules
    ├── Postal code validation
    ├── Unit normalization (Wh → kWh)
    ├── Missing value imputation
    ├── Address standardization
    ├── CSP reference validation
    └── Duplicate removal

📤 OUTPUT: Cleaned CSV files in cleaned_data/
    ├── Consommation_Evry_cleaned.csv
    ├── Consommation_Paris_cleaned.csv
    ├── Population_Evry_cleaned.csv
    ├── Population_Paris_cleaned.csv
    └── CSP_cleaned.csv
```

---

## 🚀 Installation & Usage

### Prerequisites

```bash
# Required Python packages
pip install pandas
```

### Running the Script

#### **Option 1: Standalone Execution**
```bash
# From project root
python dags/scripts/clean_data.py
```

#### **Option 2: As Part of Pipeline**
```bash
# Run full pipeline (includes cleaning)
python dags/scripts/compute_metrics.py --stage raw
python dags/scripts/clean_data.py
python dags/scripts/aggregate_data.py
python dags/scripts/compute_metrics.py --stage cleaned
```

#### **Option 3: Via Airflow DAG**
```bash
# Start Airflow scheduler
airflow scheduler

# Trigger DAG
airflow dags trigger data_quality_dag
```

#### **Option 4: Via Interactive Dashboard**
```bash
# Launch dashboard with live pipeline control
python dags/scripts/visualize_dashboard.py --server
# Then click "Launch Pipeline" button in browser
```

### Expected Output

```
============================================================
DATA CLEANING PIPELINE
============================================================

Cleaning Consommation_Evry...
  ℹ Imputed 5 missing NB_KW_Jour values with column average: 86.60 kWh
  ✓ Rows: 12 → 12 (removed 0)
  ✓ Saved to: cleaned_data/Consommation_Evry_cleaned.csv

Cleaning Consommation_Paris...
  ℹ Imputed 0 missing NB_KW_Jour values with column average: 1.55 kWh
  ✓ Rows: 13 → 13 (removed 0)
  ✓ Saved to: cleaned_data/Consommation_Paris_cleaned.csv

Cleaning Population_Paris...
  ✓ Rows: 12 → 12 (removed 0)
  ✓ Saved to: cleaned_data/Population_Paris_cleaned.csv

Cleaning Population_Evry...
  ✓ Rows: 12 → 12 (removed 0)
  ✓ Saved to: cleaned_data/Population_Evry_cleaned.csv

Cleaning CSP table...
  ℹ Imputed 1 missing Salaire_Moyen values from Min/Max average
  ℹ Added category 7 (Retraités) with averaged salary data:
    - Salaire_Moyen: 2850.00
    - Salaire_Min: 1900.00
    - Salaire_Max: 3800.00
  ✓ Rows: 6 → 7 (added 1)
  ✓ Saved to: cleaned_data/CSP_cleaned.csv

============================================================
✓ DATA CLEANING COMPLETED
============================================================
```

---

## 📚 Functions Reference

### **1. `clean_postal_code(code)`**

**Purpose:** Validate and standardize postal codes to 5 digits.

**Parameters:**
- `code` (str/int/float): Raw postal code value

**Returns:**
- `str`: Cleaned 5-digit postal code
- `None`: If invalid or missing

**Logic:**
```python
1. Handle NULL/NaN → return None
2. Convert to string and strip whitespace
3. Remove all non-digit characters (letters, spaces)
4. Extract first 5 digits
5. Validate length (must be exactly 5 digits)
```

**Examples:**
```python
clean_postal_code("91000")     # → "91000"
clean_postal_code("91000a")    # → "91000"
clean_postal_code("9100000")   # → "91000"
clean_postal_code(91000)       # → "91000"
clean_postal_code("75 016")    # → "75016"
clean_postal_code("123")       # → None (too short)
clean_postal_code(None)        # → None
clean_postal_code("")          # → None
```

**Used By:**
- `clean_consommation_evry()`
- `clean_consommation_paris()`

---

### **2. `normalize_kw_to_kwh_per_day(value)`**

**Purpose:** Normalize consumption values to kWh/day (convert Wh to kWh if needed).

**Parameters:**
- `value` (float/int/str): Raw consumption value

**Returns:**
- `float`: Normalized value in kWh/day (rounded to 2 decimals)
- `None`: If invalid or negative

**Logic:**
```python
1. Handle NULL/NaN → return None
2. Convert to float
3. Reject negative values → return None
4. If value > 1000:
     Assume Wh/day → convert to kWh (divide by 1000)
5. Otherwise:
     Assume already in kWh → keep as-is
6. Round to 2 decimal places
```

**Threshold Rationale:**
- **Paris data:** Originally in Wh/day (e.g., 1548.49 Wh)
- **Évry data:** Originally in kWh/day (e.g., 12.58 kWh)
- **Threshold 1000:** Differentiates between units (max residential kWh/day < 1000)

**Examples:**
```python
normalize_kw_to_kwh_per_day(1548.49)  # → 1.55 kWh (converted from Wh)
normalize_kw_to_kwh_per_day(12.58)    # → 12.58 kWh (already kWh)
normalize_kw_to_kwh_per_day(548.493)  # → 0.55 kWh (converted from Wh)
normalize_kw_to_kwh_per_day(-5)       # → None (negative rejected)
normalize_kw_to_kwh_per_day(None)     # → None
normalize_kw_to_kwh_per_day("abc")    # → None (invalid)
```

**Used By:**
- `clean_consommation_evry()`
- `clean_consommation_paris()`

---

### **3. `standardize_address_paris(address)`**

**Purpose:** Standardize Paris addresses to consistent format.

**Parameters:**
- `address` (str): Raw address string

**Returns:**
- `str`: Standardized address in format `"Paris, [N] rue [street]"`
- `None`: If invalid or missing

**Format:** `"Paris, [number] rue [street name]"`

**Logic:**
```python
1. Handle NULL/empty → return None
2. Strip whitespace
3. Check if already in correct format → return as-is
4. Fix spacing after "Paris," (normalize to single space)
5. Validate final format with regex
6. Return standardized address or None if invalid
```

**Validation Regex:**
```python
r'Paris,\s+\d+\s+rue\s+.+'
```

**Examples:**
```python
standardize_address_paris("Paris, 19 rue Voltaire")
# → "Paris, 19 rue Voltaire" ✅

standardize_address_paris("Paris,19 rue Voltaire")
# → "Paris, 19 rue Voltaire" ✅ (added space)

standardize_address_paris("  Paris, 19 rue Voltaire  ")
# → "Paris, 19 rue Voltaire" ✅ (trimmed)

standardize_address_paris("Paris, 19 avenue Voltaire")
# → None ❌ (only "rue" accepted)

standardize_address_paris(None)
# → None
```

**Used By:**
- `clean_population_paris()`

---

### **4. `standardize_address_evry(address)`**

**Purpose:** Standardize Évry addresses to consistent format.

**Parameters:**
- `address` (str): Raw address string

**Returns:**
- `str`: Standardized address in format `"Evry-Courcouronnes, [N] [type] [street]"`
- `None`: If invalid or missing

**Format:** `"Evry-Courcouronnes, [number] [street_type] [street_name]"`

**Logic:**
```python
1. Handle NULL/empty → return None
2. Strip whitespace
3. Remove embedded postal codes (e.g., ", 91000,") from address string
4. Standardize city name to "Evry-Courcouronnes"
5. Normalize spacing around commas
6. Validate format (number + street type + name)
7. Return standardized address or None if invalid
```

**Accepted Street Types:**
```
rue | boulevard | bd | allée | allee | square | place | avenue | av
```

**Examples:**
```python
standardize_address_evry("Evry-Courcouronnes, 91000, 19 Boulevard Aguado")
# → "Evry-Courcouronnes, 19 Boulevard Aguado" ✅

standardize_address_evry("Evry, 312 ALLEE PABLO NERUDA")
# → "Evry-Courcouronnes, 312 ALLEE PABLO NERUDA" ✅

standardize_address_evry("Evry-Courcouronnes, 4 rue Voltaire")
# → "Evry-Courcouronnes, 4 rue Voltaire" ✅

standardize_address_evry("Incomplete")
# → None ❌ (missing number + street type)

standardize_address_evry(None)
# → None
```

**Used By:**
- `clean_population_evry()`

---

### **5. `standardize_csp_value(csp_value, return_id=False)`**

**Purpose:** Comprehensive CSP (socio-professional category) standardization.

**Parameters:**
- `csp_value` (str/int): Raw CSP value (numeric code or text description)
- `return_id` (bool): If `True`, return ID_CSP (1-7); if `False`, return full description

**Returns:**
- `int` (if `return_id=True`): ID_CSP (1-7)
- `str` (if `return_id=False`): Full CSP description
- `None`: If invalid and return_id=True

**Mapping Table:**

| Input Variations | ID_CSP | Description |
|------------------|--------|-------------|
| `1`, `"Agriculteur"`, `"Agriculteurs exploitants"` | 1 | Agriculteurs exploitants / agricultrices exploitantes |
| `2`, `"Artisan"`, `"Commerçant"`, `"Chef d'entreprise"` | 2 | Artisans / artisanes, commerçants / commerçantes et chefs / cheffes d'entreprise |
| `3`, `"Cadre"`, `"Cadres"`, `"Professions intellectuelles"` | 3 | Cadres et professions intellectuelles supérieures |
| `4`, `"Professions intermédiaires"`, `"Profession intermédiaire"` | 4 | Professions intermédiaires |
| `5`, `"Employé"`, `"Employés"`, `"Employée"`, `"Etudiant"` | 5 | Employés / employées |
| `6`, `"Ouvrier"`, `"Ouvriers"`, `"Ouvrière"` | 6 | Ouvriers / ouvrières |
| `"Retraité"`, `"Retraitée"`, `"Retraités"` | 7 | Retraités / retraitées (custom category) |

**Logic:**
```python
1. Handle NULL/NaN → return None
2. Try numeric conversion first (1-6 from Population_Evry)
3. If numeric match → return corresponding ID/description
4. Otherwise, convert to lowercase for text matching
5. Match against keywords (case-insensitive, plural/singular)
6. Handle special cases (students → Employés, retirees → category 7)
7. Return ID or description based on return_id parameter
8. If no match → return original value (for traceability)
```

**Examples:**
```python
# Numeric input (Population_Evry)
standardize_csp_value(3, return_id=True)      # → 3
standardize_csp_value(5, return_id=False)     # → "Employés / employées"

# Text input (Population_Paris)
standardize_csp_value("Cadre", return_id=True)            # → 3
standardize_csp_value("Employé", return_id=False)         # → "Employés / employées"
standardize_csp_value("Ouvriers", return_id=True)         # → 6
standardize_csp_value("Professions intermédiaires", return_id=True)  # → 4

# Special cases
standardize_csp_value("Etudiant", return_id=True)         # → 5 (mapped to Employés)
standardize_csp_value("Retraité", return_id=True)         # → 7 (custom category)

# Invalid input
standardize_csp_value("Unknown", return_id=True)          # → None
standardize_csp_value(None, return_id=True)               # → None
```

**Used By:**
- `clean_population_paris()`
- `clean_population_evry()`

---

### **6. `clean_consommation_evry(base_path)`**

**Purpose:** Clean Évry consumption data.

**Parameters:**
- `base_path` (str/Path): Project root directory

**Returns:**
- `DataFrame`: Cleaned consumption data

**Operations:**
```
1. Load input_data/Consommation_Evry.csv
2. Clean postal codes (fix 9100000 → 91000, 91000a → 91000, etc.)
3. Normalize consumption units (identify and convert Wh to kWh)
4. Impute missing NB_KW_Jour with column mean
5. Remove rows with missing critical fields (Code_Postal, N, Nom_Rue)
6. Remove duplicate addresses
7. Save to cleaned_data/Consommation_Evry_cleaned.csv
```

**Critical Fields:**
- `Code_Postal` (cannot be NULL)
- `N` (street number, cannot be NULL)
- `Nom_Rue` (street name, cannot be NULL)
- `NB_KW_Jour` (imputed if missing)

**Output Columns:**
```
ID_Adr, N, Nom_Rue, Code_Postal, NB_KW_Jour
```

---

### **7. `clean_consommation_paris(base_path)`**

**Purpose:** Clean Paris consumption data.

**Parameters:**
- `base_path` (str/Path): Project root directory

**Returns:**
- `DataFrame`: Cleaned consumption data

**Operations:**
```
1. Load input_data/Consommation_Paris.csv
2. Clean postal codes (standardize to 5 digits)
3. Normalize consumption units (Wh → kWh conversion)
4. Impute missing NB_KW_Jour with column mean
5. Remove rows with missing critical fields
6. Remove duplicate addresses
7. Save to cleaned_data/Consommation_Paris_cleaned.csv
```

**Critical Fields:**
- `Code_Postal` (cannot be NULL)
- `N` (street number, cannot be NULL)
- `Nom_Rue` (street name, cannot be NULL)
- `NB_KW_Jour` (imputed if missing)

**Output Columns:**
```
ID_Adr, N, Nom_Rue, Code_Postal, NB_KW_Jour
```

---

### **8. `clean_population_paris(base_path)`**

**Purpose:** Clean Paris population data.

**Parameters:**
- `base_path` (str/Path): Project root directory

**Returns:**
- `DataFrame`: Cleaned population data

**Operations:**
```
1. Load input_data/Population_Paris.csv
2. Standardize addresses (format validation)
3. Standardize CSP values → ID_CSP (foreign key)
4. Rename column: CSP → ID_CSP
5. Remove duplicate IDs (keep first)
6. Save to cleaned_data/Population_Paris_cleaned.csv
```

**Important:** Does NOT remove rows with NULL addresses (preserves data integrity)

**Output Columns:**
```
ID_Personne, Nom, Prénom, Adresse, ID_CSP
```

---

### **9. `clean_population_evry(base_path)`**

**Purpose:** Clean Évry population data.

**Parameters:**
- `base_path` (str/Path): Project root directory

**Returns:**
- `DataFrame`: Cleaned population data

**Operations:**
```
1. Load input_data/Population_Evry.csv
2. Map numeric CSP codes → ID_CSP (validate against CSP.csv)
3. Rename column: CSP → ID_CSP
4. Standardize addresses (remove embedded postal codes, format validation)
5. Safe standardization (keep original if standardization fails)
6. Remove duplicate IDs (keep first)
7. Save to cleaned_data/Population_Evry_cleaned.csv
```

**Important:** Preserves original address if standardization returns None (prevents data loss)

**Output Columns:**
```
ID_Personne, Nom, Prénom, Adresse, ID_CSP
```

---

### **10. `clean_csp_table(base_path)`**

**Purpose:** Clean CSP reference table and add custom category for retirees.

**Parameters:**
- `base_path` (str/Path): Project root directory

**Returns:**
- `DataFrame`: Cleaned CSP reference data

**Operations:**
```
1. Load input_data/CSP.csv
2. Standardize column name: Salair_Moyen → Salaire_Moyen
3. Convert salary columns to numeric (handle spaces like "16 800")
4. Impute missing Salaire_Moyen from (Salaire_Min + Salaire_Max) / 2
5. Add category 7 (Retraités) with averaged salary data from other categories
6. Remove duplicate ID_CSP (keep first)
7. Save to cleaned_data/CSP_cleaned.csv
```

**Why Add Category 7?**
- Raw data contains "Retraité" references in Population_Paris
- Official INSEE CSP categories only include 1-6
- Custom category ensures referential integrity (all ID_CSP values exist in CSP.csv)

**Output Columns:**
```
ID_CSP, Desc, Salaire_Moyen, Salaire_Min, Salaire_Max
```

**Categories:**
```
1 - Agriculteurs exploitants
2 - Artisans, commerçants, chefs d'entreprise
3 - Cadres et professions intellectuelles supérieures
4 - Professions intermédiaires
5 - Employés / employées
6 - Ouvriers / ouvrières
7 - Retraités / retraitées (ADDED)
```

---

### **11. `main()`**

**Purpose:** Execute full cleaning pipeline for all tables.

**Parameters:** None

**Returns:** None

**Operations:**
```
1. Determine base path (project root)
2. Print header
3. Clean all tables in sequence:
   - Consommation_Evry
   - Consommation_Paris
   - Population_Paris
   - Population_Evry
   - CSP reference table
4. Print completion message
```

**Entry Point:** Called when script executed as `__main__`

---

## 📏 Cleaning Rules

### **Rule 1: Postal Code Validation**

| City | Valid Postal Codes | Action |
|------|-------------------|--------|
| **Évry** | `91000` | Fix all variations (9100000, 91000a, 910000) → 91000 |
| **Paris** | `75001-75020` | Standardize to 5 digits |

**Rejection Criteria:**
- Less than 5 digits after extraction
- NULL or empty values

---

### **Rule 2: Consumption Unit Normalization**

**Threshold:** 1000

| Original Value | Interpretation | Normalized Value |
|----------------|----------------|------------------|
| `< 1000` | Already in kWh/day | Keep as-is |
| `≥ 1000` | Assume Wh/day | Divide by 1000 → kWh/day |
| `Negative` | Invalid | Set to NULL |

**Examples:**
```
1548.49 Wh  → 1.55 kWh
12.58 kWh   → 12.58 kWh (unchanged)
-5 kWh      → NULL (invalid)
```

---

### **Rule 3: Missing Value Imputation**

| Field Type | Strategy | Applied To |
|------------|----------|------------|
| **Consumption (NB_KW_Jour)** | ✅ Mean imputation | Both Consommation tables |
| **Addresses** | ❌ NO imputation | Both Population tables |
| **CSP Salary (Salaire_Moyen)** | ✅ (Min + Max) / 2 | CSP table |
| **IDs, Names** | ❌ Never impute | All tables |

**Rationale:**
- Numerical data: Statistically sound imputation
- Categorical data: NO fabrication (integrity over completeness)

---

### **Rule 4: Duplicate Handling**

| Table | Deduplication Key | Action |
|-------|------------------|--------|
| **Consommation_Evry** | `(N, Nom_Rue, Code_Postal)` | Keep first occurrence |
| **Consommation_Paris** | `(N, Nom_Rue, Code_Postal)` | Keep first occurrence |
| **Population_Evry** | `ID_Personne` | Keep first occurrence |
| **Population_Paris** | `ID_Personne` | Keep first occurrence |
| **CSP** | `ID_CSP` | Keep first occurrence |

---

### **Rule 5: Record Deletion Criteria**

**ONLY delete if:**
- Missing critical identifier (ID_Adr, ID_Personne, ID_CSP)
- Missing mandatory address components in CONSUMPTION tables (N, Nom_Rue, Code_Postal)
- Duplicate record (keep first)

**NEVER delete if:**
- Missing address in POPULATION tables (keep as NULL)
- Missing non-critical fields (impute or leave NULL)
- Invalid CSP reference (map to valid category or add new category)

---

## 📂 Input/Output Structure

### **Input Files (input_data/)**

```
input_data/
├── Consommation_Evry.csv      (12 rows, 5 columns)
│   └── ID_Adr, N, Nom_Rue, Code_Postal, NB_KW_Jour
│
├── Consommation_Paris.csv     (13 rows, 5 columns)
│   └── ID_Adr, N, Nom_Rue, Code_Postal, NB_KW_Jour
│
├── Population_Evry.csv        (12 rows, 5 columns)
│   └── ID_Personne, Nom, Prénom, Adresse, CSP
│
├── Population_Paris.csv       (12 rows, 5 columns)
│   └── ID_Personne, Nom, Prénom, Adresse, CSP
│
└── CSP.csv                    (6 rows, 5 columns)
    └── ID_CSP, Desc, Salair_Moyen, Salaire_Min, Salaire_Max
```

### **Output Files (cleaned_data/)**

```
cleaned_data/
├── Consommation_Evry_cleaned.csv      (12 rows, 5 columns)
│   └── ID_Adr, N, Nom_Rue, Code_Postal, NB_KW_Jour
│   ✅ All postal codes valid (91000)
│   ✅ All consumption values normalized (kWh/day)
│   ✅ Missing consumption imputed with mean (86.60 kWh)
│
├── Consommation_Paris_cleaned.csv     (13 rows, 5 columns)
│   └── ID_Adr, N, Nom_Rue, Code_Postal, NB_KW_Jour
│   ✅ All postal codes valid (75001-75020)
│   ✅ All consumption converted (Wh → kWh)
│   ✅ No missing values
│
├── Population_Evry_cleaned.csv        (12 rows, 5 columns)
│   └── ID_Personne, Nom, Prénom, Adresse, ID_CSP
│   ✅ CSP → ID_CSP (numeric foreign key)
│   ✅ Addresses standardized (postal codes removed)
│   ⚠️ 4 addresses still NULL (no fabrication)
│
├── Population_Paris_cleaned.csv       (12 rows, 5 columns)
│   └── ID_Personne, Nom, Prénom, Adresse, ID_CSP
│   ✅ CSP → ID_CSP (standardized from text)
│   ✅ All addresses standardized
│   ✅ 100% valid CSP references
│
└── CSP_cleaned.csv                    (7 rows, 5 columns)
    └── ID_CSP, Desc, Salaire_Moyen, Salaire_Min, Salaire_Max
    ✅ Salaire_Moyen imputed from Min/Max
    ✅ Category 7 (Retraités) added
    ✅ All salary values numeric
```

---

## 💡 Examples

### **Example 1: Cleaning Consumption Data**

**Input:** `Consommation_Evry.csv`
```csv
ID_Adr,N,Nom_Rue,Code_Postal,NB_KW_Jour
231901,19,BOULEVARD AGUADO,91000,12.58054795
232945,5,PLACE GEORGE WASHINGTON,91000,
236474,6,SQUARE GUTENBERG,9100000,7.444931507
235743,8,RUE PABLO PICASSO,91000a,4.026027397
```

**Output:** `Consommation_Evry_cleaned.csv`
```csv
ID_Adr,N,Nom_Rue,Code_Postal,NB_KW_Jour
231901,19,BOULEVARD AGUADO,91000,12.58
232945,5,PLACE GEORGE WASHINGTON,91000,86.60
236474,6,SQUARE GUTENBERG,91000,7.44
235743,8,RUE PABLO PICASSO,91000,4.03
```

**Changes:**
1. ✅ Postal code `9100000` → `91000`
2. ✅ Postal code `91000a` → `91000`
3. ✅ Missing `NB_KW_Jour` → imputed with mean (86.60)
4. ✅ Values rounded to 2 decimals

---

### **Example 2: Cleaning Population Data**

**Input:** `Population_Evry.csv`
```csv
ID_Personne,Nom,Prénom,Adresse,CSP
GauAic,Gauthier,Aicha,"Evry-Courcouronnes, 91000, 19 Boulevard Aguado",4
MouSéb,Moulin,Sébastien,,6
```

**Output:** `Population_Evry_cleaned.csv`
```csv
ID_Personne,Nom,Prénom,Adresse,ID_CSP
GauAic,Gauthier,Aicha,"Evry-Courcouronnes, 19 Boulevard Aguado",4
MouSéb,Moulin,Sébastien,,6
```

**Changes:**
1. ✅ Column renamed: `CSP` → `ID_CSP`
2. ✅ Address standardized (removed ", 91000,")
3. ✅ Missing address preserved as NULL (not fabricated)

---

### **Example 3: CSP Standardization**

**Input:** `Population_Paris.csv`
```csv
ID_Personne,Nom,Prénom,Adresse,CSP
DupMar,Dupont,Marie,"Paris, 19 rue Voltaire",Cadre
LefPie,Lefèvre,Pierre,"Paris, 8 rue Picasso",Employé
MorAhm,Moreau,Ahmed,"Paris, 4 rue Curie",Retraité
```

**Output:** `Population_Paris_cleaned.csv`
```csv
ID_Personne,Nom,Prénom,Adresse,ID_CSP
DupMar,Dupont,Marie,"Paris, 19 rue Voltaire",3
LefPie,Lefèvre,Pierre,"Paris, 8 rue Picasso",5
MorAhm,Moreau,Ahmed,"Paris, 4 rue Curie",7
```

**Changes:**
1. ✅ "Cadre" → `3` (Cadres et professions intellectuelles)
2. ✅ "Employé" → `5` (Employés)
3. ✅ "Retraité" → `7` (Custom category added to CSP.csv)

---

## 🔧 Troubleshooting

### **Issue 1: "FileNotFoundError: input_data/..."**

**Cause:** Script not run from correct directory or input files missing

**Solution:**
```bash
# Ensure you're in project root
cd "c:\Users\mohamed abi\Desktop\new QD data"

# Verify input files exist
ls input_data/

# Run script
python dags/scripts/clean_data.py
```

---

### **Issue 2: "ModuleNotFoundError: No module named 'pandas'"**

**Cause:** pandas not installed

**Solution:**
```bash
pip install pandas
# or
pip install -r requirements.txt
```

---

### **Issue 3: "ValueError: could not convert string to float"**

**Cause:** Unexpected data format in consumption or salary columns

**Solution:**
1. Check raw data for non-numeric values in `NB_KW_Jour` or `Salaire_*` columns
2. Script already handles most cases - if error persists, open issue with sample data

---

### **Issue 4: All addresses marked as invalid after cleaning**

**Cause:** Address format doesn't match validation regex

**Solution:**
1. Check address format in raw data
2. Ensure Paris addresses: `"Paris, [N] rue [street]"`
3. Ensure Évry addresses: `"Evry-Courcouronnes, [N] [type] [street]"`
4. Update regex in `standardize_address_*()` functions if needed

---

### **Issue 5: CSP references not found**

**Cause:** CSP values don't match mapping in `standardize_csp_value()`

**Solution:**
1. Check raw CSP values in Population_*.csv
2. Add new mappings to `standardize_csp_value()` function
3. Or add new category to CSP.csv

---

### **Issue 6: Cleaned data has fewer rows than raw**

**Expected Behavior:** Some rows removed due to:
- Duplicate addresses/IDs
- Missing critical fields (postal code, street number/name in CONSUMPTION tables)

**Check Log Output:**
```
✓ Rows: 12 → 11 (removed 1)
```

**If unexpected:** Review deletion criteria in cleaning functions

---

## 📊 Quality Metrics

### **Before Cleaning**
```
Consommation Évry:   58.33% invalid rate, 7 perfect records
Consommation Paris:  100% invalid rate, 0 perfect records
Population Évry:     95.24% completeness, 100% address issues
Population Paris:    ~15% address issues
CSP Table:           83.33% salary completeness
```

### **After Cleaning**
```
Consommation Évry:   0% invalid rate, 12 perfect records ✅
Consommation Paris:  0% invalid rate, 13 perfect records ✅
Population Évry:     95.24% completeness, 41.67% missing addresses (honest metric)
Population Paris:    100% completeness, 0% address issues ✅
CSP Table:           100% salary completeness, 7 categories ✅
```

---

## 🔗 Related Documentation

- **[DATA_CLEANING_STRATEGY.md](DATA_CLEANING_STRATEGY.md)** - Detailed explanation of cleaning decisions and trade-offs
- **[PIPELINE_README.md](PIPELINE_README.md)** - Full pipeline execution guide
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide for beginners
- **[DATA_QUALITY_METRICS.md](DATA_QUALITY_METRICS.md)** - Metrics calculation documentation

---

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [DATA_CLEANING_STRATEGY.md](DATA_CLEANING_STRATEGY.md) for design decisions
3. Inspect logs in terminal output for specific error details
4. Open an issue with sample data and error message

---

**Script Version:** 1.0  
**Last Updated:** November 5, 2025  
**Maintained By:** Data Quality Team
