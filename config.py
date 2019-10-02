# this config file contains multiple variables utilized throughout the functionality of this code

MERAKI_API_KEY = ""
NETWORK_ID = ""

# ------------ Variables for Webex Teams bot notification -------------------------
BOT_ACCESS_TOKEN = "ZWNiNTcyNWYtODBhYy00MzI2LWJiNWItNmNjYjU1ZDBmZjBkZWZiM2JkOWUtNTI4"
CROWD_EVENTS_MESSAGE_RECIPIENT="user@test.com"

# ------------Variables utilized in mvSense.py-----------------------------------
TEST_CAMERA_SERIAL="XXXXXXXX"

MQTT_SERVER = "test.mosquitto.org"
#MQTT_SERVER = "MQTT_IP_DOMAIN"
MQTT_PORT = 1883
#this specifies the camera and zone we are interested in
MQTT_TOPIC = "/merakimv/"+TEST_CAMERA_SERIAL+"/0"


# Array of cameras serial numbers
COLLECT_CAMERAS_SERIAL_NUMBERS = ["*"]
# Array of zone id, all is *. eg ["*"]
COLLECT_ZONE_IDS = ["*"]
# Array of valid cameras with MVSense API
COLLECT_CAMERAS_MVSENSE_CAPABLE=["MV12", "MV22", "MV72"]

# motion trigger setting
MOTION_ALERT_PEOPLE_COUNT_THRESHOLD = 1
# message count to trigger an action
MOTION_ALERT_ITERATE_COUNT = 50
# least number of people to send action
MOTION_ALERT_TRIGGER_PEOPLE_COUNT = 1
# pause time after alert finished triggering
MOTION_ALERT_PAUSE_TIME = 5
# number of messages until action time out
TIMEOUT = 20
# number of miliseconds of dwell time to alert on
MOTION_ALERT_DWELL_TIME = 60000


# --------Variables utilized in compute.py----------------------

# number of seconds to filter out in cmxFilterHours()
# will remove MAC addresses that have been seen for over this given amount of time
_FILTER_TIME = 3600

# number of seconds between timestamps in getCMXHours() which still constitutes a session
# if a device is not seen for longer that this time threshold, the "session" will end
# and this will be logged as a visit.
# if the same device is seen again outside of this threshold, it will start a new visit session
_SESSION_TIME = 300

# utilized in correlation()
# defines a leeway period before inTime and after outTime of mvSense data in which cmx data should still be considered, as the times may not exactly match up due to granularity differences
timeWindow = 30

# utilized in correlation()
# defines threshold of signal strength that will be considered
# the closer the device, the larger the rssiThreshold
# tesing shows 45 and above is about 1 meter away from access point
rssiThreshold = 45
