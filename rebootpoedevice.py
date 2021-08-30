import json
import requests
import configparser
from datetime import datetime, timedelta
from pysnmp.hlapi import *
import time
import logging
import sys

config = configparser.ConfigParser()
config.read('config.ini')
rebootafter = config['main']['rebootafter']
rebootcooldown = config['main']['rebootcooldown']
discordwebhook = config['main']['discordwebhook']
ptc_check = config.getboolean('main', 'ptc')
stdout = config.getboolean('main', 'stdout')
snmp_ip = config['snmp']['ip']
snmp_password = config['snmp']['password']

logger = logging.getLogger('RebootPoEDevice')
logger.setLevel(logging.INFO)

if stdout:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
else:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%Y-%m-%d %H:%M:%S'))

logger.addHandler(handler)


with open('devices.json') as json_file:
    devices = json.load(json_file)

with open('servers.json') as json_file:
    servers = json.load(json_file)

engine = SnmpEngine()
community = CommunityData(snmp_password)
transport = UdpTransportTarget((snmp_ip, 161))
context = ContextData()

# load every device into memory with default values
devices_data = {}
for device in devices:
    devices_data[device] = {}
    devices_data[device]["reboot_count"] = 0
    devices_data[device]["last_reboot"] = datetime.fromtimestamp(0)
    devices_data[device]["webhook_id"] = ""


def check_device(madmin):
    logger.info(f"checking devices of instance {madmin}...")
    url = servers[madmin]["url"]
    user = servers[madmin]["user"]
    password = servers[madmin]["pass"]
   
    try:
        status = requests.get(url + '/get_status', auth=(user, password))
        status.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        status = {}
        logger.info(f"MADmin is not reachable! Http Error: {errh}")
        return
    except requests.exceptions.ConnectionError as errc:
        status = {}
        logger.info(f"MADmin is not reachable! Error Connecting: {errc}")
        return
    except requests.exceptions.Timeout as errt:
        status = {}
        logger.info(f"MADmin is not reachable! Timeout Error: {errt}")
        return
    except requests.exceptions.RequestException as err:
        status = {}
        logger.info(f"MADmin is not reachable! Something Else: {err}")
        return

    for device in status.json():
        if device["name"] in devices and device["lastProtoDateTime"] and device["mode"] != "Idle":
            now = int(datetime.now().timestamp())
            lastData = device["lastProtoDateTime"]
            sleepTime = device["currentSleepTime"]
            reboot = int(rebootafter) * 60
            calc = now - reboot - int(sleepTime)
            if int(lastData) > calc:
                if devices_data[device["name"]]["reboot_count"] != 0:
                    discord_message(device["name"], edit=True)
                    logger.info(f'{device["name"]} is back online!')
                    devices_data[device["name"]]["reboot_count"] = 0
            else:
                logger.info(f'{device["name"]} is not online!')
                reboot_device(device["name"])
        elif device["name"] in devices and device["mode"] != "Idle":
            logger.info(f'{device["name"]} is not online!')
            reboot_device(device["name"])           
    logger.info("done checking devices...")

def snmp_command(name, value):
    oid = str('1.3.6.1.2.1.105.1.1.1.3.1.') + str(devices[name])
    value = ObjectType(ObjectIdentity(oid), Integer32(value))
    g = setCmd(engine, community, transport, context, value, lookupMib=False)
    next(g)

def reboot_device(name):
    rebootdelta = timedelta(minutes=int(rebootcooldown))
    if devices_data[name]["last_reboot"] > (datetime.now() - rebootdelta):
        logger.info(f"{name} was rebooted in the recent past, skipping for now...")
        return
    else:
        devices_data[name]["reboot_count"] += 1
        devices_data[name]["last_reboot"] = datetime.now()
    logger.info(f"shutting down {name}...")
    #snmp_command(name, 2)
    time.sleep(1)
    logger.info(f"booting up {name}...")
    #snmp_command(name, 1)
    if discordwebhook:
        discord_message(name)

def discord_message(name, edit=False):
    now = datetime.utcnow()
    data = {
        "username": "Alert!",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/OOjs_UI_icon_alert-destructive.svg/500px-OOjs_UI_icon_alert-destructive.svg.png",
        "embeds": [
            {
            "title": "Device restarted!",
            "color": 16711680,
            "footer": {
                "text": "Powered by RebootPoEDevice"
            },
            "thumbnail": {
                "url": "https://img.icons8.com/plasticine/344/restart.png"
            }
            }
        ]
    }
    data["embeds"][0]["timestamp"] = str(now)

    if not edit:
        data["embeds"][0]["description"] = f"`{name}` did not send useful data for more than {rebootafter} minutes!\nReboot count: `{devices_data[name]['reboot_count']}`"
        try:
            result = requests.post(discordwebhook, json = data, params={"wait": True})
            result.raise_for_status()
            answer = result.json()
            devices_data[name]["webhook_id"] = answer["id"]
        except requests.exceptions.RequestException as err:
            logger.info(err)
    else:
        data["embeds"][0]["description"] = f"`{name}` did not send useful data for more than {rebootafter} minutes!\nReboot count: `{devices_data[name]['reboot_count']}`\nFixed :white_check_mark:"
        try:
            result = requests.patch(discordwebhook + "/messages/" + devices_data[name]["webhook_id"], json = data)
            result.raise_for_status()
        except requests.exceptions.RequestException as err:
            logger.info(err)
    return result.status_code
    

while True:
    if ptc_check:
        logger.info("Checking PTC Login Servers first...")
        try:
            result = requests.head('https://sso.pokemon.com/sso/login')
            result.raise_for_status()
        except requests.exceptions.RequestException as err:
            logger.info(f"PTC Servers are not reachable! Error: {err}")
            logger.info("Waiting 5 minutes and trying again")
            time.sleep(300)
            continue
        if result.status_code != 200:
            logger.info("IP is banned by PTC, waiting 5 minutes and trying again")
            time.sleep(300)
            continue
        else:
            logger.info("IP is not banned by PTC, continuing...")
    for madmin in servers:
        check_device(madmin)
    time.sleep(60)
