from airflow.operators.python_operator import PythonOperator
from airflow import DAG
from datetime import datetime, timedelta
from google.cloud import bigquery


import requests
import csv
import google.oauth2

# Google big query Authentication
credentials = google.oauth2.service_account.Credentials.from_service_account_file(
    '/home/nineleaps/airflow/cred.json')
project_id = 'apache-279104'
client = bigquery.Client(credentials=credentials, project=project_id)

# Arguments for a dag.
args = {
    'owner': 'Raghu',
        'depends_on_past': True,
        'start_date': datetime(2020, 5, 30),
        'end_date': datetime(2020, 6, 2),
        'retries': 2,
        'retry_delay': timedelta(minutes=1)
}

# Dag for the pipeline.
dags = DAG('covid_dag', default_args=args, schedule_interval='0 21 * * *')


def load_into_big_query(client, **context):
    """
    The method is used for loading csv data to big query table.
    :param client: Google auth client.
    :param context: Dag context.
    :return: None
    """
    """Upload table data from a CSV file."""
    dataset_id = "apache_airflow_pipeline_covid"
    table_id = "apche_covid_dataset"
    dataset = bigquery.Dataset(client.dataset(dataset_id))
    print(dataset)
    dataset.location = "US"

    dt = str(context['execution_date']).split('T')[0]
    filename = 'data_covid_{}.csv'.format(dt)
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)
    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.CSV
    job_config.skip_leading_rows = 1
    job_config.autodetect = True

    try:
        print("loading into dataset")
        with open(filename, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_ref, job_config=job_config)
        job.result()
        print("Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table_id))
    except:
        print("creating dataset")
        client.create_dataset(dataset)
        with open(filename, "rb") as source_file:
            job = client.load_table_from_file(source_file, table_ref, job_config=job_config)
        job.result()
        print("Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table_id))


def check_upload_status(**context):
    """
    The method is for checking upload status of the data.
    :param context: Dag context.
    :return: None
    """
    query = "select count(*) from apache-279104.apache_airflow_pipeline_covid.apche_covid_dataset where Date = '{}'".format(str(context['execution_date']).split('T')[0])
    query_job = client.query(query)
    result = query_job.result()
    no_of_rows = list(result)[0][0]
    print(no_of_rows, 'big query result')
    dt = str(context['execution_date']).split('T')[0]
    filename = 'data_covid_{}.csv'.format(dt)
    with open(filename, "r") as f:
        reader = csv.reader(f, delimiter=",")
        data = list(reader)
        row_count = len(data)
    print(row_count, 'csv rows')
    percent_of_upload = (no_of_rows * 100) / row_count
    print('{} % is uploaded.........'.format(percent_of_upload))


def get_covid_data(url, **context):
    """
    The method is used for getting data from covid api to a csv file.
    :param url: The url for getting data.
    :param context: Dag context.
    :return: None.
    """
    data = requests.get(url)
    dt = str(context['execution_date']).split('T')[0]

    cvd = open('data_covid_{}.csv'.format(dt), 'w')
    csv_writer = csv.writer(cvd)
    csv_writer.writerow(['Date', 'State', 'Cases'])
    data = data.json()
    for i in data:
        csv_writer.writerow([str(context['execution_date']).split('T')[0], i['State UT'], i[str(context['execution_date']).split('T')[0]]])
    print('csv loaded successfully.')


t2 = PythonOperator(task_id='big_query', op_kwargs={'client': client}, provide_context=True, python_callable=load_into_big_query, dag=dags)
t1 = PythonOperator(task_id='covid_data', python_callable=get_covid_data, provide_context=True,
                    op_kwargs={'url': "https://covid-india-cases.herokuapp.com/statetimeline/"}, dag=dags)
t3 = PythonOperator(task_id='status_of_upload', provide_context=True, python_callable=check_upload_status, dag=dags)

t2.set_upstream(t1)
t3.set_upstream(t2)


