import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/drive']
# This is the JSON file you downloaded from the Cloud Console:
CLIENT_SECRET_FILE = "/home/ubuntu/dimiterg/client_secret.json" 
# This is the file that will store the user's tokens after the first run:
TOKEN_FILE = 'token.json' 
# ---------------------

credentials = None

# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first time.
if os.path.exists(TOKEN_FILE):
    credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

# If there are no (valid) credentials available, let the user log in.
if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
        # If credentials are valid but expired, refresh them
        credentials.refresh(Request())
    else:
        # This is the initial setup: runs the browser flow and saves tokens
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
        credentials = flow.run_local_server(port=0)
    
    # Save the credentials for the next run
    with open(TOKEN_FILE, 'w') as token:
        token.write(credentials.to_json())

# Build the Google Drive service
drive_service = build('drive', 'v3', credentials=credentials)
