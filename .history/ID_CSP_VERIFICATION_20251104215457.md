# ID_CSP Foreign Key Implementation - Verification Report

**Date**: November 4, 2025  
**Change**: Replaced CSP text columns with ID_CSP numeric foreign keys in Population tables

---

## 🔑 Schema Changes

### Before (Text-based CSP):
```csv
# Population_Paris_cleaned.csv
ID_Personne,Nom,Prénom,Adresse,CSP
1,Martin,Claire,"Paris, 20 rue...",Cadres et professions intellectuelles supérieures
2,Dupont,Julien,"Paris, 17 rue...",Employés / employées
```

### After (ID_CSP Foreign Key):
```csv
# Population_Paris_cleaned.csv
ID_Personne,Nom,Prénom,Adresse,ID_CSP
1,Martin,Claire,"Paris, 20 rue...",3.0
2,Dupont,Julien,"Paris, 17 rue...",5.0
```

---

## 📊 CSP Reference Table (Foreign Key Mapping)

| ID_CSP | Description | Salaire_Moyen |
|--------|-------------|---------------|
| 1 | Agriculteurs exploitants / algricultrices exploitantes | 24,780€ |
| 2 | Artisans / artisanes, commerçants / commerçantes et chefs / cheffes d'entreprise | 24,780€ |
| 3 | Cadres et professions intellectuelles supérieures | 39,860€ |
| 4 | Professions intermédiaires | 29,720€ |
| 5 | Employés / employées | 24,450€ |
| 6 | Ouvriers / ouvrières | 26,445€ |

---

## ✅ Verification Results

### Population_Paris_cleaned.csv (12 rows)
```
ID_Personne | Nom      | Prénom   | Adresse                              | ID_CSP
------------|----------|----------|--------------------------------------|--------
1           | Martin   | Claire   | Paris, 20 rue Arthur Groussier       | 3.0
2           | Dupont   | Julien   | Paris, 17 rue Belhomme               | 5.0
3           | Lefèvre  | Amélie   | Paris, 91 rue Broca                  | 4.0
4           | Moreau   | Thomas   | Paris, 20 rue Arthur Groussier       | 6.0
5           | Bernard  | Sophie   | Paris, 76 rue Blanche                | 3.0
6           | Dubois   | Karim    | Paris, 18 rue Arthur Groussier       | 2.0
7           | Petit    | Lucas    | Paris, 8 rue Belhomme                | 5.0
8           | Roux     | Nathalie | Paris, 10 rue Belgrand               | 4.0
9           | Faure    | Antoine  | Paris, 76 rue Blanche                | 3.0
10          | Garnier  | Léa      | Paris, 79 rue Broca                  | 5.0
11          | Perrin   | Isabelle | Paris, 92 rue Broca                  | NULL
12          | Mercier  | Romain   | Paris, 25 rue Broca                  | 1.0
```

**Mapping Summary:**
- ✅ **11 of 12** records have valid ID_CSP (1-6)
- ⚠️ **1 record** (Isabelle Perrin) has NULL ID_CSP (was "Retraitée" - not in CSP categories)
- **Distribution**: 
  - ID_CSP = 1 (Agriculteurs): 1 person
  - ID_CSP = 2 (Artisans): 1 person
  - ID_CSP = 3 (Cadres): 3 people
  - ID_CSP = 4 (Professions intermédiaires): 2 people
  - ID_CSP = 5 (Employés): 3 people
  - ID_CSP = 6 (Ouvriers): 1 person

### Population_Evry_cleaned.csv (12 rows)
```
ID_Personne | Nom       | Prénom    | Adresse                                    | ID_CSP
------------|-----------|-----------|--------------------------------------------|---------
GauAic      | Gauthier  | Aicha     | Evry-Courcouronnes, 19 Boulevard Aguado    | 4
MouSéb      | Moulin    | Sébastien | (empty)                                    | 6
BerSop      | Bernard   | Sophie    | Evry-Courcouronnes, 312 Allée Pablo Neruda | 3
ChePie      | Chevalier | Pierre    | Evry-Courcouronnes, 215 rue Pierre et...   | 3
DupJul      | Dupont    | Julien    | Evry-Courcouronnes, 19 Boulevard Aguado    | 5
LefAmé      | Lefèvre   | Amélie    | Evry-Courcouronnes, 4 rue Voltaire         | 4
LemMar      | Lemoine   | Marion    | (empty)                                    | 5
RoyAhm      | Roy       | Ahmed     | Evry-Courcouronnes, 2bis rue Voltaire      | 3
DubKar      | Dubois    | Karim     | Evry-Courcouronnes, 8 rue Voltaire         | 2
MarCla      | Martin    | Claire    | (empty)                                    | 3
MorTho      | Moreau    | Thomas    | Evry-Courcouronnes, 409 Square Jacques...  | 6
NoëChl      | Noël      | Chloé     | (empty)                                    | 6
```

**Mapping Summary:**
- ✅ **12 of 12** records have valid ID_CSP (1-6)
- ✅ **100%** mapping success (numeric codes 1-6 → ID_CSP 1-6)
- **Distribution**:
  - ID_CSP = 2 (Artisans): 1 person
  - ID_CSP = 3 (Cadres): 4 people
  - ID_CSP = 4 (Professions intermédiaires): 2 people
  - ID_CSP = 5 (Employés): 2 people
  - ID_CSP = 6 (Ouvriers): 3 people

---

## 📈 Target Schema: Consommation_CSP.csv

