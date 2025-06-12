import sys
from haversine import haversine, Unit

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculates the haversine distance between two points.

    Args:
        lat1: Latitude of the first point.
        lon1: Longitude of the first point.
        lat2: Latitude of the second point.
        lon2: Longitude of the second point.

    Returns:
        The distance in meters, or None if an error occurred.
    """
    try:
      point1 = (float(lat1), float(lon1))
      point2 = (float(lat2), float(lon2))
      distance = haversine(point1, point2, unit=Unit.METERS)
      return distance
    except ValueError:
      print("Invalid input: coordinates must be numbers.")
      return None
    except Exception as e:
      print(f"An unexpected error occurred: {e}")
      return None


if __name__ == "__main__":

    search_points = [(46.05147027185778, -64.77841721319136),
(46.05148193835031, -64.77854489925093),
(46.05139936161561, -64.7783388123255),
(46.05131074600122, -64.77835562272517),
                 (46.05142752698816, -64.77864707339856)]

    for i in search_points:
      print(calculate_distance(46.05136913658,-64.7785013479078, i[0], i[1]), calculate_distance(46.051284466452906, -64.778161354959863, i[0], i[1]))

    if len(sys.argv) != 5:
        print("Usage: python haversine_distance.py <lat1> <lon1> <lat2> <lon2>")
        sys.exit(1)

    lat1, lon1, lat2, lon2 = sys.argv[1:]

    distance = calculate_distance(lat1, lon1, lat2, lon2)

    if distance is not None:
      print(f"The distance is: {distance:.2f} meters")
