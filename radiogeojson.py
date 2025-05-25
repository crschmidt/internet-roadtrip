import csv
import json
import math

def read_csv_data(file_path):
    """Reads data from a CSV file and returns a list of dictionaries."""
    data = []
    # Define the headers for the CSV file
    headers = ["name", "geolat", "geolong", "language", "tags", "Hls", "Url"]
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            if len(row) != len(headers):
                print(f"Warning: Skipping row with invalid number of columns: {row}")
                continue
            row_dict = dict(zip(headers, row))
            data.append(row_dict)
    return data


def create_geojson_feature(row):
    """Creates a GeoJSON polygon feature (approx. circle) from a row dictionary."""
    try:
      lng = float(row['geolong'])
      lat = float(row['geolat'])
    except ValueError:
      print(f"Warning: invalid geolat/geolong values for row: {row}. Skipping")
      return None
    
    # Radius of the circle in kilometers
    radius_km = 100
    
    # Approximate conversion of km to degrees (simplified)
    radius_lat_deg = radius_km / 111.0  # 1 degree of latitude is approx 111 km
    radius_lng_deg = radius_km / (111.0 * math.cos(math.radians(lat))) # adjust for latitude

    # Number of vertices for the polygon
    num_vertices = 36
    
    # Generate vertices
    vertices = []
    for i in range(num_vertices):
        angle_rad = 2 * math.pi * i / num_vertices
        
        # Calculate vertex coordinates
        vertex_lat = lat + radius_lat_deg * math.sin(angle_rad)
        vertex_lng = lng + radius_lng_deg * math.cos(angle_rad)
        
        vertices.append([vertex_lng, vertex_lat])
    
    # Close the polygon by adding the first vertex again
    vertices.append(vertices[0])

    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [vertices]
        }
        ,"properties": {
            "name": row.get("name"),
            "language": row.get("language"),
            "tags": row.get("tags"),
            "url": row.get("Url"),
            "fill-opacity": 0.0,
            'stroke-color': '#000000'
        }
    }
    if row.get("Hls") == "1" or row.get("Url").startswith("http:"):
        feature["properties"]["broken"] = True
        feature['properties']['stroke'] = '#ff0000'
    return feature

if __name__ == "__main__":
    def is_within_bounding_box(lat, lng, min_lat=18.48484891360567, min_lng=-130.9970134066682, max_lat=58.04894776618935, max_lng=-37.51062476447251):
      """Checks if a station's coordinates are within the bounding box."""
      return min_lat <= lat <= max_lat and min_lng <= lng <= max_lng


    csv_file_path = "geostations.csv"
    geojson_output_file = "geostations.geojson"

    # Read the CSV data
    data = read_csv_data(csv_file_path)

    # Create GeoJSON features
    geojson_features = []
    for row in data:
        try:
          lng = float(row['geolong'])
          lat = float(row['geolat'])
        except ValueError:
          print(f"Warning: invalid geolat/geolong values for row: {row}. Skipping")
          continue
        if is_within_bounding_box(lat, lng):
          feature = create_geojson_feature(row)
          if feature:
            geojson_features.append(feature)
        else:
          print(f"Warning: Skipping station {row['name']} because it is outside the bounding box.")

    # Create the GeoJSON FeatureCollection
    geojson_output = {
        "type": "FeatureCollection",
        "features": geojson_features
    }

    # Write the GeoJSON data to a file
    with open(geojson_output_file, "w", encoding='utf-8') as f:
        json.dump(geojson_output, f, indent=2)

    print(f"GeoJSON data written to {geojson_output_file}")