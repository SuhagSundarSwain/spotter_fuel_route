import numpy as np
import requests
import math
from os import getenv
from django.http import JsonResponse
from .models import FuelStation
import logging
from django.shortcuts import render,redirect
import json
import urllib.parse
from django.shortcuts import render

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

    total_cost = 0
    fuel_stops = []

    current_position = route_coords[0]
    destination = route_coords[-1]

    sorted_stations = sorted(fuel_stations_nearby, key=lambda x: x["retail_price"])

    while haversine(current_position[0], current_position[1], destination[0], destination[1]) > vehicle_range:
        candidates = []
        for station in sorted_stations:
            # Distance from current position to this station
            station_distance = haversine(
                current_position[0], current_position[1],
                station["latitude"], station["longitude"]
            )
            # Check if station is within range
            if station_distance <= vehicle_range:
                # Ensure the station is ahead in the route:
                # Its distance to the destination should be less than that from our current position.
                if haversine(station["latitude"], station["longitude"], destination[0], destination[1]) < \
                   haversine(current_position[0], current_position[1], destination[0], destination[1]):
                    candidates.append((station, station_distance))

        if not candidates:
            raise Exception("No reachable fuel station found ahead within range; route not feasible.")

        # Choose the optimal candidate (here: the one with the lowest fuel price)
        next_stop, distance_to_next = min(candidates, key=lambda x: x[0]["retail_price"])
        fuel_stops.append(next_stop)
        fuel_needed = distance_to_next / miles_per_gallon
        total_cost += fuel_needed * next_stop["retail_price"]
        current_position = [next_stop["latitude"], next_stop["longitude"]]
        sorted_stations.remove(next_stop)

    return fuel_stops, round(total_cost,2)





def get_route_with_fuel_stopage(request):
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

    return {"steps":steps,"route": route_coords, "fuel_stops": optimal_stops, "total_fuel_cost": total_fuel_cost}



def get_route_fuel_stop_api(request):
    try:
        resp=get_route_with_fuel_stopage(request)
        return JsonResponse(resp,resp.get("status"))
    except KeyError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)


def home(request):
    return render(request,"getRouteFrom.html")




def mapView(request):
    fuel_stopage_response = get_route_with_fuel_stopage(request)

    route = fuel_stopage_response.get('route')
    route = [[b, a] for a, b in route]
    markers = [
        f"lonlat:{stop.get('longitude')},{stop.get('latitude')};color:blue;size:medium;icon:gas-pump;icontype:awesome;strokecolor:%23000000;shadow:no"
        for stop in fuel_stopage_response.get("fuel_stops", [])
    ]
    markers.extend([
        f"lonlat:{route[0][0]},{route[0][1]};color:%23ff0000;size:medium",
        f"lonlat:{route[-1][0]},{route[-1][1]};color:%23ff0000;size:medium"
    ])
    markers = "|".join(markers)

    route = [route[0]] + [[stop.get('longitude'), stop.get('latitude')] for stop in fuel_stopage_response.get("fuel_stops", [])] + [route[-1]]
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": route
                },
                "properties": {
                    "stroke-color": "blue",
                    "stroke-width": 5
                }
            }
        ]
    }

    geojson_str = json.dumps(geojson_data)
    encoded_geojson = urllib.parse.quote(geojson_str)

    mapLink = (
        'https://maps.geoapify.com/v1/staticmap?'
        'style=klokantech-basic'
        '&width=1800'
        '&height=800'
        '&zoom=12'
        f'&marker={markers}'
        f'&geojson={encoded_geojson}'
        f'&apiKey={API_KEY}'
    )
    
    return render(request, "mapView.html", {"mapLink": mapLink,"fuel_cost":fuel_stopage_response.get('total_fuel_cost')})
