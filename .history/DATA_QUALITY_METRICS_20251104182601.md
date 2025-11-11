# Data Quality Metrics Documentation

This document describes all the data quality metrics computed by the Airflow DAG.

## Overview

The system computes **38 comprehensive metrics** across 5 tables:
- Consommation_Evry
- Consommation_Paris
- Population_Paris
- Population_Evry
- CSP

## Metrics Categories

### 1. Conformité (Conformity)
Validates that data respects defined formats and constraints.

### 2. Complétude (Completeness)
Measures the percentage of non-null values.

### 3. Distribution de Complétude des Tuples
Categorizes rows by completeness level.

---

## Detailed Metrics by Table

### Consommation_Evry (10 metrics)

| Metric | Description | Validation Rule |
|--------|-------------|-----------------|
| `total_rows_Cons_Evry` | Total number of rows | Count |
| `valid_rows_Cons_Evry` | Rows with all valid fields | All validations pass |
| `invalid_rate_Cons_Evry` | % of invalid rows | (total - valid) / total × 100 |
| `pct_invalid_CP_Cons_Evry` | % of invalid postal codes | Must match `[0-9]{5}` |
| `pct_valid_Adresse_Cons_Evry` | % of valid addresses | Both N and Nom_Rue non-empty |
| `pct_invalid_Conso_Evry` | % of invalid consumption | Must be numeric and ≥ 0 |
| `completeness_Cons_Evry` | Table completeness % | (non-null cells / total cells) × 100 |
| `tuples_below_50_Cons_Evry` | Rows with < 50% fields filled | Count rows with completeness < 50% |
| `tuples_50_to_100_Cons_Evry` | Rows with 50-99% fields filled | Count rows with 50% ≤ completeness < 100% |
| `tuples_100_Cons_Evry` | Rows with 100% fields filled | Count rows with completeness = 100% |

**Validation Rules:**
- **Code_Postal**: Must contain exactly 5 digits (`[0-9]{5}`)
- **NB_KW_Jour**: Must be numeric and ≥ 0
- **Adresse**: Both street number (N) and street name (Nom_Rue) must be non-empty

---

### Consommation_Paris (10 metrics)

| Metric | Description | Validation Rule |
|--------|-------------|-----------------|
| `total_rows_Cons_Paris` | Total number of rows | Count |
| `valid_rows_Cons_Paris` | Rows with all valid fields | All validations pass |
| `invalid_rate_Cons_Paris` | % of invalid rows | (total - valid) / total × 100 |
| `pct_invalid_CP_Cons_Paris` | % of invalid postal codes | Must match `[0-9]{5}` |
| `pct_valid_Adresse_Cons_Paris` | % of valid addresses | Both N and Nom_Rue non-empty |
| `pct_invalid_Conso_Paris` | % of invalid consumption | Must be numeric and ≥ 0 |
| `completeness_Cons_Paris` | Table completeness % | (non-null cells / total cells) × 100 |
| `tuples_below_50_Cons_Paris` | Rows with < 50% fields filled | Count rows with completeness < 50% |
| `tuples_50_to_100_Cons_Paris` | Rows with 50-99% fields filled | Count rows with 50% ≤ completeness < 100% |
| `tuples_100_Cons_Paris` | Rows with 100% fields filled | Count rows with completeness = 100% |

**Validation Rules:** Same as Consommation_Evry

---

### Population_Paris (7 metrics)

| Metric | Description | Validation Rule |
|--------|-------------|-----------------|
| `total_rows_Pop_Paris` | Total number of rows | Count |
| `pct_invalid_address_Pop_Paris` | % of addresses not respecting format | Must match "Ville, Numéro NomRue" |
| `pct_invalid_CSP_Pop_Paris` | % of CSP values not in reference list | Must belong to predefined CSP list |
| `completeness_Pop_Paris` | Table completeness % | (non-null cells / total cells) × 100 |
| `tuples_below_50_Pop_Paris` | Rows with < 50% fields filled | Count rows with completeness < 50% |
| `tuples_50_to_100_Pop_Paris` | Rows with 50-99% fields filled | Count rows with 50% ≤ completeness < 100% |
| `tuples_100_Pop_Paris` | Rows with 100% fields filled | Count rows with completeness = 100% |

**Validation Rules:**
- **Adresse**: Must respect structured format: `"Ville, Numéro NomRue"`
  - Example: `"Paris, 20 rue Arthur Groussier"`
  - Must contain comma separator
  - Must have city name before comma
  - Must have number and street name after comma
- **CSP**: Must belong to list: Agriculteurs, Artisans, Commerçants, Cadres, Professions intermédiaires, Employés, Ouvriers, etc.

---

### Population_Evry (7 metrics)

