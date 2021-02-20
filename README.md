# RebootPoEDevice

A little script to automatically power cycle devices connected to a PoE switch.

## Installation

**IMPORTANT:** if you use multiple MADmin instances, make sure to have unique origins across them as the origin has to be unique in the devices.json!

### Config
`cp config.ini.example config.ini`
Fill in the config fields.

- `rebootafter` specifies the time in minutes after a device without data should be power cycled.
- `rebootcooldown` specifies a time in minutes after a powercycled device should be ignored by the script.
- `discordwebhook` fill in a webhook url. A little discord message is sent everytime a device getting rebooted.
- `ip` is the ip of your PoE switch.
- `password` is the password of your PoE switch.

### Python requirements
`pip install -r requirements.txt`

### Devices
`cp devices.json.example devices.json`
The key is the origin, the value is the PoE portnumber.

### Servers
`cp servers.json.example servers.json`
Fill in your MADmin server(s). Set `user` and `pass` to `""` or `null` if you dont use any auth.

## Running
`python rebootpoedevice.py`