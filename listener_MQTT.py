# TEST
import paho.mqtt.client as mqtt
import json

class MQTT_subscriber(object):

    def __init__(self, broker, port):
        
        self.client = mqtt.Client("TEST")
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

        print("Topic: "+str(topic))
        print("Message: "+str(measure))

        
if __name__ == '__main__':

    broker_dict = {"ip": "test.mosquitto.org", "port": 1883}
    
    MeasuresReceiver = MQTT_subscriber(broker_dict["ip"], broker_dict["port"]) 
    MeasuresReceiver.start()

    MeasuresReceiver.subscribe("0/0/#")

    while True:
        pass