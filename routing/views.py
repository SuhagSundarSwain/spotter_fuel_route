from django.shortcuts import render
from django.http import JsonResponse
import requests
from os import getenv
import logging


# Create your views here.

logger = logging.getLogger(__name__)

def get_lat_lon(location):
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text":location,
        "apiKey": getenv("API_KEY")
    }
    try:
        response = requests.get(url,params=params)
        if not response.ok:
            raise Exception(f"Somthing went wrong in getting {location} location details")
        resp = response.json()
        features = resp.get("features",[])
        if not features:
            raise Exception(f"Not getting {location} features.")
        properties = features[0].get("properties",{})
        latitude = properties.get("lat")
        longitude = properties.get("lon")
        city = properties.get("city")
        return {"location":city,"latitude":latitude,"longitude":longitude}
    except Exception as e:
        raise e
    
def get_route():
    return

def get_route_with_fuel_stopage(request):
    try:
        if not request.method=="GET":
            raise Exception("Only Get Method is allowed.")
        
        start_location = request.GET.get("start")
        end_location = request.GET.get("end")
        if not start_location or not end_location:raise KeyError("Start and End locations are required!")
        
        start_location_details = get_lat_lon(start_location)
        end_location_details = get_lat_lon(end_location)

        return JsonResponse({"start":start_location_details,"end":end_location_details})
    
    except KeyError as e:
        return JsonResponse({"error":str(e)},status=400)
    except Exception as e :
        logger.error(f"error: {e}")
        return JsonResponse({"error":str(e)},status=500)
    