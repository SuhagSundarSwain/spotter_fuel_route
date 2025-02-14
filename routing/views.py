import numpy as np
import requests
import math
from os import getenv
from django.http import JsonResponse
from .models import FuelStation
import logging

# Logger Setup
logger = logging.getLogger(__name__)

# Constants
API_KEY = getenv("API_KEY")
EARTH_RADIUS_MILES = 3958.8
FUEL_STATION_RADIUS = 10
MAX_VEHICLE_RANGE = 500
MILES_PER_GALLON = 10

# Haversine formula for distance calculation
def haversine(lat1, lon1, lat2, lon2):
    return 2 * EARTH_RADIUS_MILES * np.arcsin(
        np.sqrt(
            np.sin(np.radians(lat2 - lat1) / 2)**2
            + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(np.radians(lon2 - lon1) / 2)**2
        )
    )

# Fetch latitude and longitude for a location
def get_lat_lon(location):
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {"text": location, "apiKey": API_KEY}
    response = requests.get(url, params=params)
    if not response.ok:
        raise Exception(f"Error fetching location details for {location}")
    data = response.json().get("features", [])
    if not data:
        raise Exception(f"No data found for location: {location}")
    props = data[0].get("properties", {})
    return {"location": props.get("city"), "latitude": props.get("lat"), "longitude": props.get("lon")}

# Fetch route from start to end location
def get_route(start, end):
    url = "https://api.geoapify.com/v1/routing"
    params = {
        "waypoints": f"{start['latitude']},{start['longitude']}|{end['latitude']},{end['longitude']}",
        "mode": "truck", "units": "imperial", "apiKey": API_KEY
    }
    response = requests.get(url, params=params)
    if not response.ok:
        raise Exception("Error fetching route details")
    data = response.json().get("features", [])
    if not data:
        raise Exception("No route data found")
    return data[0]

# Get nearby fuel stations using NumPy optimization
def get_nearby_fuel_stations(route_coords):
    latitudes, longitudes = zip(*route_coords)
    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)

    fuel_stations = FuelStation.objects.filter(
        latitude__gte=min_lat-0.1, latitude__lte=max_lat+0.1,
        longitude__gte=min_lon-0.1, longitude__lte=max_lon+0.1
    )
    
    station_list = list(fuel_stations.values("name", "address", "city", "state", "retail_price", "latitude", "longitude"))
    if not station_list:
        return []

    route_array = np.array(route_coords)
    station_array = np.array([(s["latitude"], s["longitude"]) for s in station_list])

    lat1, lon1 = np.radians(station_array[:, 0]), np.radians(station_array[:, 1])
    lat2, lon2 = np.radians(route_array[:, 0, None]), np.radians(route_array[:, 1, None])

    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    distances = 2 * EARTH_RADIUS_MILES * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    valid_stations = np.any(distances <= FUEL_STATION_RADIUS, axis=0)
    nearby_stations = [station_list[i] for i in np.where(valid_stations)[0]]
    
    return sorted(nearby_stations, key=lambda x: x["retail_price"])

# Find optimal fuel stops along the route
def get_optimal_fuel_stops(route_distance, fuel_stations_nearby, route_coords, steps):

    vehicle_range = MAX_VEHICLE_RANGE
    miles_per_gallon = MILES_PER_GALLON

    # Calculate total fuel required for the route
    total_fuel_needed = route_distance / miles_per_gallon
    total_cost = 0
    fuel_stops = []

    # Initialize the current distance traveled
    current_distance = 0
    current_index = 0  # Index to track route coordinates

    # Sort the fuel stations by fuel price (cheapest first)
    sorted_stations = sorted(fuel_stations_nearby, key=lambda x: x["retail_price"])

    # Iterate through the route steps
    for step in steps:
        segment_distance = step['distance']  # Distance in the current segment
        
        # If the current segment is within the vehicle's range, search for the best fuel station
        if segment_distance <= vehicle_range:
            # Find the fuel stations within the range of this segment
            available_stations = []
            search_range = current_distance + vehicle_range

            for station in sorted_stations:
                # Calculate the distance from the current point (route_coords[current_index])
                station_distance = haversine(route_coords[current_index][0], route_coords[current_index][1], station["latitude"], station["longitude"])
                if current_distance < station_distance <= search_range:
                    available_stations.append(station)

            # If there are no stations available, continue to the next step
            if not available_stations:
                continue

            # Select the cheapest station from the available ones in the range
            next_stop = min(available_stations, key=lambda x: x["retail_price"])

            # Add the selected stop to the list
            fuel_stops.append(next_stop)

            # Calculate the fuel cost for this segment
            segment_distance = haversine(route_coords[current_index][0], route_coords[current_index][1], next_stop["latitude"], next_stop["longitude"])
            fuel_needed = segment_distance / miles_per_gallon
            fuel_cost = fuel_needed * next_stop["retail_price"]
            total_cost += fuel_cost

            # Update the current distance and index to the fuel stop
            current_distance += segment_distance
            current_index += 1

            # Remove the selected station from further consideration
            sorted_stations = [station for station in sorted_stations if station != next_stop]
            
            # If the vehicle has reached its destination, break the loop
            if current_distance >= route_distance:
                break
    
    return fuel_stops, total_cost



def get_route_with_fuel_stopage(request):
    try:
        if request.method != "GET":
            raise Exception("Only GET method is allowed.")
        start_location, end_location = request.GET.get("start"), request.GET.get("end")
        if not start_location or not end_location:
            raise KeyError("Start and End locations are required!")
        
        start_details = get_lat_lon(start_location)
        end_details = get_lat_lon(end_location)
        route_data = get_route(start_details, end_details)
        route_coords = [(start_details["latitude"], start_details["longitude"])] + \
                       [(lat, lon) for lon, lat in route_data["geometry"]["coordinates"][0]] + \
                       [(end_details["latitude"], end_details["longitude"])]
        steps = route_data["properties"]["legs"][0]["steps"]
        route_distance = route_data["properties"].get("distance", 0)

        fuel_stations_nearby = get_nearby_fuel_stations(route_coords)
        optimal_stops, total_fuel_cost = get_optimal_fuel_stops(route_distance, fuel_stations_nearby, route_coords, steps)

        return JsonResponse({"route": route_coords, "fuel_stops": optimal_stops, "total_fuel_cost": total_fuel_cost})

    except KeyError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)
