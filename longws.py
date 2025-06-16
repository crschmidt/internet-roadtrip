import websocket
import _thread
import time
import json
import rel
from google.cloud import bigquery
from google.oauth2 import service_account
import uuid
import logging

logging.basicConfig(level=logging.INFO)

PROJECT_ID = "internet-road-trip"  # Replace with your Google Cloud project ID
DATASET_ID = "irt"  # Replace with your BigQuery dataset ID
TABLE_ID = "stops"  # Replace with your BigQuery table ID

stop = 0
prev = None
credentials = service_account.Credentials.from_service_account_file(
    './key.json',
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
dataset_ref = client.dataset(DATASET_ID)
table_ref = dataset_ref.table(TABLE_ID)
table = client.get_table(table_ref) if client.get_table(table_ref) else None

if not table:
    logging.info(f"Table {TABLE_ID} not found, creating it...")
    schema = [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("raw_json", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("stop", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("location", "RECORD", mode="NULLABLE", fields=[
            bigquery.SchemaField("road", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("state", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("county", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("neighborhood", "STRING", mode="NULLABLE"),
        ]),
        bigquery.SchemaField("voteCounts", "RECORD", mode="REPEATED", fields=[
            bigquery.SchemaField("key", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("value", "INTEGER", mode="REQUIRED"),
        ]),
        bigquery.SchemaField("pano", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("heading", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("options", "RECORD", mode="REPEATED", fields=[
            bigquery.SchemaField("pano", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("heading", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("lat", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("lng", "FLOAT", mode="NULLABLE"),
                ]),
        bigquery.SchemaField("endTime", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("lat", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("lng", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("totalUsers", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("distance", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("chosen", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("station", "RECORD", mode="NULLABLE", fields=[
            bigquery.SchemaField("name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("url", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("distance", "INTEGER", mode="NULLABLE"),
        ]),
        bigquery.SchemaField("nowPlaying", "STRING", mode="NULLABLE"),
    ]
    table = bigquery.Table(table_ref, schema=schema)
    table = client.create_table(table)
    logging.info(f"Table {TABLE_ID} created.")
else:
    logging.info(f"Table {TABLE_ID} found.")

def on_message(ws, message):
    global stop, prev
    try:
        data = json.loads(message)
        if not stop:
            stop = data.get('stop')
            logging.info(f"Initial stop: {stop}")
        if data['stop'] != stop and prev:
            #logging.info(f"Previous message: {prev}")
            row_id = str(uuid.uuid4())
            row = {
                "id": row_id,
                "raw_json": message,
                "stop": data.get('stop'),
                "location": data.get('location'),
                "voteCounts": [],
                "pano": data.get('pano'),
                "heading": data.get('heading'),
                "options": data.get('options'),
                "endTime": data.get('endTime'),
                "lat": data.get('lat'),
                "lng": data.get('lng'),
                "totalUsers": data.get('totalUsers'),
                "distance": data.get('distance'),
                "chosen": data.get('chosen'),
                "station": data.get('station'),
                "nowPlaying": data.get('nowPlaying'),
            }
            if data.get('voteCounts'):
                row["voteCounts"] = [{"key": key, "value": value} for key, value in data['voteCounts'].items()]
            errors = client.insert_rows_json(table, [row])
            if errors:
                logging.error(f"Failed to insert row: {errors}")
            else:
                logging.info(f"Inserted row with id: {row_id}")
            stop = data.get('stop')
        prev = data
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

def on_error(ws, error):
    logging.error(error)

def on_close(ws, close_status_code, close_msg):
    logging.info("### closed ###")

def on_open(ws):
    logging.info("Opened connection")

if __name__ == "__main__":
#    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://internet-roadtrip-listen-eqzms.ondigitalocean.app/",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
