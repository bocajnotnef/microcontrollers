# Microcontroller Projects

This is a general repository for all my microcontroller projects. I'll eventually break this out into their own repositories, if the individual projects grow big enough.

## Greenhouse

This is a project to automate environmental monitoring and control of a greenhouse. There are (currently) two components; a `sensor.py` module, designed to be deployed on an ESP8266 to collect DHT11 and soil moisture data, and a `server.py` program, designed to be deployed on a raspberry pi to collect the sensor's data and distill it.

The server will eventually grow into command and control for the greenhouse environment, and sensors will be adapted to handle different sensor types.

## Notes

The bin/ directory contains copies of compiled firmware binaries generated by other sources--I do not claim ownership of them.

bin/ Licenses and ownerships:

| filename | responsible organization | governing license|
|----------|--------------------------|------------------|
|esp8266-20171101-v1.9.3.bin|Micropython|MIT|

## Tools

note: might have to modify permissions of `/dev/ttyUSB*`

Use `adafruit-ampy` to copy and list files [github](https://github.com/adafruit/ampy) [usage examples](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/file-operations)

use `picocom` to connect to the board's REPL a la ` picocom /dev/ttyUSB0 -b115200`