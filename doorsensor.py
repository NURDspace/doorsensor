#!/usr/bin/python
import socket
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)

PASSWORD = 'NRD'
NURDBOT = ('vinculum.vm.nurd.space', 19107)
DOORS = {7:'front_door',12:'back_door'}

status = {}
for door in DOORS:
    GPIO.setup(door, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    status[door] = (GPIO.input(door) ==0)

def send():
    global DOORS
    global status
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sng = []
    for door in DOORS:
        sng.append(DOORS[door]+':'+str(status[door]))
    sng = PASSWORD+';'.join(sng)+'\n'
    try:
        s.connect(NURDBOT)
        s.sendall(sng)
    except:
        print('Connection failure')
    finally:
        s.close()


send()
print('Current setup: '+str([DOORS[door]+':'+str(status[door]) for door in DOORS]))

def callback(chan):
    global status
    global DOORS
    print(time.strftime('%H:%M:%S ')+str(DOORS[chan])+' called callback')
    new = (GPIO.input(chan) ==0)
    if new is not status[chan]:
        time.sleep(2)
        new = (GPIO.input(chan) ==0)
        if new is not status[chan]:
            status[chan] = new
            send()
            print(time.strftime('%H:%M:%S ')+DOORS[chan]+' ('+str(chan)+') is now '+str(status[chan]))

for door in DOORS:
    GPIO.add_event_detect(door, GPIO.BOTH, callback=callback,bouncetime=800)

while True:
    time.sleep(30)
    send()
