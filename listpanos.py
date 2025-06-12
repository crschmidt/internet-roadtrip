import json
import keys
import requests
import internet_roadtrip_panos
import havdist
API_URL = "https://tile.googleapis.com/v1/streetview/panoIds"
METADATA_API_URL = "https://tile.googleapis.com/v1/streetview/metadata"
SESSION_KEY = keys.SESSION_KEY
API_KEY = keys.API_KEY
RADIUS = 8 # Radius for PanoID search in meters
OFFSET_DISTANCE = 13 # Distance forward in meters

def run(locations):
    payload = {
        "locations": locations,
        "radius": RADIUS
    }
    params = {
        "session": SESSION_KEY,
        "key": API_KEY
    }
    fc = []
    try:
        r = requests.post(API_URL, params=params, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        r.raise_for_status()
        data = r.json()
        
        md = {}
        for i, panoid in enumerate(data['panoIds']):
          if panoid.startswith('CAoS'): # UGC
            if not panoid in md:
              mddata = internet_roadtrip_panos.get_metadata(panoid)
              if data.get('lat') and data.get('lng'):
                md[panoid] = internet_roadtrip_panos.get_metadata(panoid)
              else: print("broken?", data)
        print(len(md))
        for i, panoid in enumerate(data['panoIds']):
          if panoid.startswith('CAoS'):
            if not panoid in md: continue
            sloc = [locations[i]['lat'], locations[i]['lng']]
            dloc = [md[panoid]['lat'], md[panoid]['lng']]
            dist = havdist.calculate_distance(sloc[0], sloc[1], dloc[0], dloc[1])
            print(panoid, dist)
            if (dist > 10):
              fc.append({"type":"Feature", "geometry": {"type":"Point", "coordinates": [locations[i]['lng'], locations[i]['lat']]}, "properties": {"marker-color":"red", "panoid": panoid, 'dist': dist}})
        print(json.dumps({"type":"FeatureCollection", "features": fc}))
        return list(set([pano_id for pano_id in data.get("panoIds") if pano_id != '']))
    except requests.exceptions.RequestException as e:
        print(e.response)
        print(f"Error during API request: {e}", e.response.json())
        return None
if __name__ == "__main__":
  base = {"lat":44.64798487902375, 'lng':-63.57966749553362}
  items = []
  for i in range(-5, 5):
    for j in range(-5, 5):
      item = {'lat': base['lat']+(i*.0001), 'lng': base['lng']+(j*.0001)}
      items.append(item)
  run(items)
