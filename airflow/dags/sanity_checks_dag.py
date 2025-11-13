from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from cassandra.cluster import Cluster

def check_cassandra():
    cluster = Cluster(['cassandra'])
    session = cluster.connect()
    session.execute('SELECT now() FROM system.local')
    return "Cassandra OK"

default_args = {
    "owner": "data-eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="sanity_checks",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["sanity", "infra"],
) as dag:

    cassandra_check = PythonOperator(
        task_id="cassandra_check",
        python_callable=check_cassandra
    )

    cassandra_check
