
import paho.mqtt.client as PahoMQTT
import time
import json

if __name__ == "__main__":
    
    broker = "test.mosquitto.org"
    port = "1883"

    client = PahoMQTT.Client("Window")
    client.connect(broker)
    window=[0,1,1,0,1,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0]
    while True:
        for flag in window:
            msg = {"Window" : flag}
            client.publish("Smart_GreenHouses_P4IOT/0/1/0", json.dumps(msg))
            print("Published" + str(msg))
            time.sleep(1)
   
    