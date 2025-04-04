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

extractor_names = [
    "us_states",
    "orders",
    "products",
    "suppliers",
    "customers",
    "categories",
    "employees",
    "territories",
    "employee_territories",
    "shippers",
    "region"
]

with DAG(
    'pipeline_full',
    start_date=datetime(2000, 1, 1),
    catchup=False,
    schedule_interval='@daily',
    default_args=default_args,
) as dag:

    # Exemplo de tarefa "fixa"
    step1_task1 = BashOperator(
        task_id='tap-csv_target-csv',
        bash_command='meltano run tap-csv target-csv',
        cwd='.',
        env={
            "EXECUTION_DATE": "{{ ds }}",
            "PATH": f'{os.path.expanduser('~')}/.local/bin:{os.environ.get('PATH', '')}'}
    )

    meltano_per_table=[BashOperator(
        task_id=f"tap_postgres_target_db_csv_{extractor}",
        bash_command=(
            'export TABLE={{ params["table"] }} && '
            'meltano run '
            'tap-postgres-{{ params["extractor_name"] }} target-db-csv'
        ),
        cwd='.',
        env={
            "EXECUTION_DATE": "{{ ds }}",
            "PATH": f'{os.path.expanduser('~')}/.local/bin:{os.environ.get('PATH', '')}'
        },
        params={
            "extractor_name": extractor,
            "table": f"public-{extractor}"
        },
    ) for extractor in extractor_names]

    step2_task = BashOperator(
    task_id='tap-csv2_target-postgres',
    bash_command='meltano run tap-csv2 target-postgres',
    cwd='.',
    env={
        "EXECUTION_DATE": "{{ ds }}",
        "PATH": f'{os.path.expanduser('~')}/.local/bin:{os.environ.get('PATH', '')}'
    },
    )

    step1_task1 >> meltano_per_table >> step2_task