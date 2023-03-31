# import mysql.connector
from sqlalchemy import create_engine, text
from flask import Flask, g, render_template, jsonify
import sys
sys.path.append('/Users/minhlynguyen/Documents/software-engineering/git/ridemate/RideMate')
import config
import time
import requests
import json
import functools
import traceback
import database

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = database.connect_to_database()
    return db

# From lecture note, isn't working
# @app.teardown_appcontext
# def close_connection(exception):
#     db = getattr(g, '_database', None)
#     if db is not None:
#         db.close()

@app.route('/')

@app.route('/home')
def home_page():
    return render_template('home.html')

# From Lecture note: This code works, the one below /station doesn't work. Should we delete the one below?
@app.route("/stations")
@functools.lru_cache(maxsize=128)
def get_stations():
    engine = get_db()
    sql = "select * from station;"
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(sql)).fetchall()
            print('#found {} stations', len(rows), rows, flush=True) #this has not been print because debug mode
            # app.logger.info('#found {} stations', len(rows), rows) #Another way to print
            return jsonify([row._asdict() for row in rows]) # use this formula to turn the rows into a list of dicts
    except:
        print(traceback.format_exc())
        return "error in get_stations", 404

# @app.route('/station')
# def station_page():
#     db = mysql.connector.connect(host="dbbikes.cbqpbir87k5q.eu-west-1.rds.amazonaws.com",
#                                  user="fei", passwd="22200125", db="dbbikes", port=3306)
#     cur = db.cursor()
#     sql = ("""SELECT * FROM station""")
#     cur.execute(sql)
#     results = cur.fetchall()
#     db.close()
#     return render_template('station.html', station=results)

# Replace YOUR_API_KEY with your actual Google Maps API key
GOOGLE_MAPS_API_KEY = "AIzaSyC52j5KuFhqFUz3qfPc7s16bmfqRLb9wy8"

# Dont need this anymore because the following one already retrieve information from database
# @app.route('/station/<int:station_id>')
# def station(station_id):
#     return f'Retrieving info for Station: {station_id}'.format(station_id)

# From lecture note, working now. It's showing info of 1 station defined in the link
@app.route("/available/<int:station_id>")
def get_station(station_id):
    engine = get_db()
    data = []
    rows = engine.execute("SELECT * from availability where number = {} order by last_update DESC LIMIT 1;".format(station_id))
    for row in rows:
        data.append(dict(row))
    return jsonify(available=data)

# def new_func():
#     return station_id

# Function to get the longitude of the chosen station
@app.route("/available/<int:station_id>")
def get_lng(station_id):
    engine = get_db()
    lng = engine.execute("SELECT position_lng from availability where number = {} order by last_update DESC LIMIT 1;".format(station_id))
    return lng

@app.route("/available/<int:station_id>")
def get_lat(station_id):
    engine = get_db()
    lat = engine.execute("SELECT position_lat from availability where number = {} order by last_update DESC LIMIT 1;".format(station_id))
    return lat

@app.route('/weather')
def weather(): 
    LATITUDE = get_lat
    LONGITUDE = get_lng
    r = requests.get(config.WEATHER_URL,params={"latitude":53.340927,"longitude":-6.262501,"hourly":config.HOURLY,
    "daily":config.DAILY,"current_weather":"true","timeformat":"unixtime","timezone":config.TIMEZONE})
    r_text = json.loads(r.text)
    weather = jsonify(available=r_text)
    return weather
    # return f'Weather information: {weather}'.format(weather)

@app.route('/')
def index():
    return render_template('home.html', api_key=GOOGLE_MAPS_API_KEY)

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
    def timed(*args,**kw):
        start = time.time()
        result = method(*args,**kw)
        end = time.time()
        print("")