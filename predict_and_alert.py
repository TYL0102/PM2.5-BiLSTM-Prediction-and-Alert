import paho.mqtt.client as mqtt
from tensorflow.keras.models import load_model
import numpy as np
import json
from collections import deque
from tensorflow.keras.losses import MeanSquaredError

MQTT_BROKER = "140.116.245.212"
MQTT_PORT = 1884
MQTT_TOPIC_DATA = "air_quality/pm25"
MQTT_TOPIC_ALERT = "air_quality/alert"

custom_objects = {"mse": MeanSquaredError()}
model = load_model("pm25_bilstm_model.h5", custom_objects = custom_objects)
scaler = np.load("scaler.npy", allow_pickle=True).item()

data_buffer = deque(maxlen = 12)

def on_connect(client, userdata, flags, rc) : 
    print(f"Connected to MQTT broker")
    client.subscribe(MQTT_TOPIC_DATA, qos = 2)

def on_message(client, userdata, msg) : 
    global data_buffer
    data = json.loads(msg.payload.decode())
    data_buffer.append([data["pm25"], data["temperature"], data["humidity"]])
    if len(data_buffer) == 12 : 
        scaled_data = scaler.transform(list(data_buffer))
        prediction = model.predict(np.array([scaled_data]), verbose = 0)
        predicted_pm25 = scaler.inverse_transform([[prediction[0][0], 0, 0]])[0][0]
        if predicted_pm25 > 50 : 
            alert = {"message": f"PM2.5 exceeds 50 µg/m³, predicted: {predicted_pm25:.2f}"}
            client.publish(MQTT_TOPIC_ALERT, json.dumps(alert), qos = 2)
            print(f"Alert published: {alert}")
        else : 
            client.publish(MQTT_TOPIC_ALERT, "", qos = 2)
            print(f"No Alert published")

if __name__ == "__main__" : 
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()