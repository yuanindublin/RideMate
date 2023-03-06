import sqlalchemy
from sqlalchemy import create_engine
import traceback
import glob
import os
from pprint import pprint
import simplejson as json
import requests
import time
from IPython.display import display

URI = "dbbikes.c06rsktpo8sk.us-east-1.rds.amazonaws.com"
PORT = "3306"
DB = "dbbikes"
USER = "minhly"
PASSWORD = "22201371"
engine = create_engine("mysql://{}:{}@{}:{}/{}".format(USER,PASSWORD,URI,PORT,DB),echo=True)

sql = """CREATE DATABASE IF NOT EXISTS dbbikes"""
engine.execute(sql)

for res in engine.execute("SHOW VARIABLES"):
    print(res)