import os
import sqlite3
import shutil
import pandas as pd
import webbrowser
import tzlocal
from zoneinfo import ZoneInfo

# Get the local timezone
local_timezone = tzlocal.get_localzone()
video_timezone = ZoneInfo("UTC")

def make_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

# Set up directories
base_dir = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(base_dir, "data")
make_dir(DATA_DIR)

# Define Chrome history file paths
CHROME_HISTORY_FILE = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History")
DB_TMP_FILE = os.path.join(DATA_DIR, "chrome_history.sqlite")

def add_datetime(df):
    """Adds UTC and local datetime columns to the DataFrame."""
    df = df.copy()

    # Fill NaN timestamps with 0
    df['timestamp'] = df['timestamp'].fillna(0)

    # Convert timestamp to UTC and local datetime
    df['datetime_utc'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    df['datetime_local'] = df['datetime_utc'].apply(lambda x: x.replace(tzinfo=video_timezone).astimezone(local_timezone))
    return df

def get_chrome_history(db_file=CHROME_HISTORY_FILE, db_file_tmp=DB_TMP_FILE, kw_filter=True):
    """Retrieves Chrome browsing history."""
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
    
    places = pd.read_sql(query, con=conn)

    # Add datetime columns
    places = add_datetime(places)

    # Drop entries with missing titles
    places = places.dropna(subset=['title'])

    # Fill missing descriptions
    places['description'] = places['title'].fillna("No description")
    places['title_description'] = places.apply(lambda row: row["title"] + ":" + row['description'], axis=1)

    if kw_filter:
        # Filter out entries with specific keywords
        filter_keywords = ["Inbox", "Gmail", "ChatGPT", "Home", "LinkedIn", "Sign In", "Google Slides", "Google Search"]
        for kw in filter_keywords:
            places = places.loc[~(places['title_description'].str.lower().str.contains(kw.lower()))]

    # Close the database connection
    conn.close()

    return places

def open_urls(urls):
    """Opens a list of URLs in the default web browser."""
    for url in urls:
        webbrowser.get('firefox').open(url, new=1, autoraise=True)
