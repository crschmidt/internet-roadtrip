import requests
import math
import json
import sys
import keys

def calculate_heading(lat1, lon1, lat2, lon2):
    """
    Calculates the heading (bearing) from point 1 to point 2.
    Args:
        lat1: Latitude of point 1 in degrees.
        lon1: Longitude of point 1 in degrees.
        lat2: Latitude of point 2 in degrees.
        lon2: Longitude of point 2 in degrees.
    Returns:
        Heading in degrees (0=North, 90=East, 180=South, 270=West).
    """
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    delta_lon = lon2_rad - lon1_rad
    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    heading_rad = math.atan2(y, x)
    heading_deg = math.degrees(heading_rad)
    return (heading_deg + 360) % 360
# API Constants
API_URL = "https://tile.googleapis.com/v1/streetview/panoIds"
METADATA_API_URL = "https://tile.googleapis.com/v1/streetview/metadata"
SESSION_KEY = keys.SESSION_KEY
API_KEY = keys.API_KEY
RADIUS = 20 # Radius for PanoID search in meters
OFFSET_DISTANCE = 13 # Distance forward in meters

def inverse_haversine(lat, lon, heading, distance):
    """
    Calculates the destination coordinates given a starting point, distance, and heading.
    Args:
        lat: Starting latitude in degrees.
        lon: Starting longitude in degrees.
        heading: Heading in degrees (0=North, 90=East, 180=South, 270=West).
        distance: Distance in meters.
    Returns:
        Tuple of (destination_lat, destination_lon) in degrees.
    """
    R = 6371000  # Earth radius in meters
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    heading_rad = math.radians(heading)
    distance_ratio = distance / R

    destination_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance_ratio) +
        math.cos(lat_rad) * math.sin(distance_ratio) * math.cos(heading_rad)
    )
    destination_lon_rad = lon_rad + math.atan2(
        math.sin(heading_rad) * math.sin(distance_ratio) * math.cos(lat_rad),
        math.cos(distance_ratio) - math.sin(lat_rad) * math.sin(destination_lat_rad)
    )

    return math.degrees(destination_lat_rad), math.degrees(destination_lon_rad)

def get_pano_ids(locations):
    """
    Makes a request to the PanoIDs API for a list of locations.
    Args:
        locations: A list of dictionaries with 'lat' and 'lng' keys.
    Returns:
        A list of PanoIDs, or None if the request fails.
    """
    params = {
        "session": SESSION_KEY,
        "key": API_KEY
    }
    payload = {
        "locations": locations,
        "radius": RADIUS
    }
    try:
        r = requests.post(API_URL, params=params, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        r.raise_for_status()
        data = r.json()
        return data.get("panoIds")
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None

def get_pano_metadata(pano_id):
    """
    Makes a request to the metadata API for a given PanoID.
    Args:
        pano_id: The PanoID to fetch metadata for.
    Returns:
        The metadata dictionary, or None if the request fails.
    """
    params = {
        "session": SESSION_KEY,
        "key": API_KEY,
        "panoId": pano_id
    }
    try:
        r = requests.get(METADATA_API_URL, params=params)
        r.raise_for_status()
        data = r.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching metadata for pano {pano_id}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python irtpanos.py <pano_id> <heading>")
        sys.exit(1)

    start_pano_id = sys.argv[1]
    start_heading = float(sys.argv[2])

    # Fetch metadata for the starting pano to get its lat/lon
    start_metadata = get_pano_metadata(start_pano_id)
    if not start_metadata:
        print(f"Could not retrieve metadata for starting PanoID {start_pano_id}.")
        sys.exit(1)
    start_lat = start_metadata.get("lat")
    start_lon = start_metadata.get("lng")
    if start_lat is None or start_lon is None:
      print(f"Could not retrieve lat/lon for starting PanoID {start_pano_id}.")
      sys.exit(1)

    # Define the angles for the forward locations
    angles = [0, -45, 45, 90, -90]
    locations = []
    for angle in angles:
        new_heading = start_heading + angle
        new_lat, new_lon = inverse_haversine(start_lat, start_lon, new_heading, OFFSET_DISTANCE)
        locations.append({"lat": new_lat, "lng": new_lon})

    # Make the PanoID API request
    pano_ids_per_angle = get_pano_ids(locations)

    # Deduplicate PanoIDs
    if pano_ids_per_angle:
      unique_pano_ids = set(pano_ids_per_angle)
    else:
      unique_pano_ids = set()

    # Print the results
    if unique_pano_ids:
        for pano_id in unique_pano_ids:
            metadata = get_pano_metadata(pano_id)
            if pano_id == start_pano_id:
              continue
            if metadata:
                pano_lat = metadata.get("lat")
                pano_lon = metadata.get("lng")
                if pano_lat is not None and pano_lon is not None:
                  heading = calculate_heading(start_lat, start_lon, pano_lat, pano_lon)
                  print(f"PanoID: {pano_id}, Heading: {heading:.2f} degrees")
                else:
                  print(f"Could not retrieve lat/lon for PanoID {pano_id}.")
            else:
                print(f"No metadata found for PanoID {pano_id}.")
    else:
        print("No PanoIDs found or error during request.")
