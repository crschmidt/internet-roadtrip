import json
import math
import sys
import requests
import haversine
import keys

# https://console.cloud.google.com/google/maps-apis/credentials
API_KEY = keys.API_KEY
# curl -X POST https://tile.googleapis.com/v1/createSession?mapType=streetview&key=API_KEY
SESSION_KEY = keys.SESSION_KEY

def main(pano, heading, search_dist=13):
    #print("hi")
    predicted = predict_options(pano_id, heading, search_dist=search_dist, lat=None, lng=None)
    print(f"Predicted options for {pano_id} heading {heading}:")
    for option in predicted:
        print(f"  {json.dumps(option)}")


def predict_options(cur_pano_id: str, cur_heading: float, search_dist: float = 13, lat=None, lng=None):
    cur_lat = lat
    cur_lng = lng
    metadata = get_metadata(cur_pano_id)
    if not cur_lat:
      #if 
      #cur_lat = metadata.get("lat", 0)# or metadata["originalLat"]
      #cur_lng = metadata.get("lng", 0)# or metadata["originalLng"]
      if cur_pano_id.startswith("CAoSF"):
        cur_lat = metadata.get("lat",0)# or metadata.get("lat",0)
        cur_lng = metadata.get("lng",0)# or metadata.get("lng",0)
      else:
        cur_lat = metadata.get("originalLat") or metadata.get("lat",0)
        cur_lng = metadata.get("originalLng") or metadata.get("lng",0)

    predicted = []
    seen_pano_ids = set()
    seen_pano_ids.add(cur_pano_id)
    seen_headings = []

    checked_count = 0

    for link in metadata.get("links") or []:
        seen_pano_ids.add(link["panoId"])
        heading_offset = calculate_heading_offset(cur_heading, link["heading"])
        checked_count += 1
        if abs(heading_offset) < 100:
            data = {
                # these descriptions don't always match, for example pano id MYW4wuG31GTE35s6sjyh7g
                # (linked by O2zQFftY5qskX032Rv0L3Q) says "State Rte 9" in-game but "Main St" from this api
                # "description": link["text"],
                #
                # the real game converts these headings to 32 bit floats for some reason?
                "heading": link["heading"],
                "pano": link["panoId"],
            }
            predicted.append(data)
            seen_headings.append(link["heading"])

    heading_offsets = (0, -45, 45, 90, -90)

#    print (cur_lat, cur_lng)
    locations = []
    for heading_offset in heading_offsets:
        locations.append(
            haversine.inverse_haversine(
                (cur_lat, cur_lng),
                search_dist,
                math.radians(normalize_heading(cur_heading) + heading_offset),
                unit=haversine.Unit.METERS,
            )
        )

    #print(locations)

    extra_pano_ids = get_pano_ids(locations, 50)
    #print(extra_pano_ids)
    for option_pano_id in extra_pano_ids:
        if not option_pano_id or option_pano_id in seen_pano_ids:
            continue
        seen_pano_ids.add(option_pano_id)

        option_metadata = get_metadata(option_pano_id)

        if option_pano_id.startswith("CAoSF"):
          option_lat = option_metadata.get("lat",0)# or option_metadata.get("lat",0)
          option_lng = option_metadata.get("lng",0)# or option_metadata.get("lng",0)
        else:
          option_lat = option_metadata.get("originalLat") or option_metadata.get("lat",0)
          option_lng = option_metadata.get("originalLng") or option_metadata.get("lng",0)

        if not option_lat:
          print("Invalid pano location? Stop: %s Pano: %s \n %s" % (cur_pano_id, option_pano_id, option_metadata))

        option_heading = calculate_heading(
            (cur_lat, cur_lng),
            (option_lat, option_lng),
        )
        heading_offset = calculate_heading_offset(cur_heading, option_heading)
        if abs(heading_offset) > 100:
            #print("Pano %s in wrong direction, %s" % (option_pano_id, heading_offset))
            continue

        # filter if the heading is too close to another heading
        too_close_to_other_heading = False
        for seen_heading in seen_headings:
            calculate_heading_offset(seen_heading, option_heading)
            if abs(calculate_heading_offset(seen_heading, option_heading)) < 15:
                too_close_to_other_heading = True
                #print("Pano %s heading %s too close to %s, %s, %s" % (option_pano_id, option_heading, seen_heading, option_lat, option_lng))
                break
        if too_close_to_other_heading:
            continue
        seen_headings.append(option_heading)

        data = {
            "pano": option_pano_id,
            # unknown where to get the description from
            # "description": "",
            "heading": option_heading,
            "lat": option_metadata.get("lat", 0),
            "lng": option_metadata.get("lng", 0),
        }
        predicted.append(data)

    return predicted


def calculate_heading_offset(a: float, b: float) -> float:
    return normalize_heading(b - a)


def normalize_heading(heading: float) -> float:
    if heading > 180:
        heading -= 360
    elif heading < -180:
        heading += 360
    return heading


def get_metadata(pano_id: str) -> dict:
    res = requests.get(
        f"https://tile.googleapis.com/v1/streetview/metadata?session={SESSION_KEY}&key={API_KEY}&panoId={pano_id}"
    )
    data = res.json()
    if not 'lat' in data:
      print("Broken metadata? %s: \n %s" % (pano_id, data))
    return data


def get_pano_ids(locations: list, radius: float) -> list[str]:
    requesting_locations = [{"lat": loc[0], "lng": loc[1]} for loc in locations]
    res = requests.post(
        f"https://tile.googleapis.com/v1/streetview/panoIds?session={SESSION_KEY}&key={API_KEY}",
        json={"locations": requesting_locations, "radius": radius},
    )
    data = res.json()
    if not 'panoIds' in data:
      print("bad data?", data)
    return data["panoIds"]


def calculate_heading(start: tuple[float, float], end: tuple[float, float]) -> float:
    # based on https://gist.github.com/jeromer/2005586
    lat1 = math.radians(start[0])
    lat2 = math.radians(end[0])
    diff_lng = math.radians(end[1] - start[1])
    x = math.sin(diff_lng) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (
        math.sin(lat1) * math.cos(lat2) * math.cos(diff_lng)
    )
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    return (initial_bearing + 360) % 360


if __name__ == "__main__":
    if len(sys.argv) < 3:
      print("Usage: python internet_roadtrip_panos.py <pano_id> <heading> [<distance>]")
      sys.exit(1)

    pano_id, heading = sys.argv[1], float(sys.argv[2])
    if len(sys.argv) > 3:
      main(pano_id, heading, float(sys.argv[3]))
    else:
      main(pano_id, heading)
