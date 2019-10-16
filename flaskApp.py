#!/usr/bin/env python3
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
# web application GUI


from flask import Flask, render_template, request, jsonify, url_for, json, redirect
import csv
import shutil
from datetime import datetime
from flask_googlecharts import GoogleCharts
from flask_googlecharts import BarChart, MaterialLineChart, ColumnChart
from flask_googlecharts.utils import prep_data
from config import COLLECT_CAMERAS_MVSENSE_CAPABLE, NETWORK_ID, TEST_CAMERA_SERIAL
from compute import *
import time
import pytz    # $ pip install pytz
import tzlocal # $ pip install tzlocal
#from flask_wtf import Form
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Email, NumberRange
import os

import time
import paho.mqtt.client as mqtt
from config import MQTT_SERVER,MQTT_PORT,MERAKI_API_KEY,NETWORK_ID,MOTION_ALERT_ITERATE_COUNT,MOTION_ALERT_TRIGGER_PEOPLE_COUNT,MOTION_ALERT_PAUSE_TIME,TIMEOUT
from config import BOT_ACCESS_TOKEN
from webexteamssdk import WebexTeamsAPI


MOTION_ALERT_PEOPLE_COUNT_THRESHOLD = 2
MOTION_ALERT_DWELL_TIME = 60000
CROWD_EVENTS_MESSAGE_RECIPIENT= ''



app = Flask(__name__)
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
charts = GoogleCharts(app)

webexApi = WebexTeamsAPI(access_token=BOT_ACCESS_TOKEN)


_MONITORING_TRIGGERED = False

_MONITORING_MESSAGE_COUNT = 0

_MONITORING_PEOPLE_TOTAL_COUNT = 0

_TIMESTAMP = 0

_TIMEOUT_COUNT = 0

_TEST_TRIG_START=0

ALL_CAMERAS_AND_ZONES={}
MQTT_TOPICS = []


client = mqtt.Client()


def load_all_cameras_details():
    global ALL_CAMERAS_AND_ZONES
    global MQTT_TOPICS
    devices_data = getDevices()
    if devices_data != 'link error':
        AllDevices = json.loads(devices_data)

        for theDevice in AllDevices:
            theModel = theDevice["model"]
            if theModel[:4] not in COLLECT_CAMERAS_MVSENSE_CAPABLE:
                continue

            #create dict entry in ALL_CAMERAS_AND_ZONES for this camera, just the top level values for now
            ALL_CAMERAS_AND_ZONES[theDevice["serial"]]={'name': theDevice["name"],
                                                        'zones': {}}
            zonesdetaildata = getMVZones(theDevice["serial"])
            if zonesdetaildata == 'link error':
                continue
            #print("getMVZones returned:", zonesdetaildata)
            MVZonesDetails = json.loads(zonesdetaildata)

            #now fill out the zones and corresponding details
            theZoneDetailsDict={}
            for zoneDetails in  MVZonesDetails:
                #we are not interested in cameras that have no zones defined, so we do not pull the details into the dict and
                #we do not add it to the MQTT_TOPICS to monitor
                if zoneDetails["zoneId"]!='0':
                    theZoneDetailsDict[zoneDetails["zoneId"]]={'label':zoneDetails["label"],
                                                               '_MONITORING_TRIGGERED': False,
                                                               '_MONITORING_MESSAGE_COUNT':0,
                                                               '_MONITORING_PEOPLE_TOTAL_COUNT':0,
                                                               '_TIMESTAMP':0,
                                                               '_TIMEOUT_COUNT':0,
                                                               '_TEST_TRIG_START':0}
                    MQTT_TOPICS.append("/merakimv/" + theDevice["serial"] + "/" + zoneDetails["zoneId"])
            ALL_CAMERAS_AND_ZONES[theDevice["serial"]]['zones'] = theZoneDetailsDict

        print("All cameras and zones info: ", ALL_CAMERAS_AND_ZONES)
        print("MQTT Topics: ",MQTT_TOPICS)


def collect_zone_information(topic, payload):
    ## /merakimv/Q2GV-S7PZ-FGBK/123

    parameters = topic.split("/")
    serial_number = parameters[2]
    zone_id = parameters[3]


    # detect motion
    global ALL_CAMERAS_AND_ZONES

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
            notify(serial_number, zone_id, _MONITORING_PEOPLE_TOTAL_COUNT, _TIMESTAMP, payload['ts'])
            print('---ALERTED---')
            _TEST_TRIG_START = 0
    else:
        _TEST_TRIG_START = 0



