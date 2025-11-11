# Validation Rules and Metric Names

## Updated Metric Naming Convention

All metrics now follow the exact naming pattern specified:

### Consommation Evry - Key Metrics

**`pct_cons_evry_NB_Kw_invalid`**
- **Definition**: Percentage of rows where `(NB_KW_Jour < 0 OR NB_KW_Jour > 1000 OR NB_KW_Jour = null)`
- **Current Value**: 41.67%
- **Validation Rule**: `0 ≤ NB_KW_Jour ≤ 1000`

**`pct_cons_evry_cp_invalid`**
- **Definition**: Percentage of invalid postal codes
- **Current Value**: 25.0%
- **Validation Rule**: Must match `[0-9]{5}` (exactly 5 digits)

**`pct_cons_evry_add_valid`**
- **Definition**: Percentage of valid addresses (N and Nom_Rue present)
- **Current Value**: 100.0%

---

### Consommation Paris - Key Metrics

**`pct_cons_paris_NB_Kw_invalid`**
- **Definition**: Percentage of rows where `(NB_KW_Jour < 0 OR NB_KW_Jour > 1000 OR NB_KW_Jour = null)`
- **Current Value**: 100.0% ⚠️ All values are > 1000 (realistic consumption data)
- **Validation Rule**: `0 ≤ NB_KW_Jour ≤ 1000`

**`pct_cons_paris_cp_invalid`**
- **Definition**: Percentage of invalid postal codes
- **Current Value**: 7.69%
- **Validation Rule**: Must match `[0-9]{5}` (exactly 5 digits)

**`pct_cons_paris_add_valid`**
- **Definition**: Percentage of valid addresses
- **Current Value**: 100.0%

---

### Population Paris - Key Metrics

**`pct_pop_paris_add_invalid`**
- **Definition**: Percentage of rows where Address doesn't verify regex `Paris,\s+\d+\s+rue\s+.+`
- **Current Value**: 8.33% (1 row out of 12)
- **Validation Rule**: Address must match pattern `"Paris, [number] rue [street name]"`
- **Example Valid**: `"Paris, 20 rue Arthur Groussier"`
- **Example Invalid**: `"Paris, 17 rue Belhomme"` (missing space after comma)

**`pct_pop_paris_csp_invalid`**
- **Definition**: Percentage of rows where CSP is not in the valid list of 52 values
- **Current Value**: 0.0%
- **Validation Rule**: CSP must be one of 52 exact values (case-insensitive)
- **Valid Values Include**: 
  - Agriculteur, Agriculteurs, Agriculteurs exploitants, Agricultrice...
  - Artisan, Artisane, Artisans, Commerçant, Commerçante...
  - Cadre, Cadres, Cadres et professions intellectuelles supérieures...
  - Employé, Employée, Employés, Ouvrier, Ouvrière, Ouvriers...
  - Professions intermédiaires, Retraité, Retraitée, Etudiant, Étudiante...
  - (52 total variations)

---

### Population Evry - Key Metrics

**`pct_pop_evry_add_invalid`**
- **Definition**: Percentage of rows where Address doesn't verify regex `Evry,\s+\d+\s+rue\s+.+`
- **Current Value**: 100.0% ⚠️ All addresses need format correction
- **Validation Rule**: Address must match pattern `"Evry, [number] rue [street name]"`
- **Note**: Also accepts `"Evry-Courcouronnes"` and other street types (boulevard, allée, square, place)
- **Example Valid**: `"Evry-Courcouronnes, 19 boulevard Aguado"`
- **Example Invalid**: `"Evry-Courcouronnes, 91000, 19 Boulevard Aguado"` (includes postal code)

**`pct_pop_evry_csp_invalid`**
- **Definition**: Percentage of rows where CSP is not in the valid list
- **Current Value**: 100.0% ⚠️ CSP values are numeric (3, 4, 5, 6) instead of text
- **Validation Rule**: Same 52-value list as Population Paris

---

## CSP Table - Key Metrics

**`pct_csp_salary_invalid`**
- **Definition**: Percentage of salary values outside range [0, 1,000,000]
- **Current Value**: 0.0%
- **Validation Rule**: `0 ≤ Salair_Moyen ≤ 1,000,000`

---

## Complete CSP Valid Values List (52 values)

The validation checks for these exact values (case-insensitive):

