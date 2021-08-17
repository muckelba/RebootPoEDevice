import json
import requests
import configparser
from datetime import datetime, timedelta
from pysnmp.hlapi import *
import time
import logging

logging.basicConfig(
    format='[%(asctime)s] %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

config = configparser.ConfigParser()
config.read('config.ini')

rebootafter = config['main']['rebootafter']
rebootcooldown = config['main']['rebootcooldown']
discordwebhook = config['main']['discordwebhook']
ptc_check = config.getboolean('main', 'ptc')
snmp_ip = config['snmp']['ip']
snmp_password = config['snmp']['password']

with open('devices.json') as json_file:
    devices = json.load(json_file)

with open('servers.json') as json_file:
    servers = json.load(json_file)

engine = SnmpEngine()
community = CommunityData(snmp_password)
transport = UdpTransportTarget((snmp_ip, 161))
context = ContextData()

rebooted_devices = {}

def check_device(madmin):
    logging.info(f"checking devices of instance {madmin}...")
    url = servers[madmin]["url"]
    user = servers[madmin]["user"]
    password = servers[madmin]["pass"]

    try:
        status = requests.get(url + '/get_status', auth=(user, password))
        status.raise_for_status()
    except requests.exceptions.HTTPError as e:
        status = {}
        logging.info(e.response.text)
    
    for device in status.json():
        if device["lastProtoDateTime"] and device["mode"] != "Idle":
            now = int(datetime.now().timestamp())
            lastData = device["lastProtoDateTime"]
            sleepTime = device["currentSleepTime"]
            reboot = int(rebootafter) * 60
            calc = now - reboot - int(sleepTime)
            if int(lastData) > calc:
                continue
            else:
                logging.info(f'{device["name"]} is not online!')
                reboot_device(device["name"])
        elif device["mode"] != "Idle":
            logging.info(f'{device["name"]} is not online!')
            reboot_device(device["name"])
    logging.info("done checking devices...")

def snmp_command(name, value):
    oid = str('1.3.6.1.2.1.105.1.1.1.3.1.') + str(devices[name])
    value = ObjectType(ObjectIdentity(oid), Integer32(value))
    g = setCmd(engine, community, transport, context, value, lookupMib=False)
    next(g)

def reboot_device(name):
    if name in devices:
        if name in rebooted_devices:
            if rebooted_devices[name] > int(datetime.now().timestamp()) - (int(rebootcooldown) * 60):
                logging.info(f"{name} was rebooted in the recent past, skipping for now...")
                return
            else:
                rebooted_devices[name] = int(datetime.now().timestamp())
        else:
            rebooted_devices[name] = int(datetime.now().timestamp())
        logging.info(f"shutting down {name}...")
        snmp_command(name, 2)
        time.sleep(1)
        logging.info(f"booting up {name}...")
        snmp_command(name, 1)
        if discordwebhook:
            discord_message(name)
    else:
        logging.info(f"{name} is not in devices.json, skipping...")

def discord_message(name):
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
    data["embeds"][0]["description"] = f"`{name}` did not send useful data for more than {rebootafter} minutes!"
    data["embeds"][0]["timestamp"] = str(now)
    try:
        result = requests.post(discordwebhook, json = data)
        result.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.info(e.response.text)

while True:
    if ptc_check:
        logging.info("Checking PTC Login Servers first...")
        result = requests.head('https://sso.pokemon.com/sso/login')
        if result.status_code != 200:
            logging.info("IP is banned by PTC, waiting 5 minutes and trying again")
            time.sleep(300)
            break
        else:
            logging.info("IP is not banned by PTC, continuing...")
    for madmin in servers:
        check_device(madmin)
    time.sleep(60)