def notify(serial_number, zone_id, count,timestampIN, timestampOUT):
    with open('mvData.csv','a') as csvfile:
        fieldnames = ['Serial', 'ZoneID', 'Time In','Time Out','Count']
        writer=csv.DictWriter(csvfile,fieldnames=fieldnames)
        writer.writerow({'Serial':serial_number,'ZoneID':zone_id, 'Time In':timestampIN,'Time Out':timestampOUT, 'Count':count})


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    for topic in MQTT_TOPICS:
        client.subscribe(topic)


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):

    payload = json.loads(msg.payload.decode("utf-8"))

    parameters = msg.topic.split("/")
    #print("received a message: ", payload, " with parameters: ",parameters)
    serial_number = parameters[2]
    message_type = parameters[3]
    #print("received a message type: ",message_type," serial: ",serial_number," index: ", index)


    if message_type != 'raw_detections' and message_type != 'light':
        print(message_type)
        collect_zone_information(msg.topic, payload)
    #if message_type == '0':
    #    collect_zone_information(msg.topic,payload)
    #    print("processing msg with topic: ", msg.topic)


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

class ConfigurationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    peopleCount = StringField('PeopleCount', validators=[DataRequired()])
    dwellTime = StringField('DwellTime', validators=[DataRequired()] )


@app.route('/start_mvsense')
def startMVSense():
    #global theMVSenseThread
    #theMVSenseThread.start()
    mvSenseThreadStart()
    return 'ok'

@app.route('/stop_mvsense')
def stopMVSense():
    #global theMVSenseThread
    #theMVSenseThread.stop()
    mvSenseThreadStop()
    return 'ok'

