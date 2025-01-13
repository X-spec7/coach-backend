from zoomus import ZoomClient
from requests.auth import HTTPBasicAuth
from time import time
from time import time as current_time
import requests
import os
import jwt

CLIENT_ID = os.environ.get("ZOOM_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ZOOM_CLIENT_SECRET", "")
ACCOUNT_ID = os.environ.get("ZOOM_ACCOUNT_ID", "")

# Global variables to store the access token and its expiration time
access_token = None
token_expires_at = 0

def fetch_access_token():
    """Fetch a new access token using the account credentials."""
    global access_token, token_expires_at
    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ACCOUNT_ID}"
    response = requests.post(url, auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET))
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        # Set the token expiration time (current time + expires_in seconds)
        token_expires_at = current_time() + token_data['expires_in']
    else:
        raise Exception(f"Failed to fetch access token: {response.json()}")

def get_valid_access_token():
    """Retrieve a valid access token, refreshing it if necessary."""
    if access_token is None or current_time() >= token_expires_at:
        fetch_access_token()
    return access_token

def create_zoom_meeting(payload):
    """Go to zoom documentation https://developers.zoom.us/docs/meeting-sdk/apis/#operation/meetingCreate"""
    try:
        token = get_valid_access_token()
        headers = {'Authorization': f'Bearer {token}'}
        client = ZoomClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, api_account_id=ACCOUNT_ID)
        response = client.meeting.create(**payload)
        if response.status_code == 201:
            return response.json()
        elif response.status_code == 401 and response.json().get('code') == 124:
            fetch_access_token()
            headers['Authorization'] = f'Bearer {access_token}'
            response = client.meeting.create(**payload)
            if response.status_code == 201:
                return response.json()
            else:
                raise Exception(f"Failed to create meeting after token refresh: {response.json()}")
        else:
            raise Exception(f"Failed to create meeting: {response.json()}")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def create_auth_signature(meeting_number, role):
    try:
        ZOOM_SDK_CLIENT_ID = os.environ.get("ZOOM_SDK_ACC_ID", "")
        ZOOM_SDK_CLIENT_SECRET = os.environ.get("ZOOM_SDK_ACC_SECRET", "")
        iat = time()
        exp = iat + 60 * 60 * 1  # expire after 1 hour
        oHeader = {"alg": 'HS256', "typ": 'JWT'}
        oPayload = {
            "sdkKey": ZOOM_SDK_CLIENT_ID,
            # The Zoom meeting or webinar number.
            "mn": int(meeting_number),
            # The user role. 0 to specify participant, 1 to specify host.
            "role": role,
            "iat": iat,
            "exp": exp,
            "tokenExp": exp
        }
        jwtEncode = jwt.encode(
            oPayload,
            ZOOM_SDK_CLIENT_SECRET,
            algorithm="HS256",
            headers=oHeader,
        )
        return {'signature': jwtEncode, 'sdkKey': ZOOM_SDK_CLIENT_ID}
    except Exception as e:
        print(f"An error occurred: {e}")
        raise
