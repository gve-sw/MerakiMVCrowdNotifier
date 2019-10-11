# monitors for motion trigger from Meraki Camera MV Sense and writes it to a .txt file
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
import json, requests
import time
import paho.mqtt.client as mqtt
import csv
from config import MQTT_SERVER,MQTT_PORT,MQTT_TOPIC,MERAKI_API_KEY,NETWORK_ID,COLLECT_CAMERAS_SERIAL_NUMBERS,COLLECT_ZONE_IDS,MOTION_ALERT_PEOPLE_COUNT_THRESHOLD,MOTION_ALERT_ITERATE_COUNT,MOTION_ALERT_TRIGGER_PEOPLE_COUNT,MOTION_ALERT_PAUSE_TIME,MOTION_ALERT_DWELL_TIME,TIMEOUT
from config import BOT_ACCESS_TOKEN, CROWD_EVENTS_MESSAGE_RECIPIENT
from webexteamssdk import WebexTeamsAPI

webexApi = WebexTeamsAPI(access_token=BOT_ACCESS_TOKEN)



_MONITORING_TRIGGERED = False

_MONITORING_MESSAGE_COUNT = 0

_MONITORING_PEOPLE_TOTAL_COUNT = 0

_TIMESTAMP = 0

_TIMEOUT_COUNT = 0

_TEST_TRIG_START=0

client = mqtt.Client()

def collect_zone_information(topic, payload):
    ## /merakimv/Q2GV-S7PZ-FGBK/123

    parameters = topic.split("/")
    serial_number = parameters[2]
    zone_id = parameters[3]
    index = len([i for i, x in enumerate(COLLECT_ZONE_IDS) if x == zone_id])
    # if not wildcard or not in the zone_id list or equal to 0 (whole camera)
    if COLLECT_ZONE_IDS[0] != "*":
        if index == 0 or zone_id == "0":
            return

    # detect motion

    global _MONITORING_TRIGGERED, _MONITORING_MESSAGE_COUNT, _MONITORING_PEOPLE_TOTAL_COUNT, _TIMESTAMP, TIMEOUT, _TIMEOUT_COUNT, _TEST_TRIG_START

    # if motion monitoring triggered
    if _MONITORING_TRIGGERED:

        _MONITORING_MESSAGE_COUNT = _MONITORING_MESSAGE_COUNT + 1

        if _MONITORING_PEOPLE_TOTAL_COUNT < payload['counts']['person']:
            _MONITORING_PEOPLE_TOTAL_COUNT = payload['counts']['person']

        if payload['counts']['person'] > 0:
            _TIMEOUT_COUNT = 0
        elif payload['counts']['person'] == 0:
            _TIMEOUT_COUNT = _TIMEOUT_COUNT + 1

# Enough time has elapsed without action and the minimum number of Motion messages have been received to qualify for successful action
        if _TIMEOUT_COUNT >= TIMEOUT and _MONITORING_MESSAGE_COUNT >= MOTION_ALERT_ITERATE_COUNT:

