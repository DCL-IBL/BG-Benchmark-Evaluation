import dropbox
import time
import os

# Best practice: Store these in your Cloud Provider's 'Environment Variables'
APP_KEY = 'm3mus1bmj690fgb'
APP_SECRET = 'nbmo37ssjcqc887'
REFRESH_TOKEN = 'l_WONtSPXLgAAAAAAAAAAZOYxf1MkADJsCxCCxrbNW6UaLaHnueRkCTj606UHKb1'

def get_filename(file_path):
    # os.path.basename returns the last part of the path
    return os.path.basename(file_path)

def upload_results(file_path):
    # Providing oauth2_refresh_token makes the connection "permanent"
    dbx = dropbox.Dropbox(
        app_key=APP_KEY,
        app_secret=APP_SECRET,
        oauth2_refresh_token=REFRESH_TOKEN
    )
    
    with open(file_path, "rb") as f:
        dbx.files_upload(
        f.read(),
        "/linguistics/" + get_filename(file_path),
        mode=dropbox.files.WriteMode.overwrite)
    print("Upload successful!")

