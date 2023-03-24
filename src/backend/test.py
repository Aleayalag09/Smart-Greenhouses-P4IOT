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
from doctest import OutputChecker
from gettext import Catalog
import json
import paho.mqtt.client as mqtt
import time

from backend.Raspberry import ReadSensor


class EnviromentManager():
    def __init__(self):
        self.broker = None
        self.clientID = "Smart_Greenhouses_P4IOT_Enviroment_Manager"
        self.catalog = None
        # Client instance
        self.client = mqtt.Client(self.clientID,True)

    
    def on_message(self,client, userdata, message):
        # Callback for MQTT suscribers.
        # print msd received by mqtt subscription  
        print("received message: ",str(message.payload.decode("utf-8")))
  
    def getCatalog(self):
        #".src/backend/settings.json"
        # pendient make rest
        conf = json.load(open("settings.json"))
        self.broker = conf['broker']
        self.catalog = json.load(open(".src/backend/catalog.json"))
        print("WORKING: "+self.broker)

    def checkWindow(self):
        # MQTT Suscriber, read sensors from Device_Connector(Raspberry)
        # msm={"Window" : 1}
        self.client.connect(self.broker)
        self.client.loop_start()
        self.client.subscribe("Smart_GreenHouses_P4IOT/0/1/0")
        print("HASTA AQUÍ VA TODO BIEN")
        self.client.on_message= self.on_message
        time.sleep(30)
        self.client.loop_stop()

    def readSensors(self):
        # MQTT Suscriber, read sensors from Device_Connector(Raspberry)
        # msm={"Temperature":20.2,"Humidity":13.4}
        self.client.connect(self.broker)
        self.client.loop_start()
        self.client.subscribe("Smart_GreenHouses_P4IOT/0/1/0")
        self.client.on_message= self.on_message
        time.sleep(30)
        self.client.loop_stop()
    
    
    def sentToActuators(self,output):
        # MQTT Spublisher, sent actuators params to Device_Connector(Raspberry)
        # msm={"Fan":1,"Humidifier":1}

        #pendiente verificar con suscriber.
        
        self.client.connect(self.broker)
        '''
        fan=[1,1,1,0,0,0,0,0,0,1,0,0,1,1,1,1,1,1,1,0,0,0]
        hum=[0,1,1,0,1,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0]
        msg={"Fan":1,"Humidifier":1}
        '''
        msg={"Fan":output[0],"Humidifier":output[1],"Light":output[2]}
        while True:
            for var in fan:
                msg={"Fan":fan[var],"Humidifier":hum[var]}
                self.client.publish("Smart_GreenHouses_P4IOT/0/1/0",json.dumps(msg),2)
                print("Just published" + str(msg))
                time.sleep(2)

    def defineOutputs(self):
        #output=[flan,humidifier,light]
        temp_max= self.temp+5
        temp_min= self.temp-5
        hum_max=self.hum+0.1
        hum_min=self.hum-0.1
        
        if self.temp>temp_max and hum_min>self.hum>hum_max:
            output=[1,0,0]
            
        elif self.temp>temp_max and self.hum>hum_max:
            output=[1,-1,0]
        
        elif self.temp<temp_min and hum_min>self.hum>hum_max:
            output=[0,0,1]

        elif self.temp<temp_min and self.hum<hum_min:
            output=[0,1,1]
        
        elif self.temp<temp_min and self.hum>hum_max:
            output=[0,-1,1]
        
        elif self.temp>temp_max and self.hum<hum_min:
            output=[1,1,0]
        
        else:
            print('Error - any condition was met')
        
        return output
				
			

    def updateEnvMgr(self):
        for user in self.catalog:
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
                        self.readSensors()
                        output= self.defineOutputs()
                        self.sentToActuators(output)
    

if __name__ == "__main__":
    envmr=EnviromentManager()
    envmr.updateEnvMgr()
    # it is necessary to define main loop and verify to close subscriptions and publish process.
   
  