# Minimum people count reached
            if _MONITORING_PEOPLE_TOTAL_COUNT >= MOTION_ALERT_TRIGGER_PEOPLE_COUNT:
                # notification
                #print('---MESSAGE ALERT---' + serial_number, _MONITORING_PEOPLE_TOTAL_COUNT,_TIMESTAMP,payload['ts'])
                #notify(serial_number, _MONITORING_PEOPLE_TOTAL_COUNT,_TIMESTAMP, payload['ts'])
                #print('---ALERTED---')
                # pause
                time.sleep(MOTION_ALERT_PAUSE_TIME)

            # reset
            _MONITORING_MESSAGE_COUNT = 0

            _MONITORING_PEOPLE_TOTAL_COUNT = 0

            _MONITORING_TRIGGERED = False

            _TIMESTAMP = 0

            _TIMEOUT_COUNT = 0

        # not a registered action
        elif _TIMEOUT_COUNT >= TIMEOUT and _MONITORING_MESSAGE_COUNT < MOTION_ALERT_ITERATE_COUNT:
            # reset
            print('---ALERT DISMISSED---')
            _MONITORING_MESSAGE_COUNT = 0

            _MONITORING_PEOPLE_TOTAL_COUNT = 0

            _MONITORING_TRIGGERED = False

            _TIMESTAMP = 0

            _TIMEOUT_COUNT = 0


    # print(payload['counts']['person'])
    if payload['counts']['person'] >= MOTION_ALERT_PEOPLE_COUNT_THRESHOLD:
        _MONITORING_TRIGGERED = True
        _TIMESTAMP = payload['ts']

    #print("payload "+serial_number+": " + str(payload) +
    #      ", _MONITORING_TRIGGERED : " + str(_MONITORING_TRIGGERED) +
    #      ", _MONITORING_MESSAGE_COUNT : " + str(_MONITORING_MESSAGE_COUNT) +
    #      ", _MONITORING_PEOPLE_TOTAL_COUNT : " + str(_MONITORING_PEOPLE_TOTAL_COUNT)+
    #      ", timeout: "+str(_TIMEOUT_COUNT))
    print(_MONITORING_PEOPLE_TOTAL_COUNT,MOTION_ALERT_PEOPLE_COUNT_THRESHOLD)
    if ( _MONITORING_PEOPLE_TOTAL_COUNT >= MOTION_ALERT_PEOPLE_COUNT_THRESHOLD ):
        _TIMESTAMP = payload['ts']
        print("Timestamp: " + str(_TIMESTAMP) + " TrigTimestamp: " + str(_TEST_TRIG_START)+" diff:"+str(_TIMESTAMP - _TEST_TRIG_START))
        if (_TEST_TRIG_START == 0):
            # start mesuring a dwelling period
            _TEST_TRIG_START = payload['ts']
        if ((_TIMESTAMP - _TEST_TRIG_START) >= MOTION_ALERT_DWELL_TIME):
            theText=u"At least " + str(MOTION_ALERT_PEOPLE_COUNT_THRESHOLD) + " person(s) detected for more than " + str(int(MOTION_ALERT_DWELL_TIME/1000)) + " seconds on camera "+serial_number+" for zone "+str(zone_id)
            print(theText)
            #send message to recipient from Webex Teams bot
            theMessage=webexApi.messages.create(toPersonEmail=CROWD_EVENTS_MESSAGE_RECIPIENT, text=theText)
            print(theMessage)

            print('---MESSAGE ALERT---' + serial_number, _MONITORING_PEOPLE_TOTAL_COUNT, _TIMESTAMP, payload['ts'])
            notify(serial_number, _MONITORING_PEOPLE_TOTAL_COUNT, _TIMESTAMP, payload['ts'])
            print('---ALERTED---')
            _TEST_TRIG_START = 0
    else:
        _TEST_TRIG_START = 0



def notify(serial_number,count,timestampIN, timestampOUT):
    with open('mvData.csv','a') as csvfile:
        fieldnames = ['Time In','Time Out','Count']
        writer=csv.DictWriter(csvfile,fieldnames=fieldnames)
        writer.writerow({'Time In':timestampIN,'Time Out':timestampOUT, 'Count':count})


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    client.subscribe(MQTT_TOPIC)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode("utf-8"))
    parameters = msg.topic.split("/")
    serial_number = parameters[2]
    message_type = parameters[3]
    index = len([i for i, x in enumerate(COLLECT_CAMERAS_SERIAL_NUMBERS) if x == serial_number])


    # filter camera
    if COLLECT_CAMERAS_SERIAL_NUMBERS[0] != "*":
        if index == 0:
            return

    # if message_type != 'raw_detections' and message_type != 'light':
    #     print(message_type)
    #     collect_zone_information(msg.topic, payload)
    if message_type == '0':
        collect_zone_information(msg.topic,payload)


def mvSenseThreadStart():
    # mqtt
    global client
    try:
        client.on_connect = on_connect
        client.on_message = on_message
        # client.username_pw_set("SPMlWZKRd0k9hc1D33Zvi11ncQWUBPJiujrg60X9Q77V7WoZQciW3793NVNdAkjS","")
        client.connect(MQTT_SERVER, MQTT_PORT, 60)
        #client.loop_forever()
        client.loop_start()
    except Exception as ex:
        print("[MQTT]failed to connect or receive msg from mqtt, due to: \n {0}".format(ex))

def mvSenseThreadStop():
    # mqtt
    global client
    try:
        client.loop_stop()
    except Exception as ex:
        print("[MQTT]failed to stop, due to: \n {0}".format(ex))