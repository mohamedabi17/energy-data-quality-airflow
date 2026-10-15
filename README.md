<div align="center">

# ⚡ Energy Data Quality Pipeline

**Measure → clean → integrate → re-measure: an Airflow pipeline that audits household energy-consumption data for Paris & Évry with 38 quality metrics and proves the improvement.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8-017CEE?logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![pandas](https://img.shields.io/badge/pandas-2.1-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Flask%20dashboard-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/python/)
[![Metrics](https://img.shields.io/badge/quality%20metrics-38-success)](DATA_QUALITY_METRICS.md)
[![Dashboard](https://img.shields.io/badge/dashboard-interactive-orange)](dashboard.html)

*Master's project — Data Quality*

</div>

---

## 📌 Table of contents

- [Problem](#-problem)
- [Pipeline](#-pipeline)
- [Quality dimensions](#-quality-dimensions)
- [Results](#-results)
- [Data integration](#-data-integration)
- [Dashboard](#-dashboard)
- [Quick start](#-quick-start)
- [Project structure](#-project-structure)

---

## 🎯 Problem

Five heterogeneous sources must be integrated to answer: *what is the average annual electricity consumption per IRIS district and per socio-professional category (CSP)?*

| Source | Content | Typical defects |
|---|---|---|
| `Consommation_Paris` | Address, postal code, daily kW | Wrong unit (kW vs kWh/day), bad postal codes |
| `Consommation_Evry` | Same, different format | Invalid postal codes, non-numeric consumption, gaps |
| `Population_Paris` | Residents, address, CSP | Malformed addresses |
| `Population_Evry` | Residents, address, CSP | Address format, CSP codes vs labels |
| `CSP` | CSP reference + mean salary | Missing salary |

---

## 🔄 Pipeline

```mermaid
flowchart LR
    IN[("📥 input_data/<br/>5 raw CSV + IRIS")] --> M1["📏 compute_uncleaned_metrics"]
    M1 --> CL["🧹 clean_data"]
    CL --> AG["🔗 aggregate_data"]
    AG --> M2["📏 compute_cleaned_metrics"]
    M1 --> MD1[("metadata_qd_raw_*.csv")]
    M2 --> MD2[("metadata_qd_cleaned_*.csv")]
    CL --> CD[("cleaned_data/")]
    AG --> TS[("target_schemas/<br/>IRIS Paris · IRIS Évry · CSP")]
    MD1 & MD2 --> DB["📊 Dashboard<br/>raw vs cleaned"]

    style CL fill:#017CEE,color:#fff
    style AG fill:#017CEE,color:#fff
```

Airflow DAG `data_quality_metrics` (`@daily`):

```
compute_uncleaned_metrics >> clean_data >> aggregate_data >> compute_cleaned_metrics
```

Every run writes **timestamped metadata snapshots**, giving a full history of quality over time.

---

## 📐 Quality dimensions

```mermaid
mindmap
  root((38 metrics))
    Conformity
      Postal code = 5 digits
      Address format per city
      kWh/day numeric and ≥ 0
      CSP in reference list
      Salary in 0 – 1 000 000
    Completeness
      Attribute
      Tuple
      Relation / table
    Validity
      Valid vs invalid rows
      Invalid rate per table
    Consistency
      Unit normalization kW → kWh/day
```

**Tuple triage:** `< 50 %` complete → excluded · `50–99 %` → imputed · `100 %` → kept as is.

### Cleaning rules (`clean_data.py`)

| Function | Fix |
|---|---|
| `clean_postal_code` | Normalize to 5 digits, reject impossible codes |
| `normalize_kw_to_kwh_per_day` | Unify consumption units |
| `standardize_address_paris / _evry` | Canonical `Ville, Numéro NomRue` |
| `standardize_csp_value` · `map_csp_numeric_to_text` | Codes ↔ labels against the reference table |
| `clean_csp_table` | Salary validation + imputation |

---

## 📊 Results

Measured on the latest raw vs cleaned snapshots (`metadata/`):

| Metric | Raw | Cleaned |
|---|:---:|:---:|
| Invalid rows — Consumption Évry | 58.33 % | **0 %** |
| Invalid rows — Consumption Paris | 100 % | **0 %** |
| Invalid postal codes — Évry | 25 % | **0 %** |
| Invalid kWh values — Évry | 41.67 % | **0 %** |
| Wrong unit — Paris | 100 % | **0 %** |
| Invalid addresses — Population Paris | 8.33 % | **0 %** |
| Invalid addresses — Population Évry | 100 % | 41.67 % |
| Invalid CSP — Population Évry | 100 % | **0 %** |
| Completeness — Consumption Évry | 90.74 % | **100 %** |
| Completeness — CSP salary | 83.33 % | **100 %** |

```mermaid
xychart-beta
    title "Invalid rate (%) — raw vs cleaned"
    x-axis ["Cons. Évry", "Cons. Paris", "CP Évry", "kWh Évry", "Addr. Pop Paris", "Addr. Pop Évry", "CSP Pop Évry"]
    y-axis "% invalid" 0 --> 100
    bar [58.33, 100, 25, 41.67, 8.33, 100, 100]
    bar [0, 0, 0, 0, 0, 41.67, 0]
```

*First bar series = raw, second = cleaned.* Remaining issue: some Évry addresses can't be repaired without an external geocoding reference — documented rather than guessed (see [`DATA_CLEANING_STRATEGY.md`](DATA_CLEANING_STRATEGY.md)).

---

## 🔗 Data integration

```mermaid
flowchart TB
    CP["Consumption Paris"] --> J1{"street → IRIS<br/>map_address_to_iris"}
    CE["Consumption Évry"] --> J2{"street → IRIS"}
    IR[("IRIS reference")] --> J1 & J2
    J1 --> T1[("Consommation_IRIS_Paris<br/>ID_IRIS · Conso_moyenne_annuelle")]
    J2 --> T2[("Consommation_IRIS_Evry")]
    CP & CE --> J3{"address → resident → CSP"}
    PP["Population Paris"] & PE["Population Évry"] --> J3
    CSP[("CSP reference")] --> J3
    J3 --> T3[("Consommation_CSP<br/>ID_CSP · Conso_moyenne_annuelle · Salaire_Moyen")]
```

Issues found *after* integration are analysed in [`TARGET_SCHEMAS_ANALYSIS.md`](TARGET_SCHEMAS_ANALYSIS.md) (e.g. a duplicated IRIS caused by case sensitivity, small CSP samples).

---

## 📈 Dashboard

```bash
pip install flask flask-cors plotly                  # dashboard extras
python dags/scripts/visualize_dashboard.py --server   # → http://localhost:5050
python dags/scripts/visualize_dashboard.py            # static dashboard.html
```

Six visualizations (before/after bars, completeness gauges, quality distribution, issue breakdown, radar, table-health heatmap), a 40-metric comparison table, metadata history, and a **one-click pipeline launcher with live logs**.

---

## 🚀 Quick start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Without Airflow
python dags/scripts/compute_metrics.py
python dags/scripts/clean_data.py
python dags/scripts/aggregate_data.py

# With Airflow
export AIRFLOW_HOME=$(pwd)
airflow db init
airflow webserver --port 8080 &   airflow scheduler
# → enable and trigger the DAG "data_quality_metrics"
```

---

## 📁 Project structure

```
.
├── dags/
│   ├── data_quality_dag.py          # 4-task Airflow DAG
│   └── scripts/
│       ├── compute_metrics.py       # 38 quality metrics
│       ├── clean_data.py            # Cleaning & standardization
│       ├── aggregate_data.py        # Integration into target schemas
│       ├── compare_metrics.py       # Raw vs cleaned comparison
│       └── visualize_dashboard.py · dashboard_server.py
├── input_data/                      # Raw sources + IRIS reference
├── cleaned_data/                    # Cleaned tables
├── target_schemas/                  # Final integrated outputs
├── metadata/                        # Timestamped quality snapshots
├── rapport.tex                      # Academic report
└── *.md                             # Metrics, rules, strategy, schema analysis
```

---

<div align="center">

**Mohamed Abi** · [GitHub @mohamedabi17](https://github.com/mohamedabi17)

</div>
