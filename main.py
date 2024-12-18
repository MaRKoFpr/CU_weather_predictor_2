from city_location import city_location
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

API_KEY = "5emXwRzKHeYlW3wyTb2Ft8l99qbHlkqt"
BASE_URL = "http://dataservice.accuweather.com"


@app.route('/')
def index():
    return render_template('form.html')


@app.route('/get-weather', methods=['POST'])
def show_weather_info():
    start_city = request.form.get('start_city')
    finish_city = request.form.get('finish_city')

    if not start_city or not finish_city:
        return render_template('form.html', error="Все поля формы должны быть заполнены!")

    start_city_loc = city_location(start_city)
    finish_city_loc = city_location(finish_city)

    start_lat = start_city_loc['lat']
    start_lon = start_city_loc['lon']
    finish_lat = finish_city_loc['lat']
    finish_lon = finish_city_loc['lon']
    location_key = get_location_key(start_lat, start_lon)
    start_weather_data = get_weather_data(location_key)

    start_forecast = start_weather_data['DailyForecasts'][0]
    start_mx_temperature = start_forecast['Temperature']['Maximum']['Value']
    start_mn_temperature = start_forecast['Temperature']['Minimum']['Value']
    start_wind_speed = start_forecast['Day']['Wind']['Speed']['Value']
    start_rain_prob = start_forecast['Day']['PrecipitationProbability']
    start_weather_description = get_weather_description(start_mn_temperature, start_mx_temperature, start_wind_speed,
                                                  start_rain_prob)

    location_key = get_location_key(finish_lat, finish_lon)
    finish_weather_data = get_weather_data(location_key)


    finish_forecast = finish_weather_data['DailyForecasts'][0]
    finish_mx_temperature = finish_forecast['Temperature']['Maximum']['Value']
    finish_mn_temperature = finish_forecast['Temperature']['Minimum']['Value']
    finish_wind_speed = finish_forecast['Day']['Wind']['Speed']['Value']
    finish_rain_prob = finish_forecast['Day']['PrecipitationProbability']
    finish_weather_description = get_weather_description(finish_mn_temperature, finish_mx_temperature, finish_wind_speed,
                                                  finish_rain_prob)

    return render_template('form.html', start_description=start_weather_description,
                           finish_description=finish_weather_description)


def get_location_key(lat, lon):
    global API_KEY, BASE_URL

    url = f"{BASE_URL}/locations/v1/cities/geoposition/search?apikey={API_KEY}&q={lat},{lon}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        location_key = data.get("Key")
        return location_key
    else:
        return f"Ошибка: {response.status_code}, {response.text}"


def get_weather_data(loc_key):
    url = f"{BASE_URL}/forecasts/v1/daily/1day/{loc_key}?apikey={API_KEY}&language=en-us&details=true&metric=true"
    response = requests.get(url)
    print(url)
    try:
        return response.json()
    except Exception as e:
        return "weather exeption"


def get_weather_description(mn_t, mx_t, wind_speed, rain_prob):
    description = ""
    if mn_t < 0:
        description += 'Холодно '
    elif mn_t>= 0 and mx_t < 21:
        description += 'Тепло '
    else:
        description += 'Жарко '

    if wind_speed < 40:
        description += 'Нормальный ветер '
    else:
        description += 'Сильный ветер '
    if rain_prob < 40:
        description += 'Осадки  маловероятны '
    elif 40 <= rain_prob <= 60:
        description += "Есть вероятность осадков "
    else:
        description += 'Высокая вероятность осадков '
    return description


if __name__ == "__main__":
    app.run(debug=True)