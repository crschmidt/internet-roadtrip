import json
import csv
import os
import requests

def extract_and_write_csv(input_file, output_file):
    """
    Extracts data from a JSON file and writes it to a CSV file.

    Args:
        input_file: Path to the input JSON file.
        output_file: Path to the output CSV file.
    """
    try:
        with open(input_file, 'r') as f:
            items = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{input_file}'.")
        return

    if not isinstance(items, list):
      print(f"Error: Invalid JSON format in '{input_file}', expected a list.")
      return

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['id', 'title', 'placename', 'lat', 'lng', 'country', 'preroll', 'secure', 'website', 'streaming_url'])
        i = 0
        for item in items:
            i += 1
            try:
                url = item['page']['url']
                item_id = url.split('/')[-1]
                placename = item['page']['place']['title']
                lat = item['page']['place']['lat']
                lng = item['page']['place']['lng']
                country = item['page']['country']['title']
                website = item['page']['website']
                title = item['page']['title']
                preroll = item['page']['preroll']
                secure = item['page']['secure']
                
                # Fetch streaming URL
                stream_url = f"/api/ara/content/listen/{item_id}/channel.mp3?1748180090815"
                base_url = "https://radio.garden"
                try:
                  response = requests.get(base_url + stream_url, allow_redirects=False, timeout=3)
                  response.raise_for_status()
                  streaming_url = response.headers.get('Location')
                except requests.exceptions.RequestException as e:
                  print(f"Error fetching streaming URL for ID {item_id}: {e}")
                  streaming_url = None
                except requests.exceptions.Timeout:
                  print(f"Timeout fetching streaming URL for ID {item_id}")
                  streaming_url = None
                csv_writer.writerow([item_id, title, placename, lat, lng, country, preroll, secure, website,  streaming_url])
            except KeyError as e:
                print(f"Skipping item due to missing key: {e}, item: {item}")
                continue
            if i % 50 == 0:
                print(f"Fetched {i} items")

if __name__ == "__main__":
    input_file = 'items.json'
    output_file = 'output.csv'
    extract_and_write_csv(input_file, output_file)
    print(f"Data extracted and written to '{output_file}'")