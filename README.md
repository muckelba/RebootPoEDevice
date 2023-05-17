# RebootPoEDevice

A little script to automatically power cycle devices connected to a PoE switch.

## Installation

**IMPORTANT:** if you use multiple MADmin instances, make sure to have unique origins across them as the origin has to be unique in the devices.json!

### Config

Copy the example config file: `cp config/config.ini.example config/config.ini` and fill in the config fields:

- `rebootafter` specifies the time in minutes after a device without data should be power cycled.
- `rebootcooldown` specifies a time in minutes after a powercycled device should be ignored by the script.
- `discordwebhook` fill in a webhook url. A little discord message is sent everytime a device getting rebooted.
- `ptc` will check if the public IP adress is banned by PTC at the moment and will not try to reboot devices if set to `true`.
- `banPing` will send a ping to this Discord user ID when an IP ban is active. Roles are currently not supported, let me know if that's needed.
- `stdout` will send the output to standard out and without a timestamp if set to `true`. Set it to false if you don't know what that means.
- `ip` is the ip of your PoE switch.
- `password` is the password of your PoE switch.

### Python requirements

`pip install -r requirements.txt`

### Devices

Copy the example devices file: `cp config/devices.json.example config/devices.json` and fill in your devices and their portnumbers. The key is the origin, the value is the PoE portnumber.

### Servers

Copy the example servers file: `cp config/servers.json.example config/servers.json` and fill in your MADmin server(s). Set `user` and `pass` to `""` or `null` if you dont use any auth.

## Running

`python rebootpoedevice.py`

## Docker

It's also possible to use Docker to host this script. The image is hosted on GitHub: `ghcr.io/muckelba/rebootpoedevice:master`

### Docker Compose

Copy the example compose file: `cp docker-compose.yml.example docker-compose.yml` and make adjustments if you need to.

Start the script with `docker-compose up -d` and see its logs with `docker-compose logs -f`. 

To stop it again, run `docker-compose down`. 

To update the container, run `docker-compose pull` and restart the container.