NETNAME = None
NETPASS = None

SERVIP = None
SERVPORT = None

CONFIGFILENAME = "sensor.cfg"

with open(CONFIGFILENAME, 'r') as cfile:
    lines = cfile.readlines()
    NETNAME = lines[0][:-1]
    NETPASS = lines[1][:-1]
    SERVIP = lines[2][:-1]
    SERVPORT = int(lines[3][:-1])


import machine
import dht
import network
import time
import socket
import ubinascii

mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()


status_led = machine.Pin(2, machine.Pin.OUT)
led_state = True # annoyingly, status_led.on() turns it off

def do_connect():
    global led_state
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect(NETNAME, NETPASS)
        while not sta_if.isconnected():
            if led_state:
                status_led.on()
                led_state = False
            else:
                status_led.off()
                led_state = True
            time.sleep(0.25)
    print('network config:', sta_if.ifconfig())
    status_led.off()
    

adc = machine.ADC(0)
d = dht.DHT11(machine.Pin(5))

def do_run():
    global status_led
    global mac
    
    socket_connected = False
    
    while True:
        
        while not socket_connected:
            try:
                s = socket.socket()
                s.connect((SERVIP, SERVPORT))
                s.send("Initializing link...\n")
                socket_connected = True
            except OSError:
                print("Socket connection failed... waiting.")
                # pulse LED to indicate problem
                status_led.on()
                time.sleep(0.1)
                status_led.off()
                time.sleep(0.1)
                status_led.on()
                time.sleep(0.1)
                status_led.off()
                time.sleep(0.1)
                status_led.on()
                time.sleep(0.1)
                status_led.off()
                
        status_led.on()
        d.measure()
        msg = "Soil: " + str(adc.read()) + "; temp: " + str(d.temperature()) + "; hum: " + str(d.humidity()) + "; from " + mac + "\n"
        print(msg)
        try:
            q = s.send(msg)
        except OSError:
            socket_connected = False
        print("Sent ", q, " bytes.")
        status_led.off()
        time.sleep(2)

