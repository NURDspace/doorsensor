#!/usr/bin/python
import socket
import sys, os, time
import traceback
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
try:
   from ConfigParser import ConfigParser
except:
   from configparser import ConfigParser

GPIO.setmode(GPIO.BOARD)
basepath =os.path.dirname(os.path.realpath(__file__))
config = ConfigParser()
configfile=basepath+os.sep+'config.cfg'
if not os.path.exists(configfile):
    configfile=basepath+os.sep+'config.cfg.example'
config.read(configfile)

PASSWORD = config.get('doorsensor','password')
NURDBOT = (config.get('doorsensor','nurdbot_host'),config.getint('doorsensor','nurdbot_port'))
MOSQUITTO = (config.get('doorsensor','mqtt_host'),config.getint('doorsensor','mqtt_port'))
SENSORS = {13:'front_door'}

mqttc = mqtt.Client()
status = {}

def callback(chan):
    '''This callback functions primarily as a debouncer around the send() function.'''
    global status
    global SENSORS
    print(time.strftime('%H:%M:%S ')+str(SENSORS[chan])+' called callback')
    new = (GPIO.input(chan) ==1)
    if new is not status[chan]:
        time.sleep(2)
        new = (GPIO.input(chan) ==1)
        if new is not status[chan]:
            status[chan] = new
            send()
            print(time.strftime('%H:%M:%S ')+SENSORS[chan]+' ('+str(chan)+') is now '+str(status[chan]))

def send():
    '''Get the word out to the various listening posts.'''
    global SENSORS
    global status
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sng = []
    for door in SENSORS:
        callback(door)
        sng.append(SENSORS[door]+':'+str(status[door]))
    sng = PASSWORD+';'.join(sng)+'\n'
    try:
        s.connect(NURDBOT)
        s.sendall(sng)
    except:
        print(traceback.format_exc())
        print('Connection failure')
    finally:
        s.close()
    try:
        mqttc.connect(*MOSQUITTO)
        mqttc.publish('space/status_switch',payload=(1 if status[SENSORS.keys()[0]] else 0),qos=1,retain=True)
        mqttc.disconnect()
    except:
        print(traceback.format_exc())
        print('MQTT Connection failure')


for door in SENSORS:
    GPIO.setup(door, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    status[door] = (GPIO.input(door) == 1) 

send()
print('Current locked doors: '+str([SENSORS[door]+':'+str(status[door]) for door in SENSORS]))

for door in SENSORS:
    GPIO.add_event_detect(door, GPIO.BOTH, callback=callback,bouncetime=800)

while True:
    time.sleep(30)
    send()
