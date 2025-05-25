import json
import requests

def extract_ids_within_bounds(json_data_string, min_lat, min_lng, max_lat, max_lng):
    """
    Extracts IDs from a JSON dataset where the geo coordinates are within specified bounds.

    Args:
        json_data_string: A string containing the JSON data.
        min_lat: The minimum latitude.
        min_lng: The minimum longitude.
        max_lat: The maximum latitude.
        max_lng: The maximum longitude.

    Returns:
        A list of dicts with id, lat and lng where the geo coordinates are within the bounds.
    """
    try:
        data = json.loads(json_data_string)
    except json.JSONDecodeError:
        return [] # Or raise an exception, depending on the desired behavior.

    if 'data' not in data or 'list' not in data['data']:
      return []

    extracted_ids = []
    for item in data['data']['list']:
        if 'geo' in item and len(item['geo']) == 2:
            lng, lat = item['geo']
            if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                extracted_ids.append({'id': item['id'], 'lat': lat, 'lng': lng})
    return extracted_ids

def fetch_and_extract_items(id_dicts):
    """
    Fetches details for given IDs and extracts items from the response.
    Adds lat/lon to each item.

    Args:
        id_dicts: A list of dicts with id, lat and lng.

    Returns:
        A list of items.
    """
    all_items = []
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
    i = 0
    for id_dict in id_dicts:
      i += 1
      id = id_dict['id']
      lat = id_dict['lat']
      lng = id_dict['lng']
      url = f"https://radio.garden/api/ara/content/secure/page/{id}/channels"
      try:
          response = requests.get(url, headers={'User-Agent': user_agent})
          response.raise_for_status()  # Raise an exception for bad status codes
          data = response.json()
          if 'data' in data and 'content' in data['data'] and data['data']['content'] and 'items' in data['data']['content'][0]:
              for item in data['data']['content'][0]['items']:
                if not 'place' in item['page']: 
                    print("Huh?", item)
                    continue
                item['page']['place']['lat'] = lat
                item['page']['place']['lng'] = lng
                all_items.append(item)
      except requests.exceptions.RequestException as e:
          print(f"Error fetching data for ID {id}: {e}")
      except json.JSONDecodeError as e:
          print(f"Error decoding JSON for ID {id}: {e}")
      if i % 10 == 0:
        print(f"Fetched {i} items")
    return all_items

# Example usage:
if __name__ == "__main__":
    json_data_string = """
    {
        "apiVersion": 0,
        "version": "a5229bf",
        "data": {
            "version": "a5229bf",
            "list": [
                {
                    "size": 2,
                    "id": "5FoTpHlo",
                    "geo": [
                        -46.04898,
                        -19.310768
                    ],
                    "boost": false
                },
                {
                    "size": 2,
                    "id": "valid_id_1",
                    "geo": [
                        20.0,
                        -50.0
                    ],
                    "boost": false
                },
                 {
                    "size": 2,
                    "id": "valid_id_2",
                    "geo": [
                        50.0,
                        -40.0
                    ],
                    "boost": false
                },
                {
                    "size": 2,
                    "id": "invalid_id",
                    "geo": [
                        60.0,
                        -20.0
                    ],
                    "boost": false
                }
            ]
        }
    }
    """
    min_lat = 18.48484891360567
    min_lng = -130.9970134066682
    max_lat = 58.04894776618935
    max_lng = -37.51062476447251

    # ids = extract_ids_within_bounds(json_data_string, min_lat, min_lng, max_lat, max_lng)
    # print(f"IDs within bounds: {ids}")

    # Example of how to load from a file:
    with open('radiogarden.json', 'r') as f:
      json_data_string = f.read()
      id_dicts = extract_ids_within_bounds(json_data_string, min_lat, min_lng, max_lat, max_lng)
      first_5_ids = id_dicts
      print(len(id_dicts))
      items = fetch_and_extract_items(first_5_ids)
      json.dump(items, open('items.json', 'w'))
      print(f"Wrote {len(items)} items to items.json")

