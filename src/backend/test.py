'''
() Make a GET to the Catalog (< Web Page) to know the strategy, the topics.
Mientras se define el post,  archivo JSON.

(OK) RECEIVES (MQTT subscription) a flag from the Weather Controller that says if the window is open 
(therefore if the Environment manager has to be active or not).

While flag= 1 each 5 seg.

(OK) RECEIVES (MQTT subscription) the real-time measures about Temp, Hum,.. 
from the devices.

(OK) PUBLISH (MQTT PUBLISH), it activate actuators according to the real-time measures and the strategy.
If needed, new real-time parameters to the Devices 
(received Temp = 20 but the strategy says 22 so ⇒ 
publish actuation to Device Temp = 22 and hence the device changes the temp, 
until the next actuation)
'''
import json
import paho.mqtt.client as mqtt
import time


class EnviromentManager():
    def __init__(self,broker):
        self.broker = broker
        self.clientID = "Smart_Greenhouses_P4IOT_Enviroment_Manager"
        self.catalog = None
        # Client instance
        self.client = mqtt.Client(self.clientID,True)

    def on_message(client,userdata,message): 
        # print msd received by mqtt subscription  
        print("received message: ",str(message.payload.decode("utf-8")))
    
    def checkWindow(self):
        self.client.connect(broker)
        self.client.loop_start()
        self.client.subscribe("Smart_GreenHouses_P4IOT/0/1/0")
        self.client.on_message=on_message
        time.sleep(30)
        client.loop_stop()


if __name__ == "__main__":
    conf = json.load(open("settings.json"))
    broker = conf['broker']
    
    checkWindow(broker)
    #catalog = json.load(open(".backend/db/catalog.json"))
    #client = mqtt.Client("Env_Mgr")
    #client.connect(broker)
    #client.loop_start()
    #client.subscribe("Smart_GreenHouses_P4IOT/0/1/0")
    #client.on_message=on_message
    #time.sleep(30)
    #client.loop_stop()

    '''
    for user in catalog:
        if not user['greenHouses']:
            break
        for greenhouse in user['greenHouses']:
            if not greenhouse['devicesList']:
                break
            for device in greenhouse['devicesList']:
                if not device['strategies']:
                    break
                strategies = sorted(device['strategies'], key=lambda d:d['time'],reverse=True)
                for strategy in strategies:
                    if open_window == False:
    '''