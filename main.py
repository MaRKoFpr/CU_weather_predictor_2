import dash
import requests
from dash import dcc, html, Input, Output, State, ctx, ALL, Dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError
import plotly.graph_objs as go
from City import City

API_KEY = "5emXwRzKHeYlW3wyTb2Ft8l99qbHlkqt"
BASE_URL = "http://dataservice.accuweather.com"

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Интерфейс приложения
app.layout = html.Div([
    html.H1("Маршрут на карте"),
    dcc.Store(id="cities-store", data=[]),
    dcc.Store(id="cities_info", data=[]),
    html.Div(id="city-inputs", children=[]),
    html.Button("Добавить город", id="add-city-btn", n_clicks=0),
    html.Button("Удалить", id="del-city-btn", n_clicks=0),
    html.Button("Построить маршрут", id="plot-route-btn", n_clicks=0),
    dl.Map(
        center=[55.751244, 37.618423],  # Центр карты (Москва)
        zoom=5,
        id="map",
        style={"height": "500px", "width": "80%"},
        children=[dl.TileLayer()]),
    html.Div([
       html.H3("Выбор дней прогноза")
    ]),
    html.Div([
        dcc.RangeSlider(1, 5, 1, value=[1, 3], id='date-slider')
    ]),
    html.Div([
        dcc.Tabs(id='graph-tabs', children=[
            dcc.Tab(label='Температура', value='temperature'),
            dcc.Tab(label='Скорость ветра', value='wind_speed'),
            dcc.Tab(label='Вероятность осадков', value='precipitation')
        ]),
        html.Div(id='graph-div')
    ])
])


@app.callback(
    Output("cities-store", "data"),
    [
        Input("add-city-btn", "n_clicks"),
        Input("del-city-btn", "n_clicks")
    ],
    State('city-inputs', 'children')
)
def modify_cities_data(a, b, city_inputs):
    # Добавление нового города
    cities_data = []
    if city_inputs:
        _id = 0
        for city in city_inputs:
            city_name = city['props']['children'][0]['props']['value']
            cities_data.append({"id": _id, "value": city_name})
            _id += 1

    if ctx.triggered_id == "add-city-btn":
        new_id = max(city["id"] for city in cities_data) + 1 if cities_data else 0
        cities_data.append({"id": new_id, "value": new_id})
        return cities_data
    elif ctx.triggered_id == "del-city-btn":
        if len(cities_data) > 0:
            cities_data.pop(-1)
            return cities_data
        else:
            return cities_data


@app.callback(
    Output("city-inputs", "children"),
    Input("cities-store", "data")
)
def update_city_inputs(cities_data):
    city_inputs = []
    if cities_data is None:
        cities_data = []
    for city in cities_data:
        city_inputs.append(
            html.Div(id={"type": "city-row", "index": city["id"]}, children=[
                dcc.Input(
                    id={"type": "city-input", "index": city["id"]},
                    type="text",
                    value=city["value"],
                    placeholder=f"Введите город {city['id'] + 1}"
                )
            ])
        )
    return city_inputs


@app.callback(
    Output("cities_info", "data"),
    Input("plot-route-btn", "n_clicks"),
    State("city-inputs", "children"),
)
def set_cities_info(n_clicks, cities_data):
    if n_clicks == 0:
        return []
    cities = []
    for city in cities_data:
        name = city['props']['children'][0]['props']['value']
        if city:
            city = City(name)
            if city.get_coord():
                cities.append(city)

    print([city.get_coord() for city in cities])
    return [city.jsonify() for city in cities]


@app.callback(
    Output("map", "children"),
    Input("cities_info", "data"),
)
def draw_route(cities):
    print(cities)
    markers = [
        dl.Marker(position=city["coord"], children=dl.Tooltip(city["name"]))
        for city in cities
    ]
    if len(cities) < 2:
        return [dl.TileLayer(), *markers]

    else:
        route_line = dl.Polyline(positions=[city["coord"] for city in cities], color="blue", weight=3)
        return [dl.TileLayer(), *markers, route_line]


geolocator = Nominatim(user_agent="geoapi")


def get_coordinates(city_name):
    try:
        location = geolocator.geocode(city_name)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except GeopyError:
        return None


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
    url = f"{BASE_URL}/forecasts/v1/daily/5day/{loc_key}?apikey={API_KEY}&language=en-us&details=true&metric=true"
    response = requests.get(url)
    print(url)
    try:
        return response.json()
    except Exception as e:
        return "weather exeption"


@app.callback(Output('graph-div', 'children'),
              Input('graph-tabs', 'value'),
              Input('date-slider', 'value'),
              State('cities_info', 'data'))
def render_content(tab, dates, cities):
    if tab == 'temperature':
        X, Y = get_temperature_data(cities)
        fig = go.Figure(data=[])

        for city, x_list, y_list in zip(cities, X, Y):
            fig.add_trace(go.Scatter(x=x_list[dates[0] - 1:dates[1]], y=y_list[dates[0] - 1:dates[1]], name=city['name']))

        return html.Div([
            html.H3('Температура'),
            dcc.Graph(figure=fig)
        ])
    elif tab == 'wind_speed':
        X, Y = get_wind_speed_data(cities)
        fig = go.Figure(data=[])

        for city, x_list, y_list in zip(cities, X, Y):
            fig.add_trace(go.Scatter(x=x_list[dates[0] - 1:dates[1]], y=y_list[dates[0] - 1:dates[1]], name=city['name']))

        return html.Div([
            html.H3('Скорость ветра'),
            dcc.Graph(figure=fig)
        ])
    else:
        X, Y = get_precipitation_data(cities)
        fig = go.Figure(data=[])


        for city, x_list, y_list in zip(cities, X, Y):
            fig.add_trace(go.Scatter(x=x_list[dates[0] - 1:dates[1]], y=y_list[dates[0] - 1:dates[1]], name=city['name']))

        return html.Div([
            html.H3('Вероятность осадков'),
            dcc.Graph(figure=fig)
        ])


def get_temperature_data(cities_info):
    dates, temps = [], []
    for city in cities_info:
        dates.append([city["forecast"]['DailyForecasts'][i]['Date'][:10] for i in range(5)])
        temps.append([city["forecast"]['DailyForecasts'][i]['Temperature']['Minimum']['Value'] for i in range(5)])
    return dates, temps


def get_wind_speed_data(cities_info):
    dates, speeds = [], []
    for city in cities_info:
        dates.append([city["forecast"]['DailyForecasts'][i]['Date'][:10] for i in range(5)])
        speeds.append([city["forecast"]['DailyForecasts'][i]['Day']['Wind']['Speed']['Value'] for i in range(5)])
    return dates, speeds


def get_precipitation_data(cities_info):
    dates, precipitation = [], []
    for city in cities_info:
        dates.append([city["forecast"]['DailyForecasts'][i]['Date'][:10] for i in range(5)])
        precipitation.append(
            [city["forecast"]['DailyForecasts'][i]['Day']['PrecipitationProbability'] for i in range(5)])
    return dates, precipitation


if __name__ == '__main__':
    app.run_server(debug=True)
