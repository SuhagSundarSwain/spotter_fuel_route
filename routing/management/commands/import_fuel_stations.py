from django.core.management.base import BaseCommand
import pandas as pd
from routing.models import FuelStation

class Command(BaseCommand):
    help = 'Import fuel station data from CSV'

    def handle(self, *args, **kwargs):
        fuel_stations_with_lat_long = pd.read_csv("fuel_stations_with_lat_lon.csv")
        for _, row in fuel_stations_with_lat_long.iterrows():
            FuelStation.objects.create(
                name=row["Truckstop Name"],
                address=row["Address"],
                city=row["City"],
                state=row["State"],
                retail_price=row["Retail Price"],
                latitude=row["lat"],
                longitude=row["lon"],
            )
        self.stdout.write(self.style.SUCCESS('CSV data imported successfully!'))
