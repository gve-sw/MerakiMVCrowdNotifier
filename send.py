"""
Copyright (c) 2019 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
from config import BOT_ACCESS_TOKEN
from compute import *
import sys, json
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Generate a snapshot of what the camera sees at the specified time and return a link to that image.
# https://api.meraki.com/api_docs#generate-a-snapshot-of-what-the-camera-sees-at-the-specified-time-and-return-a-link-to-that-image
def generate_snapshot(serial, timestamp=None, session=None):
    headers = {'X-Cisco-Meraki-API-Key': MERAKI_API_KEY, 'Content-Type': 'application/json'}

    print("Serial: ", serial)
    print("Timestamp: ", timestamp)

    if not session:
        session = requests.Session()

    if timestamp:
        response = session.post(
            f'https://api.meraki.com/api/v0/networks/{NETWORK_ID}/cameras/{serial}/snapshot',
            headers=headers,
            json={'timestamp': timestamp}
        )
    else:
        response = session.post(
            f'https://api.meraki.com/api/v0/networks/{NETWORK_ID}/cameras/{serial}/snapshot',
            headers=headers
        )
    print(response)
    print("Response status code: ",response.status_code)
    print("Response text: ",response.text)
    if response.ok:
        snapshot_link = response.json()['url']
        return snapshot_link
    else:
        return None

# Download file from URL and write to local tmp storage
def download_file(session, file_name, file_url):
    attempts = 1
    while attempts <= 30:
        r = session.get(file_url, stream=True)
        if r.ok:
            print(f'Retried {attempts} times until successfully retrieved {file_url}')
            temp_file = f'/tmp/{file_name}.jpg'
            with open(temp_file, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            return temp_file
        else:
            attempts += 1
    print(f'Unsuccessful in 30 attempts retrieving {file_url}')
    return None

# Send a message with file attached from local storage
def send_file(session, headers, payload, message, file_path, file_type='text/plain'):
    # file_type such as 'image/png'
    if 'toPersonEmail' in payload:
        p = {'toPersonEmail': payload['toPersonEmail']}
    elif 'roomId' in payload:
        p = {'roomId': payload['roomId']}
    p['markdown'] = message
    p['files'] = (file_path, open(file_path, 'rb'), file_type)
    m = MultipartEncoder(p)
    session.post('https://api.ciscospark.com/v1/messages', data=m,
                      headers={'Authorization': headers['authorization'],
                               'Content-Type': m.content_type})

# Send a message in Webex Teams
def post_message(session, headers, payload, message):
    payload['markdown'] = message
    session.post('https://api.ciscospark.com/v1/messages/',
                 headers=headers,
                 json=payload)

# Main function
if __name__ == '__main__':
    # Get credentials and object count
    #(api_key, org_id, chatbot_token, user_email, mv_serial, home_macs) = gather_credentials()
    theText = sys.argv[1]
    destination_email = sys.argv[2]
    serial_number = sys.argv[3]
    timestamp = sys.argv[4]

    # Establish session
    session = requests.Session()

    # Format message
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': f'Bearer {BOT_ACCESS_TOKEN}'
    }
    payload = {
        'toPersonEmail': destination_email,
    }

    # retrieve the snapshot for that time
    theScreenShotURL = ""

    # Generating screenshot for latest time since when I selected a timestamp that was too close
    # to real time the camera had not had a chance to store it and make it available for sending
    print("About to generate snapshot with serial ",serial_number,' and session ',session)
    theScreenShotURL=generate_snapshot(serial_number, None, session)

    print("theScreenShotURL=",theScreenShotURL)

    print(theText)


    file_url=theScreenShotURL
    if file_url:  # download/GET image from URL
        temp_file = download_file(session, serial_number, file_url)
        if temp_file:
            send_file(session, headers, payload, theText, temp_file, file_type='image/jpg')
        else:
            theText += ' (snapshot unsuccessfully retrieved)'
            post_message(session, headers, payload, theText)
    else:
        theText += ' (snapshot unsuccessfully requested)'
        post_message(session, headers, payload, theText)