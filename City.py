from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
import requests

API_KEY = "5emXwRzKHeYlW3wyTb2Ft8l99qbHlkqt"
BASE_URL = "http://dataservice.accuweather.com"

geolocator = Nominatim(user_agent="geoapi")


class City:
    def __init__(self, name):
        self.name = name
        self.coord = self.init_coord()
        self.loc_key = self.init_loc_key()
        self.forecast = self.init_forecast()

    def init_coord(self):
        try:
            location = geolocator.geocode(self.get_name())
            print(location)
            if location:
                return location.latitude, location.longitude
            else:
                return None
        except GeopyError:
            return None

    def init_loc_key(self):
        if not self.get_coord():
            return
        global API_KEY, BASE_URL

        lat, lon = self.get_coord()
        url = f"{BASE_URL}/locations/v1/cities/geoposition/search?apikey={API_KEY}&q={lat},{lon}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            location_key = data.get("Key")
            return location_key
        else:
            print(f"Ошибка: {response.status_code}, {response.text}")
            return

    def init_forecast(self):
        if not self.get_loc_key():
            return
        loc_key = self.get_loc_key()
        url = f"{BASE_URL}/forecasts/v1/daily/5day/{loc_key}?apikey={API_KEY}&language=en-us&details=true&metric=true"
        response = requests.get(url)
        print(url)
        try:
            return response.json()
        except Exception as e:
            return "weather exeption"

    def get_name(self):
        return self.name

    def get_coord(self):
        return self.coord

    def get_forecast(self):
        return self.forecast

    def jsonify(self):
        data = {
            "name": self.name,
            "coord": self.coord,
            "loc_key": self.loc_key,
            "forecast": self.forecast
        }
        return data

    def get_loc_key(self):
        return self.loc_key


if __name__ == "__main__":
    moscow = City('Москва')
    print(moscow.jsonify())
    print(moscow.get_forecast())
