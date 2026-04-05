FROM apache/airflow:2.9.0

USER root
RUN apt-get update && apt-get install -y libpq-dev gcc && apt-get clean

USER airflow
RUN pip install --no-cache-dir \
    psycopg2-binary \
    dbt-core \
    dbt-postgres