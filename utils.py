import os
from sys import platform
import shutil
import sqlite3
from pathlib import Path
import pandas as pd
import webbrowser

import tzlocal
from zoneinfo import ZoneInfo

# Local timezone setup
local_timezone = tzlocal.get_localzone()
video_timezone = ZoneInfo("UTC")

# Function to create directory if it doesn't exist
def make_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

# Base directory setup
base_dir = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(base_dir, "data")
make_dir(DATA_DIR)

# Define paths based on the operating system
if platform == "linux" or platform == "linux2":
    FIREFOX_HISTORY_FILE = Path(os.path.expanduser("~/.mozilla/firefox/*.default-release/places.sqlite"))
    CHROME_HISTORY_FILE = Path(os.path.expanduser("~/.config/google-chrome/Default/History"))
    BRAVE_HISTORY_FILE = Path(os.path.expanduser("~/.config/BraveSoftware/Brave-Browser/Default/History"))
    ARC_HISTORY_FILE = Path(os.path.expanduser("~/.arc/User Data/Default/History"))  # Update to Arc's correct path on Linux
elif platform == "darwin":
    FIREFOX_HISTORY_FILE = Path(os.path.expanduser("~/Library/Application Support/Firefox/Profiles/vze01ffv.default-release/places.sqlite"))
    CHROME_HISTORY_FILE = Path(os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History"))
    BRAVE_HISTORY_FILE = Path(os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Default/History"))
    ARC_HISTORY_FILE = Path(os.path.expanduser("~/Library/Application Support/Arc/User Data/Default/History"))  # Correct path for macOS
elif platform == "win32":
    print("Using Windows")
    FIREFOX_HISTORY_FILE = Path(os.path.expanduser(r"~\AppData\Roaming\Mozilla\Firefox\Profiles\vze01ffv.default-release\places.sqlite"))
    CHROME_HISTORY_FILE = Path(os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default\History"))
    BRAVE_HISTORY_FILE = Path(os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\History"))
    ARC_HISTORY_FILE = Path(os.path.expanduser(r"~\AppData\Local\Arc\User Data\User Data\Default\History"))  # Correct path for Windows

# Temporary files for processing history
FIREFOX_TMP_FILE = Path(os.path.join(DATA_DIR, "firefox_history.sqlite"))
CHROME_TMP_FILE = Path(os.path.join(DATA_DIR, "chrome_history.sqlite"))
BRAVE_TMP_FILE = Path(os.path.join(DATA_DIR, "brave_history.sqlite"))
ARC_TMP_FILE = Path(os.path.join(DATA_DIR, "arc_history.sqlite"))

# Function to add datetime information to DataFrame
def add_datetime(df):
    df = df.copy()
    df['datetime_utc'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    df['datetime_local'] = df['datetime_utc'].apply(lambda x: x.replace(tzinfo=video_timezone).astimezone(local_timezone))
    return df

# Function to retrieve Firefox browsing history
def get_firefox_history(db_file=FIREFOX_HISTORY_FILE, db_file_tmp=FIREFOX_TMP_FILE):
    """Retrieves Firefox browsing history."""
    if not db_file.exists():
        return pd.DataFrame()
    shutil.copy(db_file, db_file_tmp)
    conn = sqlite3.connect(db_file_tmp)
    history = pd.read_sql("SELECT * FROM moz_places", con=conn)

    # Drop entries with missing titles
    history = history.dropna(subset=['title'])

    # Process history data
    history['timestamp'] = history['last_visit_date'].fillna(0) / 1000000
    history['description'] = history['description'].fillna("No description")
    history['title_description'] = history.apply(lambda row: row["title"] + ":" + row['description'], axis=1)
    history['browser'] = "Firefox"
    print(f"{len(history)} urls from Firefox")
    return history

# Function to retrieve Chrome browsing history
def get_chrome_history(db_file=CHROME_HISTORY_FILE, db_file_tmp=CHROME_TMP_FILE):
    """Retrieves Chrome browsing history."""
    if not db_file.exists():
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

    # Process history data
    history['description'] = history['title'].fillna("No description")
    history['title_description'] = history.apply(lambda row: row["title"] + ":" + row['description'], axis=1)
    history['browser'] = "Chrome"
    print(f"{len(history)} urls from Chrome")
    return history

# Function to retrieve Brave browsing history
def get_brave_history(db_file=BRAVE_HISTORY_FILE, db_file_tmp=BRAVE_TMP_FILE):
    """Retrieves Brave browsing history."""
    if not db_file.exists():
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

    # Process history data
    history['description'] = history['title'].fillna("No description")
    history['title_description'] = history.apply(lambda row: row["title"] + ":" + row['description'], axis=1)
    history['browser'] = "Brave"
    print(f"{len(history)} urls from Brave")
    return history

# Function to retrieve Arc browsing history
def get_arc_history(db_file=ARC_HISTORY_FILE, db_file_tmp=ARC_TMP_FILE):
    """Retrieves Arc browsing history."""
    if not db_file.exists():
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

    # Process history data
    history['description'] = history['title'].fillna("No description")
    history['title_description'] = history.apply(lambda row: row["title"] + ":" + row['description'], axis=1)
    history['browser'] = "Arc"
    print(f"{len(history)} urls from Arc")
    return history

# Function to retrieve and preprocess browser history from all browsers
def get_browser_history(kw_filter=True):
    """Retrieves and pre-processes browser history from all found browsers."""
    histories = list()
    histories.append(get_firefox_history())
    histories.append(get_chrome_history())
    histories.append(get_brave_history())
    histories.append(get_arc_history())
    
    history = pd.concat(histories)
    if len(history) == 0:
        print("No history found")
        return history
    history = add_datetime(history)
    history = history.sort_values(by='timestamp', ascending=True)

    # Drop duplicate URLs
    history = history.drop_duplicates(subset=['url'], keep='last')

    # Apply keyword filtering if enabled
    if kw_filter:
        filter_keywords = ["Inbox", "Gmail", "ChatGPT", "Home", "LinkedIn", "Sign In", "Google Slides", "Google Search"]
        for kw in filter_keywords:
            history = history.loc[~(history['title_description'].str.lower().str.contains(kw.lower()))]

    history['url_hash'] = history['url'].apply(lambda u : hash(u) % ((1 << 61) - 1)) # Positive hash
    return history

# Function to open URLs in specified browser
def open_urls(urls, browser="default"):
    """Open URLs in the specified browser."""
    for url in urls:
        if browser == "default":
            webbrowser.open(url, new=1, autoraise=True)
        elif browser == "firefox":
            webbrowser.get('firefox').open(url, new=1, autoraise=True)
        elif browser == "chrome":
            webbrowser.get('chrome').open(url, new=1, autoraise=True)
        elif browser == "brave":
            webbrowser.get('brave').open(url, new=1, autoraise=True)
        elif browser == "arc":
            webbrowser.get('arc').open(url, new=1, autoraise=True)

