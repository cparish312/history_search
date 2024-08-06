import os
import shutil
import sqlite3
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
DATA_DIR = os.path.join(base_dir, "data")
make_dir(DATA_DIR)

FIREFOX_HISTORY_FILE = os.path.expanduser("~/Library/Application Support/Firefox/Profiles/vze01ffv.default-release/places.sqlite")
FIREFOX_TMP_FILE = os.path.join(DATA_DIR, "firefox_history.sqlite")

CHROME_HISTORY_FILE = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History")
CHROME_TMP_FILE = os.path.join(DATA_DIR, "chrome_history.sqlite")


def add_datetime(df):
    df = df.copy()

    df['datetime_utc'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    df['datetime_local'] = df['datetime_utc'].apply(lambda x: x.replace(tzinfo=video_timezone).astimezone(local_timezone))
    return df

def get_firefox_history(db_file=FIREFOX_HISTORY_FILE, db_file_tmp=FIREFOX_TMP_FILE):
    """Retrieves Firefox browsing history."""
    if not os.path.exists(db_file):
        return pd.DataFrame()
    shutil.copy(db_file, db_file_tmp)
    conn = sqlite3.connect(db_file_tmp)
    history = pd.read_sql("SELECT * FROM moz_places", con=conn)

    # Drop entries with missing titles
    history = history.dropna(subset=['title'])

    history['timestamp'] = history['last_visit_date'].fillna(0) / 1000000
    history['description'] = history['description'].fillna("No description")
    history['title_description'] = history.apply(lambda row: row["title"] + ":" + row['description'], axis=1)
    history['browser'] = "Firefox"
    return history

def get_chrome_history(db_file=CHROME_HISTORY_FILE, db_file_tmp=CHROME_TMP_FILE):
    """Retrieves Chrome browsing history."""
    if not os.path.exists(db_file):
        return pd.DataFrame()
    
    # Copy the database to avoid locking issues
    shutil.copy(db_file, db_file_tmp)
    conn = sqlite3.connect(db_file_tmp)

    # Query the history database
    query = """
    SELECT 
        urls.url, 
        urls.title, 
        visits.visit_time/1000000 - 11644473600 AS timestamp 
    FROM urls, visits 
    WHERE urls.id = visits.url;
    """
    
    history = pd.read_sql(query, con=conn)

    # Drop entries with missing titles
    history = history.dropna(subset=['title'])

    # Fill missing descriptions
    history['description'] = history['title'].fillna("No description")
    history['title_description'] = history.apply(lambda row: row["title"] + ":" + row['description'], axis=1)
    history['browser'] = "Chrome"
    return history

def get_browser_history(kw_filter=True):
    """Retrieves and pre-proccesses browser history from all found browsers."""
    histories = list()
    histories.append(get_firefox_history())
    histories.append(get_chrome_history())
    
    history = pd.concat(histories)
    history = add_datetime(history)
    history = history.sort_values(by='timestamp', ascending=True)

    history = history.drop_duplicates(subset=['url'], keep='last')

    if kw_filter:
        filter_keywords = ["Inbox", "Gmail", "ChatGPT", "Home", "LinkedIn", "Sign In", "Google Slides", "Google Search"]
        for kw in filter_keywords:
            history = history.loc[~(history['title_description'].str.lower().str.contains(kw.lower()))]
    return history

def open_urls(urls):
    for url in urls:
        webbrowser.get('firefox').open(url, new=1, autoraise=True)