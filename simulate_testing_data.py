import serial
import board
import adafruit_dht
import paho.mqtt.client as mqtt
import json
import time

COLLECT_INTERVAL = 5

SDS011_PORT = "/dev/ttyS0"
DHT11_PIN = board.D4

sds011_device = serial.Serial(SDS011_PORT, baudrate = 9600, timeout = 2)
dht_device = adafruit_dht.DHT11(DHT11_PIN)

MQTT_BROKER = "140.116.245.212"
MQTT_PORT = 1884
MQTT_TOPIC_DATA = "air_quality/pm25"
MQTT_TOPIC_CONTROL = "air_quality/control"

GLOBAL_PM25_MAX_INCREASE = 40

RAISING = False

def read_sds011(last_pm25) : 
    try:
        sds011_device.flushInput()
        data = []
        for _ in range(10) : 
            byte = sds011_device.read()
            if byte == b"\xAA" : 
                frame = sds011_device.read(9)
                if frame[-1] == b"\xAB"[0] : 
                    data = [byte] + list(frame)
                    break
        if len(data) == 10 : 
            pm25 = (data[2] * 256 + data[1]) / 10.0
        return pm25
    except : 
        return last_pm25

def read_dht11(last_temperature, last_humidity) : 
    try : 
        temperature = dht_device.temperature
        humidity = dht_device.humidity
        if temperature is None : 
            temperature = last_temperature
        if humidity is None : 
            humidity = last_humidity
    except : 
        temperature = last_temperature
        humidity = last_humidity
    return temperature, temperature

def on_connect(client, userdata, flags, rc) : 
    print(f"Connected to MQTT broker")
    client.subscribe(MQTT_TOPIC_CONTROL, qos = 2)

def on_message(client, userdata, msg) : 
    global RAISING
    payload = msg.payload.decode()
    if payload == "1" : 
        RAISING = True
        print("Simulating PM2.5 raise")
    else : 
        RAISING = False
        print("Stop Simulating PM2.5 raise")

if __name__ == "__main__" : 
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    pm25_increase = 0
    last_pm25 = 35.0
    last_temperature = 25.0
    last_humidity = 40.0
    try : 
        while True : 
            if RAISING and pm25_increase < GLOBAL_PM25_MAX_INCREASE : 
                pm25_increase += 1
            elif not RAISING and pm25_increase > 0 : 
                pm25_increase -= 1
            pm25 = read_sds011(last_pm25)
            temperature, humidity = read_dht11(last_temperature, last_humidity)
            data = {
                "pm25": round(pm25 + pm25_increase, 2),
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2)
            }
            message = json.dumps(data).encode("utf-8")
            client.publish(MQTT_TOPIC_DATA, message, qos = 2)
            print(f"Published: {data}")
            time.sleep(COLLECT_INTERVAL)
    except : 
        client.loop_stop()
        client.disconnect()
        print("Disconnected to MQTT broker")
