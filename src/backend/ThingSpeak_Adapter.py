import paho.mqtt.client as mqtt
import time
import json
import random
import requests



class MQTTSubscriber:
    
    def __init__(self, clientID, broker, topic, port):
        self.clientID = clientID
        self.broker_url = broker
        self.topic = topic
        self.client = mqtt.Client()
        self.port = port
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.payload = None
        self.arrived = False

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result code " + str(rc))
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        self.arrived = True
        self.payload = msg.payload.decode()
        print("Received message on topic " + msg.topic + ": " + self.payload)

    def start(self):
        self.client.connect(self.broker_url, self.port, 60)
        self.client.loop_start()
             
    def stop(self):
        self.client.loop_stop()
        self.client.unsubscribe(self.topic)
        self.client.disconnect()
        
    def getValue(self):
        
        if self.arrived == True:     
            return self.payload

        else: 
            return None
           
    def setFlag(self):
        
        self.arrived = False
        
        

if __name__ == "__main__":
    
    # Retrive the settings information from a json --> TODO change from where we take these informations
    conf = json.load(open("settings.json"))

    broker = conf["broker"] #test.mosquitto.org

    port = conf["port"] #1883

    base_topic = conf["baseTopic"] #IoT_project

    
    
    MQTTSubscriber = MQTTSubscriber('Iot_greenhouse', broker, base_topic+"/group29/greenhouse1/temperature", port)
    
    
    MQTTSubscriber.start()
    
    while True:
        
        try:
            # If a new value is arrived from mqtt publ we send it to thingspeak
            
            #TODO --> send the data into the corresponding "thingSpeak channel"
            
            
            if MQTTSubscriber.getValue() != None:
                
                print("Il valore è: ", MQTTSubscriber.getValue())
                
                
                RequestToThingspeak = "https://api.thingspeak.com/update?api_key=YOUR_API_KEY #there there will be the uri of temperture graph 
        
                request = requests.get(RequestToThingspeak)  
                
                MQTTSubscriber.setFlag()
                
        
        
        except Exception as e:
            
            print(f"Exception: {e}")

        time.sleep(15)
    
    MQTTSubscriber.stop()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
