import time
import adafruit_dht
import board
import paho.mqtt.client as mqtt
import os

#our public server ip and port service with mqtt
broker = "66.179.240.113"
port = 1883
topic = "/sensor/data"

pipe_path = "/tmp/temperature_flag_pipe"

dht_device = adafruit_dht.DHT22(board.D4)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.enable_logger()

def connect_mqtt():
    try:
        client.connect(broker, port, 60)
        print("Connected to MQTT broker")
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
        return False
    return True

def read_sensor(retries=5):
    for _ in range(retries):
        try:
            temperature_c = dht_device.temperature
            temperature_f = temperature_c * (9 / 5) + 32
            humidity = dht_device.humidity
            return temperature_c, temperature_f, humidity
        except RuntimeError as err:
            print(err.args[0])
            time.sleep(2.0)  
    return None, None, None

def update_temperature_flag(temperature_c):
    with open(pipe_path, "w") as pipe:
        #
        if temperature_c > 27:
            pipe.write("1")
            #print("too hot!")
        else:
            pipe.write("0")
            #print("too cold!")

if not connect_mqtt():
    print("Exiting due to MQTT connection failure")
    exit(1)

if not os.path.exists(pipe_path):
    os.mkfifo(pipe_path)

while True:
    temperature_c, temperature_f, humidity = read_sensor()
    if temperature_c is not None and humidity is not None:
        print("Temp:{:.1f} C / {:.1f} F    Humidity: {}%".format(temperature_c, temperature_f, humidity))
        update_temperature_flag(temperature_c)
        payload = "{{\"temperature_c\": {:.1f}, \"temperature_f\": {:.1f}, \"humidity\": {:.1f}}}".format(temperature_c, temperature_f, humidity)
        try:
            client.publish(topic, payload)
        except Exception as e:
            print(f"Failed to publish data: {e}")
            if not connect_mqtt():
                print("Exiting due to MQTT connection failure")
                exit(1)
    else:
        print("Failed to read sensor data after retries.")

    time.sleep(3.0)
