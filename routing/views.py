from django.shortcuts import render
from django.http import JsonResponse
import requests
from os import getenv
import logging


# Create your views here.

logger = logging.getLogger(__name__)

API_KEY = getenv("API_KEY")

def get_lat_lon(location):
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text":location,
        "apiKey": API_KEY
    }
    response = requests.get(url,params=params)
    if not response.ok:raise Exception(f"Somthing went wrong in getting {location} location details")
    resp = response.json()
    features = resp.get("features",[])
    if not features:raise Exception(f"Not getting {location} features.")
    properties = features[0].get("properties",{})
    latitude = properties.get("lat")
    longitude = properties.get("lon")
    city = properties.get("city")
    return {"location":city,"latitude":latitude,"longitude":longitude}
    
def get_route(start,end):
    url="https://api.geoapify.com/v1/routing"
    params ={
        "waypoints":f"{start['latitude']},{start['longitude']}|{end['latitude']},{end['longitude']}",
        "mode":"truck",
        "units":"imperial",
        "apiKey": API_KEY
    }
    response = requests.get(url,params=params)
    if not response.ok:raise Exception("Not getting route. Try again after some time")
    resp = response.json()
    features = resp.get("features",[])
    if not features:raise Exception("Not getting route.")
    return features[0]

def get_route_with_fuel_stopage(request):
    try:
        if not request.method=="GET":
            raise Exception("Only Get Method is allowed.")
        
        start_location = request.GET.get("start")
        end_location = request.GET.get("end")
        if not start_location or not end_location:raise KeyError("Start and End locations are required!")
        
        start_location_details = get_lat_lon(start_location)
        end_location_details = get_lat_lon(end_location)
        route_data = get_route(start_location_details,end_location_details)
        route_coords = route_data.get("geometry").get("coordinates")[0]
        

        

        return JsonResponse({"route_data":route_coords})
    
    except KeyError as e:
        return JsonResponse({"error":str(e)},status=400)
    except Exception as e :
        logger.error(f"error: {e}")
        return JsonResponse({"error":str(e)},status=500)
    