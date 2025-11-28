# Data Quality Metrics - Airflow Project

This project calculates data quality metrics from CSV files and stores them in a metadata file.

## Project Structure

```
new QD data/
├── dags/
│   ├── data_quality_dag.py          # Airflow DAG definition
│   └── scripts/
│       └── compute_metrics.py       # Data quality computation script
├── metadata/
│   └── metadata_qd.csv              # Output metadata file (generated)
├── Consommation_Evry.csv            # Input data
├── Consommation_Paris.csv           # Input data
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Metrics Calculated

The DAG computes **38 comprehensive data quality metrics** across 5 tables. See `DATA_QUALITY_METRICS.md` for detailed documentation.

### Summary by Table:

#### Consommation_Evry (10 metrics):
- Total/valid rows, invalid rate
- % invalid postal codes, % valid addresses, % invalid consumption
- Table completeness, tuple completeness distribution (< 50%, 50-100%, 100%)

#### Consommation_Paris (10 metrics):
- Total/valid rows, invalid rate
- % invalid postal codes, % valid addresses, % invalid consumption
- Table completeness, tuple completeness distribution

#### Population_Paris (7 metrics):
- Total rows
- % invalid addresses (format: "Ville, Numéro NomRue")
- % invalid CSP (not in reference list)
- Table completeness, tuple completeness distribution

#### Population_Evry (7 metrics):
- Total rows
- % invalid addresses, % invalid CSP
- Table completeness, tuple completeness distribution

#### CSP Table (4 metrics):
- Total rows
- % invalid salaries (out of range [0, 1,000,000])
- Salary attribute completeness
- Table completeness

## Validation Rules

### Conformité (Conformity):
1. **Postal Code (Code_Postal)**: Must match regex `[0-9]{5}` (exactly 5 digits)
2. **Address (Consommation tables)**: Both N and Nom_Rue must be non-empty
3. **Address (Population tables)**: Must follow format "Ville, Numéro NomRue"
4. **Consumption (NB_KW_Jour)**: Must be numeric and ≥ 0 (CHECK constraint)
5. **CSP**: Must belong to predefined list (from CSP reference table)
6. **Salaire_Moyen**: Must be numeric and in range [0, 1,000,000]

### Complétude (Completeness):
1. **Attribute Completeness**: % of non-null values per column
2. **Tuple Completeness**: % of filled fields per row
3. **Relation Completeness**: % of non-null cells in entire table

### Tuple Classification:
- **< 50% complete**: Excluded (should use tFilterRow)
- **50-99% complete**: Requires imputation (tMap/tDenormalize)
- **100% complete**: Valid, no action needed

## Setup Instructions (Windows PowerShell)

### 1. Create Python Virtual Environment

```powershell
cd "c:\Users\mohamed abi\Desktop\new QD data"
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If you encounter execution policy errors, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Set Environment Variables

```powershell
$env:AIRFLOW_HOME = "c:\Users\mohamed abi\Desktop\new QD data"
```

### 4. Initialize Airflow Database

```powershell
airflow db init
```

### 5. Create Airflow User (Optional)

```powershell
airflow users create `
    --username admin `
    --firstname Admin `
    --lastname User `
    --role Admin `
    --email admin@example.com `
    --password admin
```

### 6. Start Airflow

Open two PowerShell terminals:

**Terminal 1 - Webserver:**
```powershell
cd "c:\Users\mohamed abi\Desktop\new QD data"
.\venv\Scripts\Activate.ps1
$env:AIRFLOW_HOME = "c:\Users\mohamed abi\Desktop\new QD data"
airflow webserver --port 8080
```

**Terminal 2 - Scheduler:**
```powershell
cd "c:\Users\mohamed abi\Desktop\new QD data"
.\venv\Scripts\Activate.ps1
$env:AIRFLOW_HOME = "c:\Users\mohamed abi\Desktop\new QD data"
airflow scheduler
```

### 7. Access Airflow UI

Open browser: http://localhost:8080

Login with credentials (if created): admin/admin

### 8. Run the DAG

- Find the DAG named `data_quality_metrics`
- Toggle it ON
- Click "Trigger DAG" to run manually

## Running the Script Standalone (Without Airflow)

You can also run the data quality computation script directly:

```powershell
cd "c:\Users\mohamed abi\Desktop\new QD data"
.\venv\Scripts\Activate.ps1
python dags\scripts\compute_metrics.py
```

This will generate the metadata file at: `metadata\metadata_qd.csv`

##  Interactive Dashboard (NEW!)

### Launch Live Dashboard with One Click

```powershell
cd "c:\Users\mohamed abi\Desktop\new QD data"
.\venv\Scripts\Activate.ps1
python dags\scripts\visualize_dashboard.py --server
```

Then open your browser to: **http://localhost:5050**

### Dashboard Features

 **6 Interactive Visualizations**:
1. Before & After Data Cleaning Comparison (Bar Chart)
2. Data Completeness Gauges (5 Tables)
3. Record Quality Distribution (Stacked Bars)
4. Issue Type Breakdown (Area Chart)
5. Multi-dimensional Quality Spider Chart
6. Table Health Matrix (Heatmap)

 **Live Pipeline Control**:
- Launch complete pipeline with one button click
- Real-time execution logs
- Step-by-step progress tracking (4 stages)
- Automatic dashboard refresh after completion

 **40-Metric Comparison Table**:
- Side-by-side Raw vs Cleaned data metrics
- Color-coded improvements/regressions
- 7 categories: Completeness, Validity, Unit Consistency, Quality Distribution, Row Counts

 **Metadata History Comparison**:
