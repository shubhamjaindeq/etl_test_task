import os
import csv
import time
import sqlite3
import json

import requests

BASE_URL = os.getenv('BASE_URL')
BASE_CSV_DIRECTORY = os.getenv('BASE_CSV_DIRECTORY')
PHOTOS_DIR = BASE_CSV_DIRECTORY + 'photos/'
MAX_PER_PAGE = int(os.getenv('MAX_PER_PAGE', 80))
SLEEP_TIMER = int(os.getenv('SLEEP_TIMER', 1))


class TaskManagement:

    def __init__(self):

        self.base_url = BASE_URL

    def extract_data(self, retry=0, **kwargs):
        """
        Extracts data from an API using a search query and optional pagination parameters.

        Args:
            retry (int, optional): Number of times to retry the API call in case of failure.
            **kwargs: Additional keyword arguments to pass to the API endpoint.
                    Supported keyword arguments:
                        - query (str): The search query to be used for filtering data.
                        - per_page (int): Number of results to return per page.
                        - page (int): The page number to retrieve from the API.

        Returns:
            dict: If the API call is successful, returns the JSON data as a dictionary.
            None: If the API call fails even after retrying, or if the retry limit is reached,
                returns None.
        """
        if retry >= 5:
            return
        headers = {"Authorization": os.getenv('API_KEY')}
        url = self.base_url + "search/"
        url += f"?query={kwargs.get('query')}&per_page={kwargs.get('per_page')}&page={kwargs.get('page')}"
        print("Request URL: ", url)
        try:
            response = requests.get(url, headers=headers)
            if response.ok:
                return response.json()
            print("Error in response: ", response, "Error message: ", response.text())
            print(f"Error on Page: {kwargs.get('page')}")
        except Exception as e:
            print("Error in API call", str(e))
        time.sleep(SLEEP_TIMER * retry)
        return self.extract_data(retry + 1, **kwargs)

    def get_records(self, start_page, end_page, query, records_per_page):
        """
        Retrieves and saves photo records from an API to a CSV file.

        This function fetches data from an API by sending requests for a specified range of pages
        and saves the retrieved photo records to a CSV file.
        method to fetch data for each page.

        Args:
            start_page (int): The page number to start fetching data from.
            end_page (int): The page number to stop fetching data (inclusive).
            query (str): The search query to be used for filtering the data.
            records_per_page (int): Number of records to retrieve per page.

        Returns:
            None
        """
        print("Executing for", start_page, end_page)
        if records_per_page > MAX_PER_PAGE:
            print(f"Records per page cannot be greater than {MAX_PER_PAGE}")
            return
        if not os.path.exists(PHOTOS_DIR):
            os.makedirs(PHOTOS_DIR)
        photos_filename = f"{PHOTOS_DIR}photos{start_page}_{end_page}.csv"
        with open(photos_filename, 'w') as p_file:
            photo_csvwriter = csv.writer(p_file)
            for page in range(start_page, end_page + 1):
                response_data = self.extract_data(
                    page=page,
                    query=query,
                    per_page=records_per_page
                )
                if not response_data:
                    print(f"Failed for {page}")
                    continue
                photos_list = []
                for photos in response_data['photos']:
                    liked = 1 if photos['liked'] else 0
                    photos_list.append([
                        photos['id'], photos['width'],
                        photos['height'], photos['url'],
                        photos['photographer'],
                        photos['photographer_url'],
                        photos['photographer_id'],
                        photos['avg_color'], liked,
                        photos['alt'],
                        json.dumps(photos['src'])
                    ])
                photo_csvwriter.writerows(photos_list)


def load_into_db(db_file, number_of_records):
    """
    Loads records into an SQLite database.

    This function reads photo records from CSV files in the directory specified by the constant
    `PHOTOS_DIR`, inserts the records into two tables (`photos` and `photo_sources`) of an SQLite
    database specified by the `db_file`, and removes the processed CSV files.

    Returns:
        None: This function does not return any value.
    """
    # db_file = DB_FILE
    conn = sqlite3.connect(db_file)
    cursor_obj = conn.cursor()
    f = open("scripts/database_ddl.sql", 'r')
    cursor_obj.executescript(f.read())
    photos_insert_query = """INSERT INTO photos(id, width, height, url, photographer, photographer_url, photographer_id, avg_color, liked, alt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    source_insert_query = """INSERT INTO photo_sources(type, url, photo_id) VALUES (?, ?, ?) """
    photo_id_dict = {}
    to_break = False
    counter = 0
    for file in os.listdir(PHOTOS_DIR):
        photo_rows = []
        source_rows = []
        with open(PHOTOS_DIR + file, mode='r') as f:
            csvFile = csv.reader(f)
            for lines in csvFile:
                if counter >= number_of_records:
                    to_break = True
                    break
                photo_id = int(lines[0])
                if photo_id in photo_id_dict:
                    continue
                photo_id_dict[photo_id] = True
                counter += 1
                current_row = (
                    int(lines[0]), int(lines[1]), int(lines[2]),
                    lines[3], lines[4], lines[5], lines[6], lines[7],
                    int(lines[8]), lines[9]
                )
                photo_rows.append(current_row)
                source = json.loads(lines[10])
                for key, value in source.items():
                    source_rows.append((key, value, photo_id))

        cursor_obj.executemany(photos_insert_query, photo_rows)
        cursor_obj.executemany(source_insert_query, source_rows)
        os.remove(PHOTOS_DIR + '/' + file)
        if to_break:
            break
    print(counter, "rows entered")
    conn.commit()
    conn.close()
