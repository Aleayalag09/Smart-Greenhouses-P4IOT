import cherrypy
import requests
import time
import json

from MQTT.MyMQTT import *

database = "src/db/thingspeak_adaptor_db.json"
resourceCatalogIP = ""
clientID = "adaptor_v2"

class addTopic(object):
    exposed = True
 
    def POST(self, *path, **queries):
        """
        This function logs a new strategy and updates the state of activity of the greenhouse 
        """
        global database
        input = json.loads(cherrypy.request.body.read())
        database_dict = json.load(open(database, "r"))

        try:
            # Da vedere che dati vengono inviati dal catalog e come => ogni volta che viene aggiunto un nuovo Device Connector deve essere fatto un POST qua
            userID = input["userID"]
            greenHouseID = input["greenHouseID"]
            sensors = input["sensors"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        
        for sensorType in sensors:

            topic = str(userID)+"/"+str(greenHouseID)+"/"+sensorType
            new_topic = {
                "topic": topic
            }
            database_dict["topics"].append(new_topic)        

            MeasuresReceiver.subscribe(topic)

        json.dump(database_dict, open(database, "w"), indent=3)

    def DELETE(self, *path, **queries):
        """
        This function logs a new strategy and updates the state of activity of the greenhouse 
        """
        global database


class MQTTMeasuresReceiver:

    def __init__(self, clientID, broker, port):
        self.client = MyMQTT(clientID, broker, port, self)

    def start (self):
        self.client.start()

    def subscribe(self, topic):
        self.client.mySubscribe(topic)

    def stop (self):
        self.client.stop()

    def notify(self, topic, payload):
        measure = json.loads(payload)
        topic = topic.split("/")

        try:
            # Unit of measure of the measure
            unit = measure['unit']
            value = measure['value']
            timestamp = measure['timestamp']
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        send_to_Thingspeak(topic, measure)


# REGISTER CONTINOUSLY THE ADAPTOR TO THE RESOURCE CATALOG
def refresh():
    payload = {'ip': "IP of the ThingSpeak_Adaptor", 'port': "PORT of the ThingSpeak_Adaptor",
               'functions': [""]}
    url = 'URL of the RESOURCE_CATALOG/POST thingspeak_adaptor'
    
    requests.post(url, payload)


# CONTACT THE GET INTERFACE FOR THE BROKER ON THE CATALOG REST API (obtains ip, port and timestamp for future controls)
def getBroker():
    global database

    url = 'URL of the RESOURCE_CATALOG/broker'
    broker = requests.get(url).json()

    try:
        ip = broker['ip']
        port = broker["port"]
    
    except:
        raise cherrypy.HTTPError(400, 'Wrong parameters')

    database_dict = json.load(open(database, "r"))
    database_dict["broker"]["ip"] = ip
    database_dict["broker"]["port"] = port
    database_dict["broker"]["timestamp"] = time.time()
    json.dump(database_dict, open(database, "w"), indent=3)


# BOOT FUNCTION USED TO GET ALL THE TOPICS FROM THE RESOURCE CATALOG
def getTopics():
    pass


# FUNCTION NEEDED TO SEND THE INFO RECEIVED FROM MQTT TO THINGSPEAK
def send_to_Thingspeak(topic, measure):
    pass
        
        

if __name__ == "__main__":
    
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(addTopic(), '/addTopic', conf)

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()

    last_refresh = time.time() 
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    refresh()

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    getBroker()

    # BOOT FUNCTION TO RETRIEVE STARTING TOPICS
    getTopics()

    refresh_freq = 60
    
    broker_dict = json.load(open(database, "r"))["broker"]
    
    MeasuresReceiver = MQTTMeasuresReceiver(clientID, broker_dict["ip"], broker_dict["port"]) 
    MeasuresReceiver.start()
    
    while True:
        
        time.sleep(5)
    
    MQTTSubscriber.stop()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
