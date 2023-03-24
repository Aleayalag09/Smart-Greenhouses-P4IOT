import json
import paho.mqtt.client as mqtt
import time
def on_message(self,client, userdata, message):
        # Callback for MQTT suscribers.
        # print msd received by mqtt subscription  
        print("received message: ",str(message.payload.decode("utf-8")))
  
client= mqtt.client("Raspberry")
client.connect("test.mosquitto.org")
client.loop_start()
client.subscribe("Smart_GreenHouses_P4IOT/0/1/0")
client.on_message= on_message
time.sleep(30)
client.loop_stop()