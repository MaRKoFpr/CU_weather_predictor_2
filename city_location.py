from geopy.geocoders import Nominatim


def city_location(city):
    geolocator = Nominatim(user_agent="geoapi")

    location = geolocator.geocode(city)

    if location is None:
        location = geolocator.geocode("Лох")
    return location.latitude, location.longitude

