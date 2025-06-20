import serial
import board
import adafruit_dht
import pandas as pd
from datetime import datetime

COLLECT_SAMPLES = 50000
COLLECT_INTERVAL = 5

SDS011_PORT = "/dev/ttyS0"
DHT11_PIN = board.D4

sds011_device = serial.Serial(SDS011_PORT, baudrate = 9600, timeout = 2)
dht_device = adafruit_dht.DHT11(DHT11_PIN)

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

def collect_training_data() : 
    csv_file = "/home/toast/IoTCore/training_dataset.csv"
    data_columns = ["timestamp", "pm25", "temperature", "humidity"]
    df = pd.DataFrame(columns=data_columns)
    last_pm25 = 35.0
    last_temperature = 25.0
    last_humidity = 40.0
    count = 0
    while count < COLLECT_SAMPLES : 
        pm25 = read_sds011(last_pm25)
        temperature, humidity = read_dht11(last_temperature, last_humidity)
        timestamp = datetime.now().isoformat()
        data = {
            "pm25": round(pm25, 2),
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2)
        }
        new_row = pd.DataFrame([{
            "timestamp": timestamp,
            "pm25": data["pm25"],
            "temperature": data["temperature"],
            "humidity": data["humidity"]
        }])
        df = pd.concat([df, new_row], ignore_index = True)
        count += 1
    df.to_csv(csv_file, index = False)

if __name__ == "__main__" : 
    try : 
        collect_training_data()
        print("Training dataset collected and saved to training_dataset.csv")
    finally : 
        sds011_device.close()
        dht_device.exit()