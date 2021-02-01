# RebootPoEDevice

A little script to automatically power cycle devices connected to a PoE switch.

## Installation

### Config
`cp config.ini.example config.ini`
Fill in the config fields. Leave fields blank if you dont use them (MADmin auth, discord).

`rebootafter` specifies the time in minutes after a device without data should be power cycled. `rebootcooldown` specifies a time in minutes after a powercycled device should be ignored by the script.

### Python requirements
`pip install -r requirements.txt`

### Devices
`cp devices.json.example devices.json`
The key is the origin, the value is the PoE portnumber.


## Running
`python rebootpoedevice.py`