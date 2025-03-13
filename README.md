# SNMP Monitoring System

A Python-based system for monitoring servers via SNMP and publishing metrics to an MQTT broker.

## Overview

This script fetches system metrics from multiple servers using SNMP, checks their connectivity with ping, and publishes the collected data to an MQTT topic. It's designed for monitoring multiple devices in a home or small network environment.

## Features

- Monitors multiple servers simultaneously using asynchronous operations
- Collects key system metrics:
  - CPU load (1, 5, and 15 minute averages)
  - CPU utilization (user, system, idle percentages)
  - Memory usage (RAM and swap)
  - Disk storage usage
  - Network latency
  - System uptime and description
- Reports server online/offline status
- Publishes data to an MQTT broker for further processing or visualization

## Requirements

- Python 3.7+
- Required Python packages:
  - `asyncio`
  - `paho-mqtt`
  - `pysnmp`
  - `ping3`

## Installation

1. Install the required Python packages:

```bash
pip install paho-mqtt pysnmp ping3
```

2. Configure your SNMP agents on target servers to accept requests from the monitoring host.

## Configuration

Edit the script to modify these configuration variables:

- `MQTT_BROKER`: IP address of your MQTT broker (currently "66.179.240.113")
- `MQTT_PORT`: Port for your MQTT broker (currently 1883)
- `MQTT_TOPIC`: MQTT topic to publish data to (currently "/home/snmp")
- `servers`: List of servers to monitor, each with:
  - `device_id`: Friendly name for the server
  - `ip`: IP address of the server

## Usage

Run the script to collect and publish data:

```bash
python snmp_monitor.py
```

The script will:
1. Check if each server is online using ping
2. For online servers, collect system metrics via SNMP
3. Publish the data to the configured MQTT topic
4. Print status information to the console

## Code Explanation

### Imports and Setup
```python
import asyncio
import paho.mqtt.client as mqtt
from pysnmp.hlapi.v3arch.asyncio import *
from datetime import datetime
import json
from ping3 import ping
```
- `asyncio`: Enables asynchronous programming for concurrent operations
- `paho.mqtt.client`: Client library for MQTT protocol communication
- `pysnmp`: Library for SNMP protocol communication
- `datetime`: Used for timestamp generation
- `json`: For data serialization
- `ping3`: Performs ICMP ping to check if devices are online

### MQTT Configuration
```python
MQTT_BROKER = "66.179.240.113"
MQTT_PORT = 1883
MQTT_TOPIC = "/home/snmp"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_BROKER, MQTT_PORT)
```
Sets up MQTT broker connection parameters and initializes the MQTT client.

### Server Configuration
```python
servers = [
    {"device_id": "server1", "ip": "192.168.0.61"},
    {"device_id": "server2", "ip": "192.168.0.47"},
    # ...additional servers...
]
```
Defines the list of servers to monitor with their IDs and IP addresses.

### SNMP Data Collection Function
```python
async def fetch_snmp_data(device_id, ip):
    # Function content
```
This asynchronous function collects data from a single server:

1. First checks if the server is online using ping:
   ```python
   ping_response = ping(ip, timeout=1, unit='ms')
   if ping_response is None:
       # Device is offline, publish offline status
   ```

2. If online, it collects SNMP data using pysnmp:
   ```python
   iterator = get_cmd(
       snmpEngine,
       CommunityData('public', mpModel=1),
       await UdpTransportTarget.create((ip, 161)),
       ContextData(),
       # Multiple ObjectType entries for different metrics
   )
   ```

3. The SNMP OIDs being collected include:
   - `SNMPv2-MIB::sysDescr.0`: System description
   - `SNMPv2-MIB::sysUpTime.0`: System uptime
   - `1.3.6.1.4.1.2021.10.1.3.1/2/3`: 1, 5, and 15 minute load averages
   - `1.3.6.1.4.1.2021.11.9/10/11.0`: CPU usage metrics
   - `1.3.6.1.4.1.2021.4.*`: Memory usage metrics
   - `1.3.6.1.4.1.2021.9.1.*`: Disk usage metrics

4. The collected data is then formatted into a structured JSON payload:
   ```python
   payload = {
       "device_id": device_id,
       "ip_address": ip,
       "timestamp": datetime.utcnow().isoformat() + "Z",
       "status": "Online",
       # System, CPU, memory, storage, and network data
   }
   ```

5. Finally, it publishes the data to the MQTT topic:
   ```python
   client.publish(MQTT_TOPIC, json.dumps(payload))
   ```

### Main Execution Function
```python
async def publish_snmp_data():
    tasks = [fetch_snmp_data(server['device_id'], server['ip']) for server in servers]
    await asyncio.gather(*tasks)

asyncio.run(publish_snmp_data())
```
This creates asynchronous tasks to collect data from all servers simultaneously and then runs them using `asyncio.gather()`. The entire process is started with `asyncio.run()`.

### SNMP OIDs Explained

The script collects data using these specific SNMP OIDs:

- `SNMPv2-MIB::sysDescr.0`: System description text
- `SNMPv2-MIB::sysUpTime.0`: Time since the system was last restarted (in hundredths of a second)
- CPU load averages:
  - `1.3.6.1.4.1.2021.10.1.3.1`: 1-minute load average
  - `1.3.6.1.4.1.2021.10.1.3.2`: 5-minute load average
  - `1.3.6.1.4.1.2021.10.1.3.3`: 15-minute load average
- CPU usage percentages:
  - `1.3.6.1.4.1.2021.11.9.0`: Percentage of user CPU time
  - `1.3.6.1.4.1.2021.11.10.0`: Percentage of system CPU time
  - `1.3.6.1.4.1.2021.11.11.0`: Percentage of idle CPU time
- Memory metrics:
  - `1.3.6.1.4.1.2021.4.3.0`: Total swap space
  - `1.3.6.1.4.1.2021.4.4.0`: Available swap space
  - `1.3.6.1.4.1.2021.4.5.0`: Total RAM
  - `1.3.6.1.4.1.2021.4.27.0`: Free RAM
- Disk storage (for first disk, index 1):
  - `1.3.6.1.4.1.2021.9.1.6.1`: Total disk space (KB)
  - `1.3.6.1.4.1.2021.9.1.7.1`: Available disk space (KB)
  - `1.3.6.1.4.1.2021.9.1.8.1`: Used disk space (KB)
  - `1.3.6.1.4.1.2021.9.1.9.1`: Percentage of disk used

## Data Format

The script publishes JSON data with the following structure:

```json
{
  "device_id": "server1",
  "ip_address": "192.168.0.61",
  "timestamp": "2025-03-13T12:34:56.789Z",
  "status": "Online",
  "system": {
    "description": "Linux server1 5.15.0-91-generic #101-Ubuntu SMP...",
    "uptime_seconds": 1234567
  },
  "cpu": {
    "load_1min": 0.15,
    "load_5min": 0.10,
    "load_15min": 0.05,
    "user_cpu_percent": 5,
    "system_cpu_percent": 2,
    "idle_cpu_percent": 93
  },
  "memory": {
    "total_ram_kb": 8192000,
    "free_ram_kb": 4096000,
    "total_swap_kb": 2097152,
    "available_swap_kb": 2097152
  },
  "storage": {
    "total_disk_kb": 102400000,
    "available_disk_kb": 51200000,
    "used_disk_kb": 51200000,
    "disk_usage_percent": 50
  },
  "network": {
    "latency_ms": 0.59
  }
}
```