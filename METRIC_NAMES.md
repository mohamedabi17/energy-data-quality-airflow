# Updated Metric Names - Final Format

## Naming Convention: `pct_column_invalid_table_name`

All metrics now follow the standardized pattern where the column/attribute being validated comes first, followed by `invalid`, then the table name.

---

## ✅ Updated Metric Names

### Consommation Evry
- `pct_CP_invalid_cons_evry` - Percentage of invalid postal codes
- `pct_address_valid_cons_evry` - Percentage of valid addresses
- `pct_NB_KW_Jour_invalid_cons_evry` - Percentage of invalid consumption values

### Consommation Paris
- `pct_CP_invalid_cons_paris` - Percentage of invalid postal codes
- `pct_address_valid_cons_paris` - Percentage of valid addresses
- `pct_NB_KW_Jour_invalid_cons_paris` - Percentage of invalid consumption values

### Population Paris
- `pct_address_invalid_pop_paris` - Percentage of invalid addresses (regex validation)
- `pct_CSP_invalid_pop_paris` - Percentage of invalid CSP values

### Population Evry
- `pct_address_invalid_pop_evry` - Percentage of invalid addresses (regex validation)
- `pct_CSP_invalid_pop_evry` - Percentage of invalid CSP values

### CSP Table
- `pct_salary_invalid_csp` - Percentage of invalid salary values

---

## Complete Metadata Column Headers

```
total_rows_cons_evry
valid_rows_cons_evry
invalid_rate_cons_evry
pct_CP_invalid_cons_evry
pct_address_valid_cons_evry
pct_NB_KW_Jour_invalid_cons_evry
completeness_cons_evry
tuples_below_50_cons_evry
tuples_50_to_100_cons_evry
tuples_100_cons_evry
total_rows_cons_paris
valid_rows_cons_paris
invalid_rate_cons_paris
pct_CP_invalid_cons_paris
pct_address_valid_cons_paris
pct_NB_KW_Jour_invalid_cons_paris
completeness_cons_paris
tuples_below_50_cons_paris
tuples_50_to_100_cons_paris
tuples_100_cons_paris
total_rows_pop_paris
pct_address_invalid_pop_paris
pct_CSP_invalid_pop_paris
completeness_pop_paris
tuples_below_50_pop_paris
tuples_50_to_100_pop_paris
tuples_100_pop_paris
total_rows_pop_evry
pct_address_invalid_pop_evry
pct_CSP_invalid_pop_evry
completeness_pop_evry
tuples_below_50_pop_evry
tuples_50_to_100_pop_evry
tuples_100_pop_evry
total_rows_csp
pct_salary_invalid_csp
completeness_salaire_csp
completeness_csp
```

---

## Sample Values (Current Data)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| `pct_CP_invalid_cons_evry` | 25.0 | 25% of postal codes are invalid in Evry consumption |
| `pct_CP_invalid_cons_paris` | 7.69 | 7.69% of postal codes are invalid in Paris consumption |
| `pct_NB_KW_Jour_invalid_cons_evry` | 41.67 | 41.67% of consumption values are invalid in Evry |
| `pct_NB_KW_Jour_invalid_cons_paris` | 100.0 | 100% of consumption values are invalid in Paris (>1000) |
| `pct_address_invalid_pop_paris` | 8.33 | 8.33% of addresses don't match Paris regex pattern |
| `pct_address_invalid_pop_evry` | 100.0 | 100% of addresses don't match Evry regex pattern |
| `pct_CSP_invalid_pop_paris` | 0.0 | All CSP values are valid in Paris population |
| `pct_CSP_invalid_pop_evry` | 100.0 | All CSP values are invalid in Evry (numeric codes) |
| `pct_salary_invalid_csp` | 0.0 | All salaries are valid in CSP table |

---

## Key Examples

✅ **Correct Format Examples:**
- `pct_CP_invalid_cons_evry` ← Postal Code validation for Evry Consumption
- `pct_address_invalid_pop_paris` ← Address validation for Paris Population
- `pct_CSP_invalid_pop_paris` ← CSP validation for Paris Population
- `pct_NB_KW_Jour_invalid_cons_paris` ← Consumption validation for Paris
- `pct_salary_invalid_csp` ← Salary validation for CSP table

---

## Metadata File Location

**Path**: `metadata\metadata_qd.csv`

**Format**: Semicolon-separated values (`;`)

**Structure**: 
- Header row with 38 column names
- Data row with computed metric values
