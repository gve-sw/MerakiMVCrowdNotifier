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
import csv
import shutil
import json, requests
import time
from datetime import datetime
from config import NETWORK_ID, MERAKI_API_KEY



# gets meraki MV video link
def getMVLink(serial_number,timestamp):
    # Get video link
    url = "https://api.meraki.com/api/v0/networks/"+NETWORK_ID+"/cameras/"+str(serial_number)+"/videoLink?timestamp="+str(timestamp)

    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.request("GET", url, headers=headers)
    # print(resp)
    if int(resp.status_code / 100) == 2:
        return(resp.text)
    return('link error')


# gets meraki MV activity summary overview for a camera
def getMVOverview(serial_number):
    # Get video link
    url = "https://api.meraki.com/api/v0/devices/"+serial_number+"/camera/analytics/overview?timespan=604800"

    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.request("GET", url, headers=headers)
    print("URL: ", url)
    print("Call to MV overview response: ", resp)
    if int(resp.status_code / 100) == 2:
        return(resp.text)
    return('link error')


# gets meraki MV zones for a camera
def getMVZones(serial_number):
    # Get video link
    url = "https://api.meraki.com/api/v0/devices/"+serial_number+"/camera/analytics/zones"

    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    resp = requests.request("GET", url, headers=headers)
    print("URL: ", url)
    print("Call to MV zones response: ", resp)
    if int(resp.status_code / 100) == 2:
        return(resp.text)
    return('link error')


# gets meraki MV activity summary overview for a camera
def getCameraScreenshot(serial_number,timestamp):
    # Get video link
    url = "https://api.meraki.com/api/v0/networks/"+NETWORK_ID+"/cameras/"+serial_number+"/snapshot"

 #   headers = {
 #       'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
#      "Content-Type": "application/json"
 #   }
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'cache-control': "no-cache",
    }
    querystring = {"timestamp": timestamp}

    payload = ""

    resp = requests.request("POST", url, data=payload, headers=headers, params=querystring)
    print("URL: ", url)
    print("Timestamp: ",timestamp)
    print("Call to camera snapshot response: ", resp)
    if int(resp.status_code / 100) == 2:
        return(resp.text)
    return('link error')

# gets meraki MV history summary overview for a camera
def getMVHistory(serial_number, zone):
    # Get video link
    url = "https://api.meraki.com/api/v0/devices/"+serial_number+"/camera/analytics/zones/"+zone+"/history?timespan=50400"

    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"""
    }
    resp = requests.request("GET", url, headers=headers)
    # print(resp)
    if int(resp.status_code / 100) == 2:
        return(resp.text)
    return('link error')


# gets meraki devices
def getDevices():
    # Get video link
    url = "https://api.meraki.com/api/v0/networks/"+NETWORK_ID+"/devices/"

    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"""
    }
    resp = requests.request("GET", url, headers=headers)
    # print(resp)
    if int(resp.status_code / 100) == 2:
        return(resp.text)
    return('link error')


