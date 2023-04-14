# import mysql.connector
import functools
import json
import pickle
import time
import datetime
import traceback

import googlemaps
import numpy as np
import pandas as pd
import requests
from flask import Flask, g, jsonify, render_template, request
from flask_googlemaps import GoogleMaps
from sklearn.linear_model import LinearRegression
from sqlalchemy import text

import config
import database

app = Flask(__name__)
GoogleMaps(app, key=config.MAP_KEY)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = database.connect_to_database()
    return db


# Set up the Google Maps client
gmaps = googlemaps.Client(config.MAP_KEY)

# Search for a location in Dublin
address = "Dublin, Ireland"
geocode_result = gmaps.geocode(address)

# Get the latitude and longitude of the location
lat = geocode_result[0]["geometry"]["location"]["lat"]
lng = geocode_result[0]["geometry"]["location"]["lng"]


@app.route('/')
def index():

    # Fetch the station data from the MySQL database
    query = 'SELECT * FROM station'
    engine = get_db()
    stations = engine.connect().execute(text(query)).fetchall()
    weather_station = {}

    # Fetch the latest available bikes data
    availability_query = 'SELECT number, available_bikes FROM availability ORDER BY last_update DESC'
    availability_data = engine.connect().execute(
        text(availability_query)).fetchall() 
    availability_dict = {item[0]: item[1] for item in availability_data}

    # Set up the markers
    markers = []
    for station in stations:
        available_bikes = availability_dict.get(station[0], 0)
        marker = {
            'number': station[0],
            'position': {'lat': station[7], 'lng': station[8]},
            'title': station[6],
            'weathercode': 10,
            'status': station[9],
            'bike_stands': station[3],
            'available_bikes': available_bikes
        }
        markers.append(marker)

    # Render the template with API key, markers, and specified lat and lng
    return render_template("map.html", api_key=config.MAP_KEY, markers=markers, lat=lat, lng=lng, availability=availability_dict)


@app.route('/data')
def station_data():
    engine = get_db()
    query = 'SELECT * FROM station'
    data = engine.connectstation_data().execute(text(query)).fetchall()
    query = request.args.get('query')
    filter_criteria = request.args.get('filter')
    if query and filter_criteria:
        query = f"SELECT * FROM station WHERE {filter_criteria} LIKE '%{query}%'"
        search_results = engine.connect().execute(text(query)).fetchall()
        return render_template('data.html', search_results=search_results)
    else:
        return render_template('data.html')


@app.route("/stations")
@functools.lru_cache(maxsize=128)
def get_stations():
    engine = get_db()
    sql = "select * from station;"
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
            # this has not been print because debug mode
            print('#found {} stations', len(rows), rows, flush=True)
            # app.logger.info('#found {} stations', len(rows), rows) #Another way to print
            # use this formula to turn the rows into a list of dicts
            get_stations = jsonify([row._asdict() for row in rows])
            return get_stations
    except:
        print(traceback.format_exc())
        return "error in get_stations", 404


@app.route("/availability/daily/<int:station_id>")
def get_availability_daily(station_id):
    engine = get_db()
    df = pd.read_sql_query(
        "SELECT * from availability where number = %(number)s", engine, params={"number": station_id})
    df['last_update'] = pd.to_datetime(df.last_update, unit='s')
    df.set_index('last_update', inplace=True)
    res = df[['available_bikes', 'available_bike_stands']
             ].resample('1d').mean()
    daily = jsonify(data=json.dumps(
        list(zip(map(lambda x: x.isoformat(), res.index), res.values.tolist()))))
    return daily


@app.route("/chart")
def chart():
    return render_template("chart.html")


@app.route("/predict_bikes/<int:station_id>")
def predict_id(station_id):
    filename = 'models_bikes/'+str(station_id)+'.pkl'
    with open(filename, 'rb') as handle:
        model = pickle.load(handle)
    
    for i in get_stations().json:
        if i['number'] == station_id:
            lat = i['position_lat']
            lng = i['position_lng']
    LATITUDE = lat
    LONGITUDE = lng
    req = requests.get(config.WEATHER_URL, params={"latitude": LATITUDE, "longitude": LONGITUDE, "current_weather": "true", "timeformat": "unixtime", "timezone": config.TIMEZONE})
    data = req.json()
    temperature = data["current_weather"]["temperature"]
    weathercode = data["current_weather"]["weathercode"]
    windspeed = data["current_weather"]["windspeed"]
    day_of_week = datetime.datetime.now().isoweekday()
    # is_holiday = 0
    res = {}
    for i in range(1, 25):
        result = model.predict([[i, day_of_week, 0, temperature, weathercode, windspeed]])
        res[i] = int(result[0])
    return res


if __name__ == '__main__':
    app.run(debug=True)

# Testing decorators:


def build_regression_model(**kwargs):
    print('building model...')

# build_regression_model()


start = time.time()
build_regression_model()
end = time.time()

print(end-start)
print("took: {} secs".format(end-start))


def timeit(method):
    def timed(*args, **kw):
        start = time.time()
        result = method(*args, **kw)
        end = time.time()
        print("")