```
1. Agriculteur
2. Agriculteurs
3. Agriculteurs exploitants
4. Agriculteurs exploitants / algricultrices exploitantes
5. Agricultrice
6. Agricultrices
7. Algricultrices exploitantes
8. Artisan
9. Artisan / Commerçant
10. Artisane
11. Artisanes
12. Artisans
13. Artisans / artisanes, commerçants / commerçantes et chefs / cheffes d'entreprise
14. Autres personnes sans activité professionnelle
15. Cadre
16. Cadre supérieur
17. Cadres
18. Cadres et professions intellectuelles supérieures
19. Cadres supérieurs
20. Chef d'entreprise
21. Cheffe d'entreprise
22. Cheffes d'entreprise
23. Chefs d'entreprise
24. Commerçant
25. Commerçant / Artisan
26. Commerçante
27. Commerçantes
28. Commerçants
29. Employe
30. Employé
31. Employée
32. Employées
33. Employés
34. Employés / employées
35. Etudiant
36. Etudiante
37. Ouvrier
38. Ouvriers
39. Ouvriers / ouvrières
40. Ouvrière
41. Ouvrières
42. Profession intermédiaire
43. Professions intellectuelles supérieures
44. Professions intermediaires
45. Professions intermédiaires
46. Retraité
47. Retraitée
48. Retraitées
49. Retraités
50. Sans activité professionnelle
51. cadres et professions intellectuelles supérieures
52. Étudiante
53. Étudiants
```

---

## All Metric Names (38 total)

### Consommation Evry (10)
- `total_rows_cons_evry`
- `valid_rows_cons_evry`
- `invalid_rate_cons_evry`
- `pct_cons_evry_cp_invalid`
- `pct_cons_evry_add_valid`
- `pct_cons_evry_NB_Kw_invalid` ⭐
- `completeness_cons_evry`
- `tuples_below_50_cons_evry`
- `tuples_50_to_100_cons_evry`
- `tuples_100_cons_evry`

### Consommation Paris (10)
- `total_rows_cons_paris`
- `valid_rows_cons_paris`
- `invalid_rate_cons_paris`
- `pct_cons_paris_cp_invalid`
- `pct_cons_paris_add_valid`
- `pct_cons_paris_NB_Kw_invalid` ⭐
- `completeness_cons_paris`
- `tuples_below_50_cons_paris`
- `tuples_50_to_100_cons_paris`
- `tuples_100_cons_paris`

### Population Paris (7)
- `total_rows_pop_paris`
- `pct_pop_paris_add_invalid` 
- `pct_pop_paris_csp_invalid` 
- `completeness_pop_paris`
- `tuples_below_50_pop_paris`
- `tuples_50_to_100_pop_paris`
- `tuples_100_pop_paris`

### Population Evry (7)
- `total_rows_pop_evry`
- `pct_pop_evry_add_invalid` ⭐
- `pct_pop_evry_csp_invalid` ⭐
- `completeness_pop_evry`
- `tuples_below_50_pop_evry`
- `tuples_50_to_100_pop_evry`
- `tuples_100_pop_evry`

### CSP (4)
- `total_rows_csp`
- `pct_csp_salary_invalid` ⭐
- `completeness_salaire_csp`
- `completeness_csp`

⭐ = Key metrics as specified in requirements

---

## Sample Metadata Output

```csv
total_rows_cons_evry;valid_rows_cons_evry;invalid_rate_cons_evry;pct_cons_evry_cp_invalid;pct_cons_evry_add_valid;pct_cons_evry_NB_Kw_invalid;completeness_cons_evry;tuples_below_50_cons_evry;tuples_50_to_100_cons_evry;tuples_100_cons_evry;total_rows_cons_paris;valid_rows_cons_paris;invalid_rate_cons_paris;pct_cons_paris_cp_invalid;pct_cons_paris_add_valid;pct_cons_paris_NB_Kw_invalid;completeness_cons_paris;tuples_below_50_cons_paris;tuples_50_to_100_cons_paris;tuples_100_cons_paris;total_rows_pop_paris;pct_pop_paris_add_invalid;pct_pop_paris_csp_invalid;completeness_pop_paris;tuples_below_50_pop_paris;tuples_50_to_100_pop_paris;tuples_100_pop_paris;total_rows_pop_evry;pct_pop_evry_add_invalid;pct_pop_evry_csp_invalid;completeness_pop_evry;tuples_below_50_pop_evry;tuples_50_to_100_pop_evry;tuples_100_pop_evry;total_rows_csp;pct_csp_salary_invalid;completeness_salaire_csp;completeness_csp
12;5;58.33;25.0;100.0;41.67;94.79;0;5;7;13;0;100.0;7.69;100.0;100.0;100.0;0;0;13;12;8.33;0.0;100.0;0;0;12;12;100.0;100.0;95.24;0;4;8;6;0.0;83.33;96.67
```

---

## Key Findings

### ✅ Good Quality
- **Population Paris**: 0% invalid CSP (all match the 52-value list)
- **Consommation Evry**: 100% valid addresses
- **CSP Table**: 0% invalid salaries (all within range)

### ⚠️ Needs Attention
- **Consommation Paris**: 100% invalid consumption (values > 1000 kW/day - may need threshold adjustment)
- **Consommation Evry**: 41.67% invalid consumption, 25% invalid postal codes
- **Population Paris**: 8.33% invalid address format (1 row)

### ❌ Critical Issues
- **Population Evry**: 
  - 100% invalid address format (all need reformatting)
  - 100% invalid CSP (numeric codes instead of text descriptions)
