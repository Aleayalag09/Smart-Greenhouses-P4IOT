import cherrypy
import time
import json
import paho.mqtt.client as mqtt

class MQTT_subscriber(object):

    def __init__(self, broker, port):
        
        self.client = mqtt.Client("utility")
        self.broker = broker
        self.port = port
        self.topic = None

    def start (self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def subscribe(self, topic):
        self.client.subscribe(topic)
        self.client.on_message= self.on_message
        self.topic = topic

    def unsubscribe(self, topic):
        self.client.unsubscribe(topic)

    def stop (self):
        self.client.loop_stop()
        self.client.disconnect()

    def on_message(self, client, userdata, message):
        measure = json.loads(message.payload)
        topic = message.topic

        try:
            # Unit of measure of the measure
            # unit = measure['unit']
            value = measure["e"]['v']
            timestamp = measure["e"]['t']
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        print(value)

if __name__ == "__main__":
    
    MeasuresReceiver = MQTT_subscriber("test.mosquitto.org", 1883) 
    MeasuresReceiver.start()

    MeasuresReceiver.subscribe("IoT_project_29/0/0/utility/#")

    while True:
        pass
