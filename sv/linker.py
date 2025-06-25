from google.streetview.publish_v1 import street_view_publish_service_client as client

from google.streetview.publish_v1.types import Connection, Photo, PhotoId
from google.protobuf import field_mask_pb2
import google.oauth2.credentials
from sv import get_access_token
import sys

def update_photo_connections(photo_ids: list[str]):
    """
    Updates a list of Street View photos to connect to each other.

    Args:
        photo_ids: A list of Street View photo IDs to connect.
    """
    token = get_access_token()
    credentials = google.oauth2.credentials.Credentials(token)
    
    # Create a client and request an Upload URL.
    streetview_client = client.StreetViewPublishServiceClient(credentials=credentials)

    for photo_id_to_update in photo_ids:
        # Create a list of connections to all other photos in the list.
        connections = []
        for other_photo_id in photo_ids:
            if other_photo_id != photo_id_to_update:
                connection = Connection(
                    target=PhotoId(id=other_photo_id)
                )
                connections.append(connection)

        # Create the Photo object with the updated connections.
        photo = Photo(
            photo_id=PhotoId(id=photo_id_to_update),
            connections=connections,
        )

        # Create the update mask to specify that only the 'connections' field should be updated.
        update_mask = field_mask_pb2.FieldMask(paths=['connections'])


        # Make the API call to update the photo.
        try:
            response = streetview_client.update_photo(photo, update_mask)
            print(response)        
            print(f"Successfully updated connections for photo: {photo_id_to_update}")
            print(f"New connections: {[conn.target.id for conn in response.connections]}")
        except Exception as e:
            print(f"Error updating connections for photo {photo_id_to_update}: {e}")

if __name__ == '__main__':
    # Replace with your actual photo IDs
    # It is assumed that you have already authenticated with Google Cloud.
    # See the Google Cloud documentation for authentication details:
    # https://cloud.google.com/docs/authentication/getting-started
    street_view_photo_ids = sys.argv[1:]
    update_photo_connections(street_view_photo_ids)
