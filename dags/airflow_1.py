from airflow.operators.python_operator import PythonOperator
from airflow import DAG
from datetime import datetime, timedelta

# from airflow.sensors.time_sensor import TimeSensor
import requests
import csv
from datetime import date
# import google.oauth2
#
# # Google big query Authentication
# credentials = google.oauth2.service_account.Credentials.from_service_account_file(
#     '/home/nineleaps/airflow/cred.json')
# project_id = 'apache-279104'
# client = bigquery.Client(credentials=credentials, project=project_id)

args = {'owner': 'me', 'start_date': datetime(2020, 5, 30),
        'end_date': datetime(2020, 5, 31),
        'retries': 2, 'retry_delay': timedelta(minutes=1)}
dags = DAG('covid_dag_tra', default_args=args)


# schedule_interval='0 */6 * * *',


# def load_into_big_query(client=client):
    # """Upload table data from a CSV file."""
    # dataset_id = "apache_airflow_pipeline"
    # table_id = "covid_dataset"
    # dataset = bigquery.Dataset(client.dataset(dataset_id))
    # print(dataset)
    # dataset.location = "US"
    #
    # filename = "data_covid.csv"
    # dataset_ref = client.dataset(dataset_id)
    # table_ref = dataset_ref.table(table_id)
    # job_config = bigquery.LoadJobConfig()
    # job_config.source_format = bigquery.SourceFormat.CSV
    # job_config.skip_leading_rows = 1
    # job_config.autodetect = True
    #
    # try:
    #     print("loading into dataset")
    #     with open(filename, "rb") as source_file:
    #         job = client.load_table_from_file(source_file, table_ref, job_config=job_config)
    #     job.result()
    #     print("Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table_id))
    # except:
    #     print("creating dataset")
    #     client.create_dataset(dataset)
    #     with open(filename, "rb") as source_file:
    #         job = client.load_table_from_file(source_file, table_ref, job_config=job_config)
    #     job.result()
    #     print("Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table_id))


def get_covid_data(url, **context):
    data = requests.get(url)
    cvd = open('data_covid-tra.csv', 'a')
    csv_writer = csv.writer(cvd)

    csv_writer.writerow(['Date', 'State', 'Cases'])
    data = data.json()
    for i in data:
        csv_writer.writerow([context['execution_date'], i['State UT'], i[str(context['execution_date']).split('T')[0]]])
    print('csv loaded successfully.')
    print(context['execution_date'])


# t2 = PythonOperator(task_id='big_query', op_kwargs={'client': client}, python_callable=load_into_big_query, dag=dags)
t1 = PythonOperator(task_id='covid_data', python_callable=get_covid_data,
                    op_kwargs={'url': "https://covid-india-cases.herokuapp.com/statetimeline/"}, provide_context=True, dag=dags)
# t2.set_upstream(t1)
t1
# t2.set_upstream(t1)
# t3.set_upstream(t2)
# [t1, t2] << t3
