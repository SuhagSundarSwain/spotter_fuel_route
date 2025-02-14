import pandas as pd
import requests
from os import getenv

fuel_stations = pd.read_csv("fuel-prices-for-be-assessment.csv")

URL = "https://api.geoapify.com/v1/geocode/search"
API_KEY = getenv("API_KEY")
def getFeatures(search_address):
    params = {
            "text":search_address,
            "apiKey":API_KEY
        }
    response = requests.get(URL, params=params)
    if response.ok:
        data = response.json()
        features = data.get("features", [])
        return features
    

error_count = 0
success_count = 0
completed_locations = set()

for index,row in fuel_stations.iterrows():
    try:
        # Construct search address
        search_address = f"{row['Truckstop Name']},{row['Address']},{row['City']},{row['State']}"
        if search_address in completed_locations:
            continue  # Skip if already processed
        
        features = getFeatures(search_address=search_address)
        if not features:
            search_address = f"{row['Truckstop Name']},{row['City']},{row['State']}"
            features = getFeatures(search_address=search_address)
        properties = features[0].get("properties", {})
        lat, lon = properties.get("lat"), properties.get("lon")
        completed_locations.add(search_address)
        success_count += 1
        print(f"{search_address} -->lat: {lat}, lon:{lon}")
        fuel_stations.at[index,"lat"] = lat
        fuel_stations.at[index,"lon"] = lon
    except Exception as e:
        error_count += 1
        print(f"Error processing {search_address[0]}: {e}")

# Summary
print(f"Total Successful: {success_count}")
print(f"Total Errors: {error_count}")


fuel_stations.to_csv("fuel_stations_with_lat_lon.csv",index=False)