| Metric | Description | Validation Rule |
|--------|-------------|-----------------|
| `total_rows_Pop_Evry` | Total number of rows | Count |
| `pct_invalid_address_Pop_Evry` | % of addresses not respecting format | Must match "Ville, Numéro NomRue" |
| `pct_invalid_CSP_Pop_Evry` | % of CSP values not in reference list | Must belong to predefined CSP list |
| `completeness_Pop_Evry` | Table completeness % | (non-null cells / total cells) × 100 |
| `tuples_below_50_Pop_Evry` | Rows with < 50% fields filled | Count rows with completeness < 50% |
| `tuples_50_to_100_Pop_Evry` | Rows with 50-99% fields filled | Count rows with 50% ≤ completeness < 100% |
| `tuples_100_Pop_Evry` | Rows with 100% fields filled | Count rows with completeness = 100% |

**Validation Rules:** Same as Population_Paris

---

### CSP (4 metrics)

| Metric | Description | Validation Rule |
|--------|-------------|-----------------|
| `total_rows_CSP` | Total number of rows | Count |
| `pct_invalid_salary_CSP` | % of salary values out of range | Must be numeric and 0 ≤ value ≤ 1,000,000 |
| `completeness_salaire_CSP` | % of non-null salaries | COUNT(Salaire_Moyen) / COUNT(*) × 100 |
| `completeness_CSP` | Table completeness % | (non-null cells / total cells) × 100 |

**Validation Rules:**
- **Salair_Moyen**: 
  - Must be numeric
  - Must be in range: `0 ≤ Salaire_Moyen ≤ 1,000,000`
  - If missing, imputed with: `(Salaire_Min + Salaire_Max) / 2`

---

## Tuple Completeness Categories

Based on the completeness rules:

| Category | Condition | Action |
|----------|-----------|--------|
| **Tuples < 50%** | Completeness < 50% | Should be excluded (tFilterRow) |
| **Tuples 50-100%** | 50% ≤ Completeness < 100% | Requires imputation (tMap/tDenormalize) |
| **Tuples 100%** | Completeness = 100% | Valid, no action needed |

---

## Metadata File Format

The metadata file (`metadata/metadata_qd.csv`) uses **semicolon (;) separators**.

### Sample Output:
```
total_rows_Cons_Evry;valid_rows_Cons_Evry;invalid_rate_Cons_Evry;...
12;5;58.33;25.0;100.0;41.67;94.79;0;5;7;13;12;7.69;...
```

---

## Example Results Interpretation

### Consommation_Evry Results:
- **Total rows**: 12
- **Valid rows**: 5 (41.67% valid)
- **Invalid rate**: 58.33%
- **Invalid postal codes**: 25% (3 rows)
- **Invalid consumption**: 41.67% (5 rows)
- **Completeness**: 94.79%
- **Tuple distribution**: 7 complete (100%), 5 partial (50-100%), 0 low (<50%)

### Population_Paris Results:
- **Total rows**: 12
- **Invalid addresses**: 0% (all follow format)
- **Invalid CSP**: 8.33% (1 row)
- **Completeness**: 100%

### CSP Table Results:
- **Total rows**: 6
- **Invalid salaries**: 0%
- **Salary completeness**: 83.33% (1 missing, imputed)
- **Overall completeness**: 96.67%

---

## Technical Implementation

### Technologies Used:
- **Python 3.x**
- **pandas**: Data manipulation
- **re (regex)**: Pattern validation
- **Apache Airflow**: Workflow orchestration

### Validation Functions:
- `is_valid_postal_code()`: Regex `[0-9]{5}`
- `is_valid_address_format()`: Structured format check
- `is_valid_consumption()`: Numeric and ≥ 0
- `is_valid_csp()`: List membership check
- `is_valid_salary()`: Range check [0, 1,000,000]
- `calculate_tuple_completeness()`: Row-level completeness
- `calculate_relation_completeness()`: Table-level completeness

---

## Running the Metrics

### Standalone:
```powershell
python dags\scripts\compute_metrics.py
```

### Via Airflow:
1. Start Airflow scheduler and webserver
2. Navigate to http://localhost:8080
3. Enable and trigger `data_quality_metrics` DAG

---

## Output Files

- **Metadata file**: `metadata/metadata_qd.csv`
- **Format**: Semicolon-separated values
- **Encoding**: UTF-8
- **Structure**: Header row + values row

---

## References

### Data Quality Dimensions:
1. **Conformité**: Data respects defined formats
2. **Complétude**: Data has no missing values
3. **Cohérence**: Data is consistent across sources
4. **Précision**: Data represents reality accurately
5. **Unicité**: No duplicates exist

This implementation focuses on **Conformité** and **Complétude**.
