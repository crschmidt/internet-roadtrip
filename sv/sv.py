from google.streetview.publish_v1.proto import resources_pb2
from google.streetview.publish_v1 import street_view_publish_service_client as client
import google.oauth2.credentials
import requests
import time
import sys
import argparse

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the scope for the API you want to access.
SCOPES = ['https://www.googleapis.com/auth/streetviewpublish']
CLIENT_SECRETS_FILE = 'client_secret.json'
CREDENTIALS_FILE = 'token.json'

def get_credentials():
    """
    Handles user authentication and credential storage.
    If valid credentials are not found, it initiates the OAuth 2.0 flow.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(CREDENTIALS_FILE):
        creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # If credentials have expired and a refresh token exists, refresh them.
            creds.refresh(Request())
        else:
            # Run the OAuth 2.0 flow to get new credentials.
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run.
        with open(CREDENTIALS_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return creds

def get_access_token():
    """
    A simple wrapper to get just the access token from the credentials.
    In most cases, you will use the full credentials object with a client library.
    """
    credentials = get_credentials()
    if not credentials or not credentials.token:
        raise Exception("Could not retrieve access token.")
    return credentials.token

def run(lat, lng, path):

  token = get_access_token()
  credentials = google.oauth2.credentials.Credentials(token)
  
  # Create a client and request an Upload URL.
  streetview_client = client.StreetViewPublishServiceClient(credentials=credentials)
  upload_ref = streetview_client.start_upload()
  print("Created upload URL: " + str(upload_ref))
  
  # Upload the photo bytes to the Upload URL.
  with open(path, "rb") as f:
    print("Uploading file: " + f.name)
    raw_data = f.read()
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "image/jpeg",
        "X-Goog-Upload-Protocol": "raw",
        "X-Goog-Upload-Content-Length": str(len(raw_data)),
    }
    r = requests.post(upload_ref.upload_url, data=raw_data, headers=headers)
    print("Upload response: " + str(r))
  
  # Upload the metadata of the photo.
  photo = resources_pb2.Photo()
  photo.upload_reference.upload_url = upload_ref.upload_url
  photo.capture_time.seconds = int(time.time())
  photo.pose.heading = 105.0
  photo.pose.lat_lng_pair.latitude = float(lat)
  photo.pose.lat_lng_pair.longitude = float(lng)
  create_photo_response = streetview_client.create_photo(photo)
  print("Create photo response: " + str(create_photo_response))


if __name__ == "__main__":
    lat, lng, path = sys.argv[1:]    
    run(lat, lng, path)
