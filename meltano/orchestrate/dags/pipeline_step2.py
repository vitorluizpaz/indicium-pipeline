import os
from airflow import DAG
from airflow.operators.bash import BashOperator # type: ignore
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'pipeline_step2',
    start_date=datetime(2000, 1, 1),
    catchup=True,
    schedule_interval='@daily',
    default_args=default_args,
) as dag:

    step2_task = BashOperator(
        task_id='tap-csv2_target-postgres',
        bash_command='/Users/vitorpaz/.local/bin/meltano run tap-csv2 target-postgres',
        cwd='/Users/vitorpaz/Desktop/indicium-pipeline/meltano',
        env={
            "EXECUTION_DATE": "{{ ds }}",
            "PATH": f"/Users/vitorpaz/.local/bin:{os.environ.get('PATH', '')}"
        },
    )

    step2_task
    