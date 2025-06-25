from google.streetview.publish_v1 import street_view_publish_service_client as client

from google.streetview.publish_v1 import enums
from google.streetview.publish_v1.types import Connection, Photo, PhotoId
from google.protobuf import field_mask_pb2
import google.oauth2.credentials
from sv import get_access_token
import sys

def list(photos):
    token = get_access_token()
    credentials = google.oauth2.credentials.Credentials(token)
    view = enums.PhotoView.BASIC
 
    # Create a client and request an Upload URL.
    streetview_client = client.StreetViewPublishServiceClient(credentials=credentials)
    print(streetview_client.batch_delete_photos(photos))

if __name__ == "__main__":
    list(sys.argv[1:])
