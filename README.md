# Prerequisite
- docker


# Description

* Extracts Data from pexel API and loads into sqlite3 DB.
* Data is extracted using parallelism by airflow tasks

# Setup
 - create .env file in the root directory and put "AIRFLOW_UID=1000" in the .env file.
 
 - inside docker compose x-airflow-common in the the environment set these env variables
 BASE_URL = "https://api.pexels.com/v1/"
 API_KEY = {API key generated from pexel}
 BASE_CSV_DIRECTORY = {directory where intermediate csvs should be createdD}
 MAX_PER_PAGE = {max request per page}
 SLEEP_TIMER = {sleep time between calls of API for retry}
 - run `docker compose up --build`

# Run application
- go to http://127.0.0.1:8080
- login with username = "airflow", password = "airflow"
- Set these variables in the Admin dropdown
PAGE_SIZE = {number of records for each page }
REQUEST_IN_TASK = {number of requests handled by each task in airflow}
TOTAL_RECORDS = {total number of records required in DB}
- In the DAGs menu search for "extract_data"
- Select trigger dag with config from run button in right corner
- Set parameters and put json in the format {
    "query": {query value}
} and click trigger

# Submissions
- DDL queries are submitted in `database_ddl.sql` file.
- DQL queries are submitted in `dql_queries.sql`