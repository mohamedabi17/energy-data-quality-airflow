# Quick Reference: Data Quality Metrics

## 📊 Metrics Overview

| Table | Total Metrics | Key Focus Areas |
|-------|---------------|-----------------|
| **Consommation_Evry** | 10 | Postal codes, consumption values, completeness |
| **Consommation_Paris** | 10 | Postal codes, consumption values, completeness |
| **Population_Paris** | 7 | Address format, CSP validation, completeness |
| **Population_Evry** | 7 | Address format, CSP validation, completeness |
| **CSP** | 4 | Salary validation, completeness |
| **TOTAL** | **38** | Comprehensive data quality assessment |

---

## 🎯 Current Data Quality Status

### Consommation_Evry
```
✅ Good: 100% valid addresses
⚠️  Needs attention: 58.33% invalid rows overall
⚠️  Needs attention: 25% invalid postal codes
⚠️  Needs attention: 41.67% invalid consumption values
✅ Good: 94.79% completeness
```

### Consommation_Paris
```
✅ Excellent: 92.31% valid rows
✅ Excellent: 100% valid addresses
⚠️  Minor issue: 7.69% invalid postal codes
✅ Perfect: 100% valid consumption
✅ Perfect: 100% completeness
```

### Population_Paris
```
✅ Perfect: 100% valid address formats
⚠️  Minor issue: 8.33% invalid CSP values (1 row)
✅ Perfect: 100% completeness
```

### Population_Evry
```
❌ Critical: 100% invalid address formats
   → All addresses need format correction to "Ville, Numéro NomRue"
✅ Good: 0% invalid CSP
⚠️  Good: 95.24% completeness (4 rows have missing fields)
```

### CSP Table
```
✅ Perfect: 100% valid salaries
✅ Good: 83.33% salary completeness (1 missing, auto-imputed)
✅ Excellent: 96.67% overall completeness
```

---

## 🔍 Priority Actions

### HIGH PRIORITY
1. **Population_Evry Addresses**: Fix address format for all 12 rows
   - Current format varies
   - Required format: `"Evry-Courcouronnes, Numéro rue"`
   - Example: `"Evry-Courcouronnes, 19 Boulevard Aguado"`

2. **Consommation_Evry Data Quality**: Improve from 41.67% to >90%
   - Fix 3 invalid postal codes
   - Fix 5 invalid consumption values (empty or non-numeric)

### MEDIUM PRIORITY
3. **Consommation_Paris**: Fix 1 invalid postal code (7.69%)

4. **Population_Paris**: Fix 1 invalid CSP value (8.33%)

### LOW PRIORITY
5. **Completeness**: Monitor the 5 rows in Consommation_Evry with partial data
6. **CSP Table**: Already handled via automatic imputation

---

## 📈 Metrics Categories

### 1️⃣ Conformité Metrics (Format Validation)
- Invalid postal codes percentage
- Invalid addresses percentage  
- Invalid consumption values percentage
- Invalid CSP values percentage
- Invalid salary values percentage

### 2️⃣ Complétude Metrics (Completeness)
- Relation completeness (table level)
- Attribute completeness (column level)
- Tuple completeness distribution:
  - Tuples < 50%: Should be excluded
  - Tuples 50-100%: Need imputation
  - Tuples 100%: Valid

### 3️⃣ Overall Quality Metrics
- Total rows
- Valid rows (all validations pass)
- Invalid rate (%)

---

## 🚀 Running the Metrics

### Quick Test (No Airflow):
```powershell
cd "c:\Users\mohamed abi\Desktop\new QD data"
python dags\scripts\compute_metrics.py
```

### Production (With Airflow):
```powershell
# Terminal 1: Start webserver
airflow webserver --port 8080

# Terminal 2: Start scheduler  
airflow scheduler

# Browser: http://localhost:8080
# Enable and trigger: data_quality_metrics DAG
```

---

## 📁 Output Location

**Metadata file**: `metadata\metadata_qd.csv`

**Format**: Semicolon-separated (`;`)

**Columns**: 38 metrics (see DATA_QUALITY_METRICS.md for full list)

---

## 🔧 Customization

To modify validation rules, edit `dags\scripts\compute_metrics.py`:

- **Postal code pattern**: Line ~13 (`is_valid_postal_code`)
- **Address format**: Line ~32 (`is_valid_address_format`)
- **Consumption range**: Line ~65 (`is_valid_consumption`)
- **CSP reference list**: Line ~357 (`get_csp_reference_list`)
- **Salary range**: Line ~93 (`is_valid_salary`)

---

## 📚 Documentation

- **Full metrics list**: `DATA_QUALITY_METRICS.md`
- **Setup guide**: `README.md`
- **This file**: Quick reference and current status
