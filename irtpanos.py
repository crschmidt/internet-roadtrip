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
#    print("calculate_heading: %f, %f, %f, %f" % (lat1, lon1, lat2, lon2))
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
OFFSET_DISTANCE = 15 # Distance forward in meters

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
        
        return list(set([pano_id for pano_id in data.get("panoIds") if pano_id != '']))
    except requests.exceptions.RequestException as e:
        print(e.response)
        print(f"Error during API request: {e}", e.response.json())
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

def safe_heading(start_heading, heading):
  """
  Determine if the heading is in the range of -100 to 100 degrees from the start heading.
  Args:
      start_heading: The starting heading.
      heading: The heading to check.
  Returns:
      True if the heading is in the range of -100 to 100 degrees from the start heading, False otherwise.
  
  Test cases:
  1. start_heading = 10, heading = -10: True
  2. start_heading = 350, heading = 10: True
  3. start_heading = 350, heading = 220: False
  """
  heading_diff = (heading - start_heading + 360) % 360
  return heading_diff <= 100 or heading_diff >= 260



def get_second(pano_id, start_pano):
  data = get_pano_metadata(pano_id)
  options = []
  if data.get("links"):
    for link in data.get("links"):
      
      if link.get("panoId") == start_pano:
        continue
      options.append(link.get("panoId"))
  if len(options) > 1:
    return []
  if len(options) == 0:
    return []
  return options[0]

def repro_irt(start_pano_id, start_heading, start_lat=None, start_lon=None):
    linked_panos = []
    # Fetch metadata for the starting pano to get its lat/lon
    if start_pano_id:
      start_metadata = get_pano_metadata(start_pano_id)
      if not start_metadata:
        print(f"Could not retrieve metadata for starting PanoID {start_pano_id}.")
        sys.exit(1)
      print(start_metadata)
      if not start_lat and not start_lon:
        start_lat = start_metadata.get("originalLat")
        start_lon = start_metadata.get("originalLng")
        if not start_lat or not start_lon:
          start_lat = start_metadata.get("lat")
          start_lon = start_metadata.get("lng")
      linked_panos = start_metadata.get("links", [])
    
    if start_lat is None or start_lon is None:
      print(f"Could not retrieve lat/lon for starting PanoID {start_pano_id}.")
      sys.exit(1)
    linked_locations = {}
    # Add linked panos to the list of locations
    locations = []
    pano_headings = {}
    for link in linked_panos:
        if "panoId" in link and "heading" in link:
          linked_pano_id = link["panoId"]
          linked_pano_heading = link["heading"]
          linked_locations[linked_pano_id] = linked_pano_heading
          pano_headings[linked_pano_id] = linked_pano_heading
    # Define the angles for the forward locations
    angles = [0, -45, 45, 90, -90]
    for angle in angles:
        new_heading = start_heading + angle
        new_lat, new_lon = inverse_haversine(start_lat, start_lon, new_heading, OFFSET_DISTANCE)
        locations.append({"lat": new_lat, "lng": new_lon})
    # Make the PanoID API request
    pano_ids_per_angle = get_pano_ids(locations)
    print(pano_ids_per_angle)
    #print(pano_ids_per_angle)
    # Deduplicate PanoIDs
    if pano_ids_per_angle:
      unique_pano_ids = set(pano_ids_per_angle+list(linked_locations.keys()))
    else:
      unique_pano_ids = set()

    # Print the results
    if unique_pano_ids:
        for pano_id in unique_pano_ids:
            if pano_id == start_pano_id:
                continue
            if pano_id in linked_locations: continue
            print("Fetching metadata for pano %s" % pano_id)
            metadata = get_pano_metadata(pano_id)
            #print(metadata)
            if metadata:
                pano_lat = metadata.get("originalLat") or metadata.get("lat")
                pano_lon = metadata.get("originalLng") or metadata.get("lng")
                if pano_lat is not None and pano_lon is not None:
                  heading = calculate_heading(start_lat, start_lon, pano_lat, pano_lon)
                  pano_headings[pano_id] = heading
    else:
      print("No PanoIDs found or error during request.")
    allowed_options = []
    for pano, heading in pano_headings.items():
      if safe_heading(start_heading, heading):
        print("Pano %s with heading %f is the right direction." % (pano, heading))
        allowed_options.append((pano, heading))
      else:
        print("Skipping pano %s with heading %f" % (pano, heading))
    if len(allowed_options) == 1:
      print("There is only one option")
      skip = get_second(allowed_options[0][0], start_pano_id)
      print("Would (maybe?) skip to: %s" % skip)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python irtpanos.py <pano_id> <heading>")
        sys.exit(1)

    start_pano_id = sys.argv[1]
#    start_pano_id= None
    start_heading = float(sys.argv[2])
    start_lat = None
    start_lon = None
    if len(sys.argv) > 3:
      start_lat, start_lon = float(sys.argv[3]), float(sys.argv[4])
    repro_irt(start_pano_id, start_heading, start_lat, start_lon)
    print(calculate_heading(46.149727169237636, -67.22092450562987, 46.149760269473916, -67.220834990240547))
