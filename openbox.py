#!/usr/bin/python

import paho.mqtt.client as mqtt
import socket
import time

mqttIP = '192.168.0.254'
mqttPort = 1883
mqttFlag = False
client = mqtt.Client()
client.username_pw_set(username="mqtt", password="skabent0mqtt")

def onConnect(client, userdata, flags, rc):
    global myIP
    global mqttIP
    global mqttFlag
    mqttFlag = True
    time.sleep(0.2)
#    client.publish("box/all/cup","{\"timestamp\":123, \"datahold\":{\"state\":\"OPEN\"}}")
#    time.sleep(0.1)

def mqttSetup():
    client.on_connect = onConnect
    try:
        client.connect(mqttIP, mqttPort, 5)
    except socket.error:
        print ("Can not connect")
    else: 
        client.loop_start()
        time.sleep(0.2)
        client.publish("box/all/cup","{\"timestamp\":123, \"datahold\":{\"state\":\"OPEN\"}}")
        time.sleep(0.1)

mqttSetup()
time.sleep(0.5)