- View latest cleaned vs latest raw metadata files
- Full CSV data displayed in responsive tables
- Color-coded badges (Green=Cleaned, Blue=Raw)

 **Target Schemas Quality Metrics**:
- Completeness analysis for all 3 target schemas
- Missing values and duplicate detection
- Color-coded health indicators (Green/Orange/Red)

### Generate Static Dashboard (Without Server)

```powershell
python dags\scripts\visualize_dashboard.py
```

This creates `dashboard.html` with all visualizations embedded.

## Output Format

The metadata file (`metadata\metadata_qd.csv`) is semicolon-separated with **38 metrics**.

### Example Output:
```
total_rows_Cons_Evry;valid_rows_Cons_Evry;invalid_rate_Cons_Evry;pct_invalid_CP_Cons_Evry;...
12;5;58.33;25.0;100.0;41.67;94.79;0;5;7;13;12;7.69;7.69;100.0;0.0;100.0;...
```

### Key Insights from Sample Results:
- **Evry Consumption**: 58.33% invalid rows, 25% invalid postal codes, 41.67% invalid consumption
- **Paris Consumption**: 7.69% invalid rows, 7.69% invalid postal codes, 100% completeness
- **Population Paris**: 100% valid addresses, 8.33% invalid CSP
- **Population Evry**: 100% invalid addresses (format issue), 95.24% completeness
- **CSP Table**: 83.33% salary completeness (1 missing value imputed)

## Troubleshooting

### Issue: Import errors in Airflow
- Make sure `AIRFLOW_HOME` points to the project directory
- Check that the DAG file is in the `dags/` folder

### Issue: CSV files not found
- Ensure CSV files are in the root directory of the project
- Check file paths in the script

### Issue: Permission errors
- Run PowerShell as Administrator
- Adjust execution policy as shown above

## Configuration

To adjust the DAG schedule:
- Edit `schedule_interval` in `dags/data_quality_dag.py`
- Options: `'@daily'`, `'@hourly'`, `'@weekly'`, or cron expression

To modify validation rules:
- Edit functions in `dags/scripts/compute_metrics.py`

##  Documentation

This project includes comprehensive documentation:

### Core Documentation
- **[QUICK_START.md](QUICK_START.md)** - Quick start guide for new users (⭐ START HERE)
- **[PIPELINE_README.md](PIPELINE_README.md)** - Complete pipeline execution guide
- **[DATA_QUALITY_METRICS.md](DATA_QUALITY_METRICS.md)** - Detailed metrics documentation

### Data Cleaning Documentation
- **[DATA_CLEANING_STRATEGY.md](DATA_CLEANING_STRATEGY.md)** 🆕 - Complete explanation of our data cleaning philosophy, decisions, and quality trade-offs
  - Case studies (Population Évry, Consumption Évry, Address validation)
  - Specific transformations (postal codes, consumption units, CSP standardization)
  - Quality metrics explained (completeness, invalid rates, quality distribution)
  - Trade-offs & decisions (imputation strategy, deletion criteria)

- **[CLEAN_DATA_README.md](CLEAN_DATA_README.md)** 🆕 - Technical documentation for `clean_data.py` script
  - All functions reference (11 cleaning functions)
  - Cleaning rules and validation logic
  - Input/output structure
  - Examples and troubleshooting

### Target Schemas & Aggregation
- **[TARGET_SCHEMAS_ANALYSIS.md](TARGET_SCHEMAS_ANALYSIS.md)** 🆕 - Comprehensive analysis of final aggregated outputs
  - **Quality metrics for all 3 target schemas** (IRIS Paris, IRIS Évry, CSP)
  - **Issue #1 detected:** Duplicate IRIS in Évry ("AGUADO" vs "Aguado" case sensitivity)
  - **Issue #2 detected:** CSP aggregation limitations (small sample sizes, low coverage)
  - Comparison to source data (raw → cleaned → aggregated)
  - Detailed recommendations with implementation examples

### Additional Documentation
- **[DATA_MAPPING_README.md](DATA_MAPPING_README.md)** - Data mapping and transformation guide
- **[VALIDATION_RULES.md](VALIDATION_RULES.md)** - Validation rules reference
- **[ID_CSP_VERIFICATION.md](ID_CSP_VERIFICATION.md)** - CSP reference verification
- **[METRICS_SUMMARY.md](METRICS_SUMMARY.md)** - Metrics summary report
- **[SEPARATION_SUMMARY.md](SEPARATION_SUMMARY.md)** - Data separation documentation
- **[OUTPUT_STRUCTURE.md](OUTPUT_STRUCTURE.md)** - Output structure reference

### Why Read the Cleaning Documentation?

If you want to understand:
-  **Why** certain data quality metrics changed (e.g., "good quality" records decreased)
-  **How** we handle missing values (imputation vs. preservation)
-  **What** transformations are applied (postal codes, addresses, CSP codes)
-  **When** we delete vs. fix vs. keep data (our decision criteria)

 **Read [DATA_CLEANING_STRATEGY.md](DATA_CLEANING_STRATEGY.md)** for the complete story with case studies

 **Read [CLEAN_DATA_README.md](CLEAN_DATA_README.md)** for technical implementation details

## Notes

- The DAG runs daily by default
- No Docker configuration required
- All data quality checks are performed in Python
- Results are appended with timestamp for historical tracking
"# Data-Quality-Project-Energy-Data-" 