@app.route('/mvSense',methods=['GET','POST'])
def mvSense():
    # open mv sense data
    data = []
    with open('mvData.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        arrayCount=0
        flag=0
        for row in reader:
            print(row['Time In'])
            #link = getMVLink(TEST_CAMERA_SERIAL,row['Time In'])
            link = getMVLink(row['Serial'],row['Time In'])
            link = link.replace('{"url":"',"")
            link = link.replace('"}',"")
            #TODO Pass down the name of the camera instead of serial and the name of the zone
            data.append({'Serial':row['Serial'],'ZoneID':row['ZoneID'],'timeIn':datetime.fromtimestamp(float(row['Time In'])/1000).strftime('%m-%d,%H:%M'),'timeOut':datetime.fromtimestamp(float(row['Time Out'])/1000).strftime('%m-%d,%H:%M'),'count':row['Count'],'link':link})
    # print(len(data[0]['timestamps']))
    return render_template("mvSense.html",data=data, numPersons=MOTION_ALERT_PEOPLE_COUNT_THRESHOLD, numSeconds=int(MOTION_ALERT_DWELL_TIME/1000))


@app.route('/pleasewait',methods=['GET'])
def pleasewait():
    # this is for the GET to show the overview
    return render_template("pleasewait.html", theReason='Getting crowd events for cameras on network: ' + NETWORK_ID)



@app.route('/',methods=['GET','POST'])
@app.route('/index',methods=['GET','POST'])
def index():
    global MOTION_ALERT_PEOPLE_COUNT_THRESHOLD, CROWD_EVENTS_MESSAGE_RECIPIENT, MOTION_ALERT_DWELL_TIME
    form = ConfigurationForm()
    if form.validate_on_submit():
        #copy the values from the form into variables
        CROWD_EVENTS_MESSAGE_RECIPIENT=form.email.data
        MOTION_ALERT_PEOPLE_COUNT_THRESHOLD=int(form.peopleCount.data)
        MOTION_ALERT_DWELL_TIME=int(form.dwellTime.data)
        print("set email:", CROWD_EVENTS_MESSAGE_RECIPIENT, " PeopleCount: ",MOTION_ALERT_PEOPLE_COUNT_THRESHOLD," and dwellTime: ",MOTION_ALERT_DWELL_TIME)
        return render_template("index.html", form=form)
    return render_template("index.html", form=form)


@app.route('/mvOverview',methods=['GET','POST'])
def mvOverview():
    # extract MVSense over view data for a camera from the analytics API
    MVZones = []
    animation_option = {"startup": True, "duration": 1000, "easing": 'out'}

    #First we have the logic for creating the page with all the historical details of zone below,
    #further down is the logic to show the Overview of all cameras and their respective zones
    if request.method == 'POST':
        # This is for the historical detail
        zoneDetails = request.form['zone_details']
        print("zoneDetails=",zoneDetails)
        #zoneDetailsTuple contains: [camera serial, camera name, zone id, zone name]
        zoneDetailsTuple=zoneDetails.split(',')
        theSERIAL=zoneDetailsTuple[0]
        theCameraNAME=zoneDetailsTuple[1]
        theZoneID=zoneDetailsTuple[2]
        theZoneNAME=zoneDetailsTuple[3]

        data = getMVHistory(theSERIAL,theZoneID)
        if data != 'link error':


            print("getMVHistory returned:", data)

            MVHistory = json.loads(data)
            # add a chart

            # now create the chart object using the serial as the name and the name of the device as the title
            mv_history_chart = ColumnChart("mvhistorychart", options={"title": "Camera: "+theCameraNAME+" Zone: "+theZoneNAME,
                                                                                 "width": 1000,
                                                                                 "height": 500,
                                                                                 "hAxis.title": "Hour",
                                                                                 "animation": animation_option})
            mv_history_chart.add_column("string", "Zone")
            mv_history_chart.add_column("number", "Visitors")
            print(data)
            the_rows = []
            theHoursDict = dict()
            theHoursMaxEntrancesDict = dict()
            theHoursMaxEntrancesTimestampDict = dict()
            theLocalHoursMaxEntrancesTimestampDict = dict()

            for j in range(len(MVHistory)):
                # grab all events in MVHistory, then
                # tabulate and summarize in hour blocks
                # example startTS: "2019-08-05T17:06:46.312Z" example endTs: "2019-08-05T17:07:46.312Z"
                # also, for each hour that has entrances, select the timeframe where there are
                # the most and extract a snapshot 30 seconds after that timestamp to show below in the page

                thisStartTs = MVHistory[j]["startTs"]
                thisEndTs = MVHistory[j]["endTs"]

                thisHour = thisEndTs.partition('T')[2][:2]

                theEndTsTimeStamp=datetime.strptime(thisEndTs, "%Y-%m-%dT%H:%M:%S.%fZ")

                thisMinuteMedTimestamp= time.mktime(theEndTsTimeStamp.timetuple())-30
                thisMinuteMedISOts=datetime.fromtimestamp(thisMinuteMedTimestamp).isoformat()+"Z"

                #convert to localtimezone
                local_timezone = tzlocal.get_localzone()  # get pytz tzinfo
                local_timezone_str = str(local_timezone)
                theLocalEndTsTimeStamp = theEndTsTimeStamp.replace(tzinfo=pytz.utc).astimezone(local_timezone)

                thislocalMinuteMedTimestamp= time.mktime(theLocalEndTsTimeStamp.timetuple())-30
                thislocalMinuteMedISOts = datetime.fromtimestamp(thislocalMinuteMedTimestamp).isoformat() + "Z"
                localHour = thislocalMinuteMedISOts.partition('T')[2][:2]

                #print("Timestamp string:",thisEndTs )

                #print("Numerical equivalent: ", thisMinuteMedTimestamp)
                #print("Local Numerical equivalent: ", thislocalMinuteMedTimestamp)
                #print("ISO equivalent: ", thisMinuteMedISOts)
                #print("local ISO equivalent: ", thislocalMinuteMedISOts)

                thisEntrances = MVHistory[j]["entrances"]

                # Now we will use localHour instead of thisHour as the Dict key to hold the accounting for body
                # detection per hour since that is what is shown on the graph, it should behave the same otherwise
                # as when we used thisHour originally, but show a local hour instead of UTC which was confusing.

                if localHour in theHoursDict.keys():
                    #increase the number of entrances of this hour slot
                    theHoursDict[localHour]=theHoursDict[localHour]+thisEntrances
                    #check to see if the entrances for this minute are the most for this hour
                    if thisEntrances>theHoursMaxEntrancesDict[localHour]:
                        #if so, make these entrances the most for the timeframe and save the timestamp for the
                        #middle of the minute with the most entrances
                        theHoursMaxEntrancesDict[localHour]=thisEntrances
                        theHoursMaxEntrancesTimestampDict[localHour]=thisMinuteMedISOts
                        #keep track of local version as well
                        theLocalHoursMaxEntrancesTimestampDict[localHour]=thislocalMinuteMedISOts

                else:
                    #if this is the first time we see this timeslot, make the current entrances
                    #the starting balance for the dict entry
                    theHoursDict[localHour] = thisEntrances
                    theHoursMaxEntrancesDict[localHour] = thisEntrances
                    #only keep timestamp if there is at least one entry detected
                    if thisEntrances>0:
                        theHoursMaxEntrancesTimestampDict[localHour] = thisMinuteMedISOts
                        theLocalHoursMaxEntrancesTimestampDict[localHour] = thislocalMinuteMedISOts
                    else:
                        theHoursMaxEntrancesTimestampDict[localHour]=''
                        theLocalHoursMaxEntrancesTimestampDict[localHour]=''


            for dEntryKey in theHoursDict.keys():
                the_rows.append([dEntryKey, theHoursDict[dEntryKey]])

            mv_history_chart.add_rows(the_rows)
            charts.register(mv_history_chart)

            print("Max Entrances Timestamps: ", theHoursMaxEntrancesTimestampDict)
            print("Max Local Entrances Timestamps: ", theLocalHoursMaxEntrancesTimestampDict)

            #theScreenshots is an array of arays in the format [ timestamp string,  snapshot URL ]
            #this is to be passed to the form that will render them
            theScreenshots=[]

            for dTimeStampKey in theHoursMaxEntrancesTimestampDict.keys():
                if theHoursMaxEntrancesTimestampDict[dTimeStampKey]!='':
                    screenShotURLdata=getCameraScreenshot(theSERIAL,theHoursMaxEntrancesTimestampDict[dTimeStampKey])
                    print("getCameraSCreenshot returned: ",screenShotURLdata)
                    if  screenShotURLdata != 'link error':
                        screenShotURL = json.loads(screenShotURLdata)
                        #Passing theLocalHoursMaxEntrancesTimestampDict[dTimeStampKey] instead of theHoursMaxEntrancesTimestampDict[dTimeStampKey] below
                        #to show a local timestamp we calculated in a previous loop
                        theScreenshots.append([ theLocalHoursMaxEntrancesTimestampDict[dTimeStampKey], screenShotURL["url"]])

            # wait for the URLs to be valid
            print("Waiting 10 seconds...")
            time.sleep(10)
            return render_template("mvHistory.html", historyChart=mv_history_chart, snapshotsArray=theScreenshots, localTimezone=local_timezone_str)
    else:

        devices_data=getDevices()
        if devices_data != 'link error':

            AllDevices=json.loads(devices_data)

            #theDeviceCharts is just a list (array) of the names of the charts constructed with the
            #google charts flask library. They are to be iterated through to place on the History/details page
            theDeviceCharts=[]
            #theDeviceDetails is a list of the details of each camera device. Each entry has a serial number, label and
            #a list of zones for which there is zoneID and label
            theDeviceDetails=[]

            theChartNum=0

            for theDevice in AllDevices:
                theModel=theDevice["model"]

                if theModel[:4] not in COLLECT_CAMERAS_MVSENSE_CAPABLE:
                    continue

                data=getMVOverview(theDevice["serial"])
                if data == 'link error':
                    continue

                print("getMVOverview returned:" , data)
                MVZones=json.loads(data)

                zonesdetaildata=getMVZones(theDevice["serial"])
                if zonesdetaildata == 'link error':
                    continue

                print("getMVZones returned:" , zonesdetaildata)
                MVZonesDetails=json.loads(zonesdetaildata)

                # add a chart
                #first add the name of the chart to the list of charts to be displayed in the page
                theDeviceCharts.append("chart"+str(theChartNum))

                #now append the top level details of the camera for this chart to theDeviceDetails
                theDeviceDetails.append([theDevice["serial"],theDevice["name"],[]])

                #now create the chart object using the serial as the name and the name of the device as the title
                mv_overview_chart = ColumnChart("chart"+str(theChartNum), options={"title": theDevice["name"],
                                                                          "width": 800,
                                                                          "height": 400,
                                                                          "hAxis.title": "Hour",
                                                                          "animation": animation_option})
                mv_overview_chart.add_column("string", "Zone")
                mv_overview_chart.add_column("number", "Visitors")
                print(data)
                the_rows = []
                for j in range(len(MVZones)):
                    thisZone=MVZones[j]
                    #assuming same number of zone entries overviews than number of zones here
                    thisZoneDetails=MVZonesDetails[j]
                    the_rows.append([ str(thisZoneDetails["label"]), thisZone["entrances"] ])
                    # store away the zoneID and serial of the camera to pass to the form so when someone clicks
                    # on a bar or button to expand detail, it comes back to this function in the POST section
                    # to know which zone from which camera to use


                    #we are assuming below that we have a chart per each MV capable camera, if that changes
                    # we need to figure out aonther way to index theDeviceDetails or use some other method
                    # to store/retrieve the data besides a list of lists
                    theDeviceDetails[theChartNum][2].append([thisZoneDetails["zoneId"], thisZoneDetails["label"]])

                mv_overview_chart.add_rows(the_rows)
                charts.register(mv_overview_chart)

                theChartNum+=1

            print("Rendering overview form with:")
            print("allTheDetails=",theDeviceDetails)

            return render_template("mvOverview.html",allTheCharts=theDeviceCharts,allTheDetails=theDeviceDetails)

        else:
            return render_template('error.html'), 404


if __name__ == "__main__":
    load_all_cameras_details()
    app.run(host='0.0.0.0', port=5001, debug=True)
