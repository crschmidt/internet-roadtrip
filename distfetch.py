import csv
import time
import requests

# Constants
API_ENDPOINT = "https://roadtrip.pikarocks.dev/query"
TOTAL_RECORDS_TO_FETCH = 140000
SAMPLE_INTERVAL = 200
INITIAL_START_TIME = 1747527000
FETCH_LIMIT = 1


def fetch_data(start_time, offset, limit):
  """Fetches data from the API and returns timestamp and distance.

  Args:
      start_time: The start time for the query.
      offset: The offset for the query.
      limit: The limit for the query.

  Returns:
      A tuple containing the timestamp and distance, or (None, None) if the
      request fails or no results are found.
  """
  params = {
      "limit": limit,
      "offset": offset,
      "startTime": start_time,
      "endTime": start_time + 44,  # 44 seconds after start time
  }
  try:
    response = requests.get(API_ENDPOINT, params=params)
    response.raise_for_status()  # Raise an exception for bad status codes
    data = response.json()
    if "results" in data and data["results"]:
      record = data["results"][0]
      return (
          record["timestamp"],
          record["distance"],
          record["lat"],
          record["lng"],
      )
    else:
      return None, None
  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    return None, None


if __name__ == "__main__":
  results = []
  previous_timestamp = None
  previous_distance = None
  for i in range(TOTAL_RECORDS_TO_FETCH // SAMPLE_INTERVAL):
    offset = i * SAMPLE_INTERVAL
    start_time = INITIAL_START_TIME + offset
    timestamp, distance, lat, lng = fetch_data(start_time, offset, FETCH_LIMIT)
    if timestamp is not None and distance is not None:
      if previous_timestamp is not None and previous_distance is not None:
        time_diff_seconds = timestamp - previous_timestamp
        distance_delta = distance - previous_distance
        time_diff_hours = abs(time_diff_seconds / 3600.0)
        if time_diff_hours > 0:  # Avoid division by zero
          mph = (previous_distance - distance) / time_diff_hours
          print(
              f"Fetched record {i*SAMPLE_INTERVAL}: timestamp={timestamp},"
              f" distance={distance:.2f} miles, mph={mph:.2f}"
          )
          results.append((timestamp, distance, mph, lat, lng))
        else:
          print(
              f"Fetched record {i*SAMPLE_INTERVAL}: timestamp={timestamp},"
              f" distance={distance:.2f} miles, time difference too small to"
              " compute mph."
          )
      else:
        print(
            f"Fetched record {i*SAMPLE_INTERVAL}: timestamp={timestamp},"
            f" distance={distance:.2f} miles"
        )
      previous_timestamp = timestamp
      previous_distance = distance
    else:
      print(f"No record found for offset {offset} and start_time {start_time}")
    time.sleep(0.1)  # Add a small delay to avoid overloading the API

  print("\nAll Fetched Results:")
  # Write results to CSV
  with open("fetched_results.csv", "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["timestamp", "distance", "mph", "lat", "lng"])
    for timestamp, distance, mph, lat, lng in results:
      csv_writer.writerow([timestamp, distance, mph, lat, lng])

  print("\nFetched results written to fetched_results.csv")