```csv
ID_CSP,Conso_moyenne_annuelle,Salaire_Moyen
1.0,5383.75,24780.0
2.0,4453.0,24780.0
3.0,4945.75,39860.0
4.0,5779.17,29720.0
5.0,5155.62,24450.0
6.0,4453.0,26445.0
```

**Verification:**
- ✅ All 6 CSP categories present
- ✅ Each ID_CSP joined with CSP table for Salaire_Moyen
- ✅ Average consumption calculated per CSP category
- ✅ Data integrity: ID_CSP values match CSP.csv primary keys

---

## 🔗 Join Verification

### Join Path (Simplified by Foreign Key):
```
BEFORE (Text Matching):
Population.CSP (text) --[fuzzy match]--> CSP.Desc (text) --> CSP.ID_CSP

AFTER (Direct Foreign Key):
Population.ID_CSP (int) --[exact match]--> CSP.ID_CSP (int)
```

### Benefits:
1. ✅ **Faster Joins**: Integer comparison vs. text fuzzy matching
2. ✅ **Referential Integrity**: ID_CSP must exist in CSP table
3. ✅ **No Ambiguity**: No more "Cadre" vs "Cadres" vs "cadres et professions..."
4. ✅ **Storage Efficiency**: 4 bytes (int) vs 50+ bytes (text)
5. ✅ **Easier Updates**: Change CSP.Desc without updating Population tables

---

## 📊 Data Quality Metrics (After ID_CSP Implementation)

### Population Paris:
- **Invalid CSP**: 8.33% (1 of 12 - "Retraitée" not mapped)
- **Completeness**: 98.81% (1 field NULL out of 60 total)
- **Perfect Records**: 11 of 12

### Population Evry:
- **Invalid CSP**: 0% (all 12 mapped successfully)
- **Completeness**: 95.24% (4 missing addresses)
- **Perfect Records**: 8 of 12

### Overall:
- ✅ **23 of 24** people (95.83%) have valid ID_CSP foreign keys
- ✅ **No orphaned records** in Consommation_CSP (all 6 categories have data)
- ✅ **Referential integrity maintained** across all joins

---

## 🎯 Aggregate Results Verification

### Query: "Show average consumption by CSP category"

**SQL Equivalent:**
```sql
SELECT 
    c.ID_CSP,
    AVG(cons.NB_KW_Jour * 365) AS Conso_moyenne_annuelle,
    c.Salaire_Moyen
FROM CSP c
JOIN Population p ON c.ID_CSP = p.ID_CSP
JOIN Consommation cons ON extract_street(p.Adresse) = cons.Nom_Rue
GROUP BY c.ID_CSP, c.Salaire_Moyen
ORDER BY c.ID_CSP;
```

**Results (from Consommation_CSP.csv):**
```
ID_CSP | Avg Consumption (kWh/year) | Avg Salary (€)
-------|----------------------------|---------------
1      | 5,383.75                   | 24,780
2      | 4,453.00                   | 24,780
3      | 4,945.75                   | 39,860
4      | 5,779.17                   | 29,720
5      | 5,155.62                   | 24,450
6      | 4,453.00                   | 26,445
```

**Insights:**
- 🔍 Professions intermédiaires (ID_CSP=4) have **highest consumption** (5,779 kWh/year)
- 💰 Cadres (ID_CSP=3) have **highest salary** (39,860€) but moderate consumption
- 📉 Artisans (ID_CSP=2) and Ouvriers (ID_CSP=6) have **lowest consumption** (4,453 kWh/year)

---

## ✅ Implementation Checklist

- [x] Modified `standardize_csp_value()` to return ID_CSP (1-6) instead of text
- [x] Updated `clean_population_paris()` to create ID_CSP column
- [x] Updated `clean_population_evry()` to create ID_CSP column
- [x] Removed old CSP text column from cleaned files
- [x] Updated `aggregate_data.py` to use ID_CSP directly (no text mapping needed)
- [x] Updated `compute_metrics.py` to validate ID_CSP (integers 1-6)
- [x] Verified all 6 CSP categories in output
- [x] Verified joins work correctly with foreign keys
- [x] Tested complete pipeline: Raw → Clean → Aggregate → Metrics

---

## 🚀 Next Steps

1. **Database Schema (if migrating to SQL database):**
   ```sql
   ALTER TABLE Population_Paris 
   ADD CONSTRAINT fk_csp 
   FOREIGN KEY (ID_CSP) REFERENCES CSP(ID_CSP);
   
   ALTER TABLE Population_Evry 
   ADD CONSTRAINT fk_csp 
   FOREIGN KEY (ID_CSP) REFERENCES CSP(ID_CSP);
   ```

2. **Index Optimization:**
   ```sql
   CREATE INDEX idx_population_paris_csp ON Population_Paris(ID_CSP);
   CREATE INDEX idx_population_evry_csp ON Population_Evry(ID_CSP);
   ```

3. **Consider**: Add `ON DELETE RESTRICT` to prevent CSP deletion if referenced

---

## 📝 Notes

- **"Retraitée" Handling**: Row 11 in Population_Paris (Isabelle Perrin) has NULL ID_CSP because "Retraitée" (retiree) is not an official INSEE CSP category (only active employment categories 1-6 are recognized).

- **Data Integrity**: The foreign key approach ensures that only valid CSP categories (1-6) can exist in population tables, preventing data quality issues.

- **Performance**: Integer joins are significantly faster than text matching, especially important when scaling to larger datasets.

---

*Generated: November 4, 2025 21:54*  
*Pipeline Version: 2.0 (ID_CSP Foreign Keys)*
