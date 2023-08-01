import os
import sys
from datetime import datetime
sys.path.append("/opt/airflow/scripts")

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable

from etl_script import TaskManagement, load_into_db

db_file = Variable.get("DB_FILE")
total_records = int(Variable.get("TOTAL_RECORDS"))
page_size = int(Variable.get("PAGE_SIZE"))
req_in_task = int(Variable.get("REQUEST_IN_TASK"))
extra_task = 1
number_of_request = total_records // page_size
if total_records % page_size != 0:
    extra_task += 1
total_task = (number_of_request // req_in_task)
if number_of_request % req_in_task != 0:
    extra_task += 1

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 7, 31),
    'depends_on_past': False,
}

with DAG(
        'extract_data',
        default_args=default_args,
        description='DAG to extract images from 3rd party.',
        schedule_interval='@daily',
) as dag:

    def ingesting():
        """
        This task is created to ingest the data into the DB.
        :return: None
        """
        
        load_into_db(db_file, total_records)

    # Define the task that generates data and stores it in XCom
    def generate_data(query, **context):
        context['ti'].xcom_push(key='query', value=query)

    task_generate_data = PythonOperator(
        task_id='generate_data',
        python_callable=generate_data,
        op_kwargs={"query": '{{dag_run.conf["query"] if "query" in dag_run.conf else "nature"}}'},
        provide_context=True,
        dag=dag,
    )

    ingesting_data = PythonOperator(
        task_id='ingest_data',
        python_callable=ingesting,
        dag=dag,
    )

    # Define a list of parallel tasks that process data using the values from XCom
    def process_parallel(start, end, query):
        obj = TaskManagement()
        result = obj.get_records(start, end, query, page_size)
        return result

    task_process_parallel = [PythonOperator(
        task_id=f'page_start_{i * req_in_task + 1}_end_{(i + 1) * req_in_task if i + 1 != total_task else ((i + 1) * req_in_task) + extra_task}',
        python_callable=process_parallel,
        provide_context=True,
        op_kwargs={
            "start": i * req_in_task + 1,
            "end": (i + 1) * req_in_task if i + 1 != total_task else ((i + 1) * req_in_task) + extra_task,
            "query": '{{dag_run.conf["query"] if "query" in dag_run.conf else "nature"}}'
        },
        dag=dag,
    ) for i in range(0, total_task)]

    # Set the dependencies between tasks
    task_generate_data >> task_process_parallel >> ingesting_data
