# Meraki MV Crowd notifier

This demo utilizes Meraki MV Sense camera data to detect when there are a number of persons in view of
the camera in a specific zone for at least a specified period of time (dwell time). Upon detecting an event,
it sends a message and camera snapshot via Webex Teams to a user and resets a timer to start the process over.

It also implements web page that lists the crowd notification events with a URL to the video clip of when the crowds where detected.

![This is what the main user interface and notifications sent by Webex Teams look like:](ScreenShotCrowdApp.png)


## Configuration

The **Config.py** contains all of the global variables and configuration needed throughout the code, including keys and thresholds:

**MERAKI_API_KEY**: This Meraki API Key needed to access the Meraki Dashboard via API. Here are instructions on how to obtain it: https://developer.cisco.com/meraki/meraki-platform/

**NETWORK_ID**: This is is the ID for the Meraki network for which cameras will be considered for monitoring. Only cameras
that have zones defined will be included. 

**BOT_ACCESS_TOKEN**: You need to have a Cisco Webex Teams Bot access token defined in this variable. This way, the application
can send Webex Teams messages and snapshots from the cameras to any destination specified on behalf of that Bot and not have to
create an integration with a real user's credentials.
Here are instructions on how to obtain one: https://developer.webex.com/docs/bots

**MQTT_SERVER**: The MQTT broker ip or domain ("test.mosquitto.org" for example)

**MQTT_PORT**: is the MQTT broker port being utilized (usually 1883)

**COLLECT_CAMERAS_MVSENSE_CAPABLE**: Array of valid cameras with MVSense API. Default value=["MV12", "MV22", "MV72"]

**MOTION_ALERT_ITERATE_COUNT**: is the minimum number of mqtt messages counted to indicate that an activity has successfully occurred. Default value = 50

**MOTION_ALERT_TRIGGER_PEOPLE_COUNT**: is the minimum number of people needed to successfully complete and activity. Default value = 1

**MOTION_ALERT_PAUSE_TIME**: is the pause time after alert finished triggering. Default value = 5

**TIMEOUT**: is the number of messages until action times out due to in activity (will then check whether minimum alert iterate count is met to determine activity success). Default value = 20

Please note that the actual email address of the Webex Teams recipient,  "Dwell Time" and "People Count" used to determine crowd events are not set in the **config.py** file. Those are collected in the initial page of the application before the user initiates detection.


---
## MV Sense Camera Setup  
This sample application leverages the  Meraki MV camera API and MQTT capability to create a notification service.


More information on MV Sense can be found here: https://developer.cisco.com/meraki/build/mv-sense-documentation/

---
## MV Sense confguration and setting up MQTT

1. In the Meraki dashboard, go to **Cameras > [Camera Name] > Settings > Sense** page.
2. Click **Add or edit MQTT Brokers > New MQTT Broker** and add you broker information. For testing/trial you can find public broker at [here](https://github.com/mqtt/mqtt.github.io/wiki/public_brokers).


---
## Running the Code 
1. Make sure Python 3 is installed
2. Make sure pip is installed (https://pip.pypa.io/en/stable/installing/ for more information on pip)
3. Enter 'pip install -r requirements.txt' into command line to download necessary libraries
4. Ensure all elements of the **config.py** file are completed
5. To run the flask application, enter ```python flaskApp.py``` in another terminal window and navigate your browser to the given url address (example: http://0.0.0.0:5001)
6. Enter values on the index page of the Flask application before initiating detection of crowd events:
- **Email** is the email address of the Webex Teams user that will receive the notifications.
- **PeopleCount** is the number of persons that can be seen in a particular zone in a camera that will be tracked to determine a crowd event 
- **DwellTime** is the number of seconds that need to transcur with at least PeopleCount persons detected to trigger a crowd event
7. Click on the **Set Value** button to set the values before detecting.    
8. Click on the **Start Detecting Crowds** button to start detecting and logging crowd events. The button changes to **Stop Detecting Crowds** so you can click on it again to stop detection. 
9. At any point that there are crowd events already recorded, you can click on the **Events Summary** link at the bottom to navigate to that page where you can see those events with timestamps and click on a link to see the corresponding camera snapshot. 
