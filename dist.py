import math
import json
import random
import sys
import requests
import keys

# ... existing code ...

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points on Earth (specified in decimal degrees).

    Args:
        lat1: Latitude of the first point.
        lon1: Longitude of the first point.
        lat2: Latitude of the second point.
        lon2: Longitude of the second point.

    Returns:
        The distance between the two points in meters.
    """
    R = 6371000  # Radius of Earth in meters
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def calculate_planar_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the planar distance between two points, treating lat/lon as x/y coordinates.

    Args:
        lat1: Latitude of the first point.
        lon1: Longitude of the first point.
        lat2: Latitude of the second point.
        lon2: Longitude of the second point.

    Returns:
        The planar distance between the two points in meters.
    """
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Approximate meters per degree of latitude and longitude
    meters_per_lat_degree = 100000  # Approximate meters per degree of latitude
    avg_lat = (lat1 + lat2) / 2
    meters_per_lon_degree = 100000 * math.cos(math.radians(avg_lat))

    distance_meters = math.sqrt((dlat * meters_per_lat_degree)**2 + (dlon * meters_per_lon_degree)**2)
    return distance_meters

# Example usage with your coordinates
coord1_lat = 45.27510085513047
coord1_lon = -66.05780303478242
coord2_lat = 45.00861622547305
coord2_lon = -67.4333853578659

distance_meters = calculate_planar_distance(coord1_lat, coord1_lon, coord2_lat, coord2_lon)
print(f"The distance between the two points is: {distance_meters:.2f} meters")
# ... existing code ...
