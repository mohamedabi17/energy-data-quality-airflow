"""
Data Quality Metrics DAG
Airflow DAG to compute data quality metrics from CSV files.

Pipeline:
1. Compute metrics on uncleaned data
2. Clean data (normalize units, standardize formats, remove duplicates)
3. Aggregate to target schemas (IRIS and CSP)
4. Compute metrics on cleaned data
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
from pathlib import Path

# Add scripts directory to path
scripts_path = Path(__file__).parent / 'scripts'
sys.path.insert(0, str(scripts_path))

from compute_metrics import main as compute_metrics_main
from clean_data import main as clean_data_main
from aggregate_data import main as aggregate_data_main


# Default arguments for the DAG
default_args = {
    'owner': 'data_quality_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def run_uncleaned_metrics():
    """
    Execute data quality metrics computation on uncleaned data.
    """
    print("Starting uncleaned data quality metrics computation...")
    compute_metrics_main()
    print("Uncleaned metrics computation completed!")


def run_data_cleaning():
    """
    Execute data cleaning pipeline.
    """
    print("Starting data cleaning...")
    clean_data_main()
    print("Data cleaning completed!")


def run_data_aggregation():
    """
    Execute data aggregation to create target schemas.
    """
    print("Starting data aggregation...")
    aggregate_data_main()
    print("Data aggregation completed!")


def run_cleaned_metrics():
    """
    Execute data quality metrics computation on cleaned data.
    """
    print("Starting cleaned data quality metrics computation...")
    compute_metrics_main()
    print("Cleaned metrics computation completed!")


# Create the DAG
with DAG(
    'data_quality_metrics',
    default_args=default_args,
    description='Complete data quality pipeline: metrics → clean → aggregate → metrics',
    schedule_interval='@daily',  # Run daily, adjust as needed
    catchup=False,
    tags=['data_quality', 'metrics', 'etl'],
) as dag:

    # Task 1: Compute metrics on uncleaned data
    compute_uncleaned_metrics = PythonOperator(
        task_id='compute_uncleaned_metrics',
        python_callable=run_uncleaned_metrics,
        dag=dag,
    )

    # Task 2: Clean the data
    clean_data = PythonOperator(
        task_id='clean_data',
        python_callable=run_data_cleaning,
        dag=dag,
    )

    # Task 3: Aggregate cleaned data to target schemas
    aggregate_data = PythonOperator(
        task_id='aggregate_data',
        python_callable=run_data_aggregation,
        dag=dag,
    )

    # Task 4: Compute metrics on cleaned data
    compute_cleaned_metrics = PythonOperator(
        task_id='compute_cleaned_metrics',
        python_callable=run_cleaned_metrics,
        dag=dag,
    )

    # Define pipeline dependencies
    compute_uncleaned_metrics >> clean_data >> aggregate_data >> compute_cleaned_metrics
