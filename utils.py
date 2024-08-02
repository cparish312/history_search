import os
import requests
import shutil
import sqlite3
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from numba import njit, prange
import numpy as np
import pandas as pd
import webbrowser

import tzlocal
from zoneinfo import ZoneInfo

local_timezone = tzlocal.get_localzone()
video_timezone = ZoneInfo("UTC")

def make_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

base_dir = os.path.dirname(os.path.abspath(__file__))
FIREFOX_DB_FILE = "/Users/connorparish/Library/Application Support/Firefox/Profiles/vze01ffv.default-release/places.sqlite"
DATA_DIR = os.path.join(base_dir, "data")
make_dir(DATA_DIR)
DB_TMP_FILE = os.path.join(DATA_DIR, "places.sqlite")


def add_datetime(df):
    df = df.copy()

    df['timestamp'] = df['timestamp'].fillna(0)

    df['datetime_utc'] = pd.to_datetime(df['timestamp'] / 1000000, unit='s', utc=True)
    df['datetime_local'] = df['datetime_utc'].apply(lambda x: x.replace(tzinfo=video_timezone).astimezone(local_timezone))
    return df

def get_firefox_history(db_file=FIREFOX_DB_FILE, db_file_tmp=DB_TMP_FILE, kw_filter=True):
    shutil.copy(db_file, db_file_tmp)
    conn = sqlite3.connect(db_file_tmp)
    places = pd.read_sql("SELECT * FROM moz_places", con=conn)

    places['timestamp'] = places['last_visit_date']
    places = add_datetime(places)

    places = places.dropna(subset=['title'])

    places['description'] = places['description'].fillna("No description")
    places['title_description'] = places.apply(lambda row: row["title"] + ":" + row['description'], axis=1)

    if kw_filter:
        filter_keywords = ["Inbox", "Gmail", "ChatGPT", "Home", "LinkedIn", "Sign In", "Google Slides", "Google Search"]
        for kw in filter_keywords:
            places = places.loc[~(places['title_description'].str.lower().str.contains(kw.lower()))]
    return places

def open_urls(urls):
    for url in urls:
        webbrowser.get('firefox').open(url, new=1, autoraise=True)