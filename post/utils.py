import math
from math import radians, cos, sin, asin, sqrt

# earth_radius = 3960.0  # for miles
earth_radius = 6371.0  # for kms
degrees_to_radians = math.pi / 180.0
radians_to_degrees = 180.0 / math.pi


def change_in_latitude(distance):
    """Given a distance north, return the change in latitude."""
    return (distance / earth_radius) * radians_to_degrees


def change_in_longitude(latitude, distance):
    """Given a latitude and a distance west, return the change in longitude."""
    # Find the radius of a circle around the earth at given latitude.
    r = earth_radius * math.cos(latitude * degrees_to_radians)
    return (distance / r) * radians_to_degrees


def bounding_box(longitude, latitude, distance):
    print(latitude, longitude)
    lat_change = change_in_latitude(distance)
    lat_max = latitude + lat_change
    lat_min = latitude - lat_change
    lon_change = change_in_longitude(latitude, distance)
    lon_max = longitude + lon_change
    lon_min = longitude - lon_change
    return lon_min, lon_max, lat_min, lat_max


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r
