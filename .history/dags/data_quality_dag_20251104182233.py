"""
Data Quality Metrics DAG
Airflow DAG to compute data quality metrics from CSV files.
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


def run_data_quality_checks():
    """
    Execute data quality metrics computation.
    """
    print("Starting data quality metrics computation...")
    compute_metrics_main()
    print("Data quality metrics computation completed!")


# Create the DAG
with DAG(
    'data_quality_metrics',
    default_args=default_args,
    description='Calculate data quality metrics for CSV files',
    schedule_interval='@daily',  # Run daily, adjust as needed
    catchup=False,
    tags=['data_quality', 'metrics'],
) as dag:

    # Task to compute data quality metrics
    compute_metrics_task = PythonOperator(
        task_id='compute_data_quality_metrics',
        python_callable=run_data_quality_checks,
        dag=dag,
    )

    compute_metrics_task
