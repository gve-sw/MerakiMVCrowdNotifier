from config import BOT_ACCESS_TOKEN
from webexteamssdk import WebexTeamsAPI
from compute import *
import sys, json
from requests_toolbelt.multipart.encoder import MultipartEncoder


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

    webexApi = WebexTeamsAPI(access_token=BOT_ACCESS_TOKEN)

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
    screenShotURLdata = getCameraScreenshot(serial_number, timestamp)
    print("getCameraSCreenshot returned: ", screenShotURLdata)
    if screenShotURLdata != 'link error':
        screenShotURL = json.loads(screenShotURLdata)
        theScreenShotURL = screenShotURL["url"]

    if theScreenShotURL != "":
        theText = theText + ". Screenshot: " + theScreenShotURL

    print(theText)

    # send message to recipient from Webex Teams bot
    #theMessage = webexApi.messages.create(toPersonEmail=destination_email, text=theText)
    #print(theMessage)

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