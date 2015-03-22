#!/usr/bin/env python
"""
This module connects to a Netatmo device and outputs measured data.  The Netatmo data can then be processed
by another module to output over to an LCD display.

A JSON file is required to store the login information.  This should not be tracked by git!!  By default the
login file is login_data.json and has the following contents:

{"client_secret": "<CLIENT SECRET>", "client_id": "<CLIENT ID>", "password": "<PASSWORD>", "username": "<USERNAME>"}
"""
__author__ = 'Andy Kobyljanec'


import requests
import json


class NetatmoDevice:
    LOGIN_FILE = 'login_data.json'
    CONNECT_URL = "https://api.netatmo.net/oauth2/token"
    DEVICE_URL = "https://api.netatmo.net/api/devicelist"
    MEASURE_URL = "https://api.netatmo.net/api/getmeasure"

    CLIENT_ID = ""
    CLIENT_SECRET = ""
    ACCESS_TOKEN = ""
    RENEW_TOKEN = ""
    DEVICE_ID = ""

    def __init__(self):
        self.connect()

    def connect(self):
        f = open(self.LOGIN_FILE, 'r')
        login_data = json.loads(f.read())
        f.close()

        # open the login_data.json file and copy the login data
        self.CLIENT_ID = login_data['client_id']
        self.CLIENT_SECRET = login_data['client_secret']
        username = login_data['username']
        password = login_data['password']

        # create an authentication request
        payload = {'grant_type': 'password', 'client_id': self.CLIENT_ID, 'client_secret': self.CLIENT_SECRET,
                   'username': username, 'password': password}
        r = requests.post(self.CONNECT_URL, data=payload)

        if r.status_code == 200:
            # save the access token
            self.ACCESS_TOKEN = r.json()['access_token']
            self.RENEW_TOKEN = r.json()['refresh_token']

            # get a device id
            payload = {'access_token': self.ACCESS_TOKEN}
            r = requests.get(self.DEVICE_URL, params=payload)

            self.DEVICE_ID = r.json()['body']['devices'][0]['_id']

            print("netatmo connected")

    def renew(self):
        payload = {'grant_type': 'refresh_token', 'refresh_token': self.RENEW_TOKEN, 'client_id': self.CLIENT_ID,
                   'client_secret': self.CLIENT_SECRET}
        r = requests.post(self.CONNECT_URL, data=payload)

        if r.status_code == 200:
            print("refreshed token successfully")
        else:
            print("refreshed token failed")

    def measure(self, type):
        """
        reads the most recent measurement from the netatmo device.  Information on the API available at
        https://dev.netatmo.com/doc/methods/getmeasure

        :param type: measurement type, Temperature, Co2, Humidity, etc
        :return:
        """
        measurement = None

        payload = {'device_id': self.DEVICE_ID, 'type': type, 'access_token': self.ACCESS_TOKEN, 'scale': 'max',
                   'limit': '1'}

        r = requests.get(self.MEASURE_URL, params=payload)

        # renew the token if it is expired
        while r.status_code != 200:
            self.renew()
            r = requests.get(self.MEASURE_URL, params=payload)

        measurement = r.json()['body'][0]['value'][0][0]

        return measurement


if __name__ == "__main__":
    device = NetatmoDevice()
    print(device.measure('Temperature'))