from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys

sys.path.insert(0, '/opt/airflow')

default_args = {
    'owner': 'de_admin',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,
}

with DAG(
    dag_id='ecommerce_pipeline',
    default_args=default_args,
    description='E-commerce data pipeline: ingest → dbt run → dbt test',
    schedule_interval='0 6 * * *',   # Chạy mỗi ngày lúc 6 giờ sáng
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ecommerce', 'daily'],
) as dag:

    # Task 1: Load CSV vào raw schema
    ingest = PythonOperator(
        task_id='ingest_raw_data',
        python_callable=lambda: __import__(
            'ingestion.load_raw', fromlist=['main']
        ).main(),
    )

    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command=(
            'export PATH=$PATH:/home/airflow/.local/bin && '
            'cd /opt/airflow/ecommerce_pipeline && '
            'dbt run --profiles-dir /opt/airflow/ecommerce_pipeline'
        ),
    )

    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command=(
            'export PATH=$PATH:/home/airflow/.local/bin && '
            'cd /opt/airflow/ecommerce_pipeline && '
            'dbt test --profiles-dir /opt/airflow/ecommerce_pipeline'
        ),
    )

    # Định nghĩa thứ tự chạy
    ingest >> dbt_run >> dbt_test