import asyncio
import paho.mqtt.client as mqtt
from pysnmp.hlapi.v3arch.asyncio import *
from datetime import datetime
import json
from ping3 import ping

snmpEngine = SnmpEngine()

MQTT_BROKER = "66.179.240.113"
MQTT_PORT = 1883
MQTT_TOPIC = "/home/snmp"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_BROKER, MQTT_PORT)

servers = [
    {"device_id": "server1", "ip": "192.168.0.61"},
    {"device_id": "server2", "ip": "192.168.0.47"},
    {"device_id": "server3", "ip": "192.168.0.18"},
    {"device_id": "server4", "ip": "192.168.0.19"},
    {"device_id": "server5", "ip": "192.168.0.20"}

]

async def fetch_snmp_data(device_id, ip):

    ping_response = ping(ip, timeout=1,  unit='ms')
    if ping_response is None:
        print(f"🚫 {device_id} ({ip}) is offline!")
        payload = {
            "device_id": device_id,
            "ip_address": ip,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        client.publish(MQTT_TOPIC, json.dumps(payload))
        return

    latency_ms = round(ping_response, 2)

    iterator = get_cmd(
        snmpEngine,
        CommunityData('public', mpModel=1),
        await UdpTransportTarget.create((ip, 161)),
        ContextData(),

        ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0)),
        ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysUpTime', 0)),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.10.1.3.1")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.10.1.3.2")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.10.1.3.3")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.11.10.0")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.11.11.0")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.11.9.0")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.4.3.0")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.4.4.0")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.4.5.0")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.4.27.0")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.9.1.6.1")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.9.1.7.1")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.9.1.8.1")),
        ObjectType(ObjectIdentity("1.3.6.1.4.1.2021.9.1.9.1"))
    )

    errorIndication, errorStatus, errorIndex, varBinds = await iterator

    if errorIndication or errorStatus:
        print(f"⚠️ SNMP Error for {device_id}: {errorIndication or errorStatus.prettyPrint()}")
        return

    data = {oid.prettyPrint(): val.prettyPrint() for oid, val in varBinds}

    payload = {
        "device_id": device_id,
        "ip_address": ip,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "Online",
        "system": {
            "description": data.get('SNMPv2-MIB::sysDescr.0'),
            "uptime_seconds": int(data.get('SNMPv2-MIB::sysUpTime.0', 0)) / 100
        },
        "cpu": {
            "load_1min": float(data.get('SNMPv2-SMI::enterprises.2021.10.1.3.1', 0)),
            "load_5min": float(data.get('SNMPv2-SMI::enterprises.2021.10.1.3.2', 0)),
            "load_15min": float(data.get('SNMPv2-SMI::enterprises.2021.10.1.3.3', 0)),
            "user_cpu_percent": int(data.get('SNMPv2-SMI::enterprises.2021.11.9.0', 0)),
            "system_cpu_percent": int(data.get('SNMPv2-SMI::enterprises.2021.11.10.0', 0)),
            "idle_cpu_percent": int(data.get('SNMPv2-SMI::enterprises.2021.11.11.0', 0)),
        },
        "memory": {
            "total_ram_kb": int(data.get('SNMPv2-SMI::enterprises.2021.4.5.0', 0)),
            "free_ram_kb": int(data.get('SNMPv2-SMI::enterprises.2021.4.27.0', 0)),
            "total_swap_kb": int(data.get('SNMPv2-SMI::enterprises.2021.4.3.0', 0)),
            "available_swap_kb": int(data.get('SNMPv2-SMI::enterprises.2021.4.4.0', 0)),
        },
        "storage": {
            "total_disk_kb": int(data.get('SNMPv2-SMI::enterprises.2021.9.1.6.1', 0)),
            "available_disk_kb": int(data.get('SNMPv2-SMI::enterprises.2021.9.1.7.1', 0)),
            "used_disk_kb": int(data.get('SNMPv2-SMI::enterprises.2021.9.1.8.1', 0)),
            "disk_usage_percent": int(data.get('SNMPv2-SMI::enterprises.2021.9.1.9.1', 0)),
        },
        "network": {
             "latency_ms": float(latency_ms)
        }
    }

    print(json.dumps(payload, indent=2))
    client.publish(MQTT_TOPIC, json.dumps(payload))
    print(f"✅ Published data from {device_id}")

async def publish_snmp_data():
    tasks = [fetch_snmp_data(server['device_id'], server['ip']) for server in servers]
    await asyncio.gather(*tasks)

asyncio.run(publish_snmp_data())
