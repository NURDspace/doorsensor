#!/usr/bin/python
import socket
import time
import traceback
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
GPIO.setmode(GPIO.BOARD)

PASSWORD = 'NRD'
NURDBOT = ('vinculum', 19107)
MOSQUITTO = ('arbiter', 1883)
DOORS = {13:'front_door'}

mqttc = mqtt.Client()
status = {}

def callback(chan):
    global status
    global DOORS
    print(time.strftime('%H:%M:%S ')+str(DOORS[chan])+' called callback')
    new = (GPIO.input(chan) ==1)
    if new is not status[chan]:
        time.sleep(2)
        new = (GPIO.input(chan) ==1)
        if new is not status[chan]:
            status[chan] = new
            send()
            print(time.strftime('%H:%M:%S ')+DOORS[chan]+' ('+str(chan)+') is now '+str(status[chan]))

def send():
    global DOORS
    global status
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sng = []
    for door in DOORS:
        callback(door)
        sng.append(DOORS[door]+':'+str(status[door]))
    sng = PASSWORD+';'.join(sng)+'\n'
    try:
        s.connect(NURDBOT)
        s.sendall(sng)
    except:
        print('Connection failure')
    finally:
        s.close()
    try:
        mqttc.connect(*MOSQUITTO)
        mqttc.publish('space/status_switch',status[DOORS.keys()[0]],qos=1,retain=True)
        mqttc.disconnect()
    except:
        print(traceback.format_exc())
        print('MQTT Connection failure')


for door in DOORS:
    GPIO.setup(door, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    status[door] = (GPIO.input(door) == 1) 

send()
print('Current locked doors: '+str([DOORS[door]+':'+str(status[door]) for door in DOORS]))

for door in DOORS:
    GPIO.add_event_detect(door, GPIO.BOTH, callback=callback,bouncetime=800)

while True:
    time.sleep(30)
    send()
