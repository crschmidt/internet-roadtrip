import json
import random
import sys
import requests
import keys

url = "https://tile.googleapis.com/v1/streetview/metadata"

# Base parameters for the API request, session and key are from your example
base_params = {
    "session": (
        keys.SESSION_KEY
    ),
    "key": keys.API_KEY,
}

# Global set to keep track of panos whose data has been fetched and processed
# This prevents re-fetching and re-exploring from the same pano multiple times.
processed_pano_ids = set()
geojson_features = []  # To store GeoJSON LineString features

# List of distinct RGB colors
color_palette = [
    "#e6194B",
    "#3cb44b",
    "#ffe119",
    "#4363db",
    "#f58231",
    "#911eb4",
    "#46f0f0",
    "#f032e6",
    "#bcf60c",
    "#fabebe",
    "#008080",
    "#e6beff",
    "#9A6324",
    "#fffac8",
    "#800000",
    "#aaffc3",
    "#808000",
    "#ffd8b1",
    "#000075",
    "#808080",
    "#ffffff",
    "#000000",
]
color_index = 0
MAX_DEPTH = 300  # Remains as per your existing code


def build_lines_recursive(
    pano_id_to_process, current_depth, accumulated_path_nodes
):
  global color_index

  # accumulated_path_nodes is a list of tuples: [([lng, lat], pano_id), ...]

  # Termination Condition 1: Max depth reached for pano_id_to_process
  if current_depth > MAX_DEPTH:
    if len(accumulated_path_nodes) >= 2:
      coords = [node[0] for node in accumulated_path_nodes]
      ids = [node[1] for node in accumulated_path_nodes]
      feature = {
          "type": "Feature",
          "geometry": {"type": "LineString", "coordinates": coords},
          "properties": {
              "panoIds": ids,
              "stroke": color_palette[color_index],
              "stroke-width": 10,
          },
      }
      if feature not in geojson_features:
        geojson_features.append(feature)
      color_index = (color_index + 1) % len(color_palette)
    return

  # Termination Condition 2: pano_id_to_process has already been processed.
  # The current path leading up to it is a complete line segment.
  if pano_id_to_process in processed_pano_ids:
    if len(accumulated_path_nodes) >= 2:

      coords = [node[0] for node in accumulated_path_nodes]
      ids = [node[1] for node in accumulated_path_nodes]
      feature = {
          "type": "Feature",
          "geometry": {"type": "LineString", "coordinates": coords},
          "properties": {"panoIds": ids, "stroke-width": 10},
      }
      if feature not in geojson_features:
        geojson_features.append(feature)
    return

  processed_pano_ids.add(pano_id_to_process)

  current_params = base_params.copy()
  current_params["panoId"] = pano_id_to_process
  data = None
  try:
    r = requests.get(url, params=current_params)
    r.raise_for_status()
    data = r.json()
  except requests.exceptions.RequestException as e:
    print(f"Error fetching data for pano {pano_id_to_process}: {e}", e.response.json())
  except ValueError as e:  # Includes JSONDecodeError
    print(f"Error decoding JSON for pano {pano_id_to_process}: {e}")
  if data is None:  # API call failed or JSON decoding failed
    if len(accumulated_path_nodes) >= 2:  # Save path so far
      coords = [node[0] for node in accumulated_path_nodes]
      ids = [node[1] for node in accumulated_path_nodes]
      feature = {
          "type": "Feature",
          "geometry": {"type": "LineString", "coordinates": coords},
          "properties": {
              "panoIds": ids,
              "stroke": color_palette[color_index],
              "stroke-width": 10,
          },
      }
      if feature not in geojson_features:
        geojson_features.append(feature)
      color_index = (color_index + 1) % len(color_palette)
      if feature not in geojson_features:
        geojson_features.append(feature)
    return

  lat = data.get("lat")
  lng = data.get("lng")
  links_api = data.get("links", [])
  if lat is None or lng is None:
    print(f"Warning: No lat/lng for pano {pano_id_to_process}. Data: {data}")
    if len(accumulated_path_nodes) >= 2:  # Save path so far
      coords = [node[0] for node in accumulated_path_nodes]
      ids = [node[1] for node in accumulated_path_nodes]
      feature = {
          "type": "Feature",
          "geometry": {"type": "LineString", "coordinates": coords},
          "properties": {
              "panoIds": ids,
              "stroke": color_palette[color_index],
              "stroke-width": 10,
          },
      }
      if feature not in geojson_features:
        geojson_features.append(feature)
      color_index = (color_index + 1) % len(color_palette)
      if feature not in geojson_features:
        geojson_features.append(feature)
    return
  print(data['date'])
  link_ids = [link.get("panoId") for link in links_api]
  # Current pano is valid, print its info
  print(f"PanoID: {pano_id_to_process}, Lat: {lat}, Lng: {lng}, \n  Links: {link_ids}")

  # Path extended with the current pano's data
  current_node_data = ([lng, lat], pano_id_to_process)
  new_accumulated_path = accumulated_path_nodes + [current_node_data]

  explorable_linked_pano_ids = []
  if isinstance(links_api, list):
    for link in links_api:
      linked_pano_id = link.get("panoId")
      # Explore link if it has a panoId AND it hasn't been processed globally yet
      if linked_pano_id and linked_pano_id not in processed_pano_ids:
        explorable_linked_pano_ids.append(linked_pano_id)

  if not explorable_linked_pano_ids:
    # This node is a terminal node for new exploration.
    # The new_accumulated_path (including current node) is a complete line.
    if len(new_accumulated_path) >= 2:
      coords = [node[0] for node in new_accumulated_path]
      ids = [node[1] for node in new_accumulated_path]
      feature = {
          "type": "Feature",
          "geometry": {"type": "LineString", "coordinates": coords},
          "properties": {
              "panoIds": ids,
              "stroke": color_palette[color_index],
              "stroke-width": 10,
          },
      }
      if feature not in geojson_features:
        geojson_features.append(feature)
      color_index = (color_index + 1) % len(color_palette)
      if feature not in geojson_features:
        geojson_features.append(feature)
    return

  # Branch out: for each explorable_linked_pano_id, make a recursive call
  for next_pano_id in explorable_linked_pano_ids:
    # Pass a copy of the new_accumulated_path for each new branch
    build_lines_recursive(
        next_pano_id, current_depth + 1, list(new_accumulated_path)
    )


# Initial panorama ID from your example
initial_pano_id = sys.argv[1] #(  # Make sure this is the desired start
#    "KGOB4Z-fiYK1C7OkrQc4yw"
#)
geojson_features.clear()  # Ensure lists are empty for a fresh run
processed_pano_ids.clear()
color_index = 0  # Reset the color index

print(
    f"Starting scrape from PanoID: {initial_pano_id} up to {MAX_DEPTH} levels"
    " deep to build LineStrings."
)
# Initial call to the recursive function. Depth 0, empty path.
build_lines_recursive(initial_pano_id, 0, [])

# Create the GeoJSON FeatureCollection
geojson_output = {"type": "FeatureCollection", "features": geojson_features}

# Write the GeoJSON data to output.geojson
output_filename = "output.geojson"
with open(output_filename, "w") as f:
  json.dump(geojson_output, f, indent=2)  # indent for pretty printing

print(f"GeoJSON LineString data written to {output_filename}")
# The user's original comment with the example JSON response is omitted for brevity.
