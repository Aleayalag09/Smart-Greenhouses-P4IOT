import cherrypy
import requests
import time
import json

from MyMQTT import *

database = "db/thingspeak_adaptor_db.json"
resCatEndpoints = "http://resource_catalog:8080"
clientID = "adaptor"
url_thingspeak = "https://api.thingspeak.com/update?api_key=YOUR_API_KEY

class regTopic(object):
    exposed = True
 
    def POST(self, *path, **queries):
        """
        Logs a new topic
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

            topic = str(userID)+"/"+str(greenHouseID)+"/sensors/"+sensorType
            new_topic = {
                "topic": topic
            }
            database_dict["topics"].append(new_topic)        

            MeasuresReceiver.subscribe(topic)

        json.dump(database_dict, open(database, "w"), indent=3)
        
        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "sensors": sensors,
            "timestamp": time.time()
        }
        return result

    def DELETE(self, *path, **queries):
        """
        Deletes a topic 
        """

        global database
        input = json.loads(cherrypy.request.body.read())
        database_dict = json.load(open(database, "r"))

        try:
            userID = input["userID"]
            greenHouseID = input["greenHouseID"]
            sensors = input["sensors"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        
        idxs = []
        for idx, topicdb in enumerate(database_dict["topics"]):
            for sensorType in sensors:

                topic = str(userID)+"/"+str(greenHouseID)+"/sensors/"+sensorType
                if topic == topicdb["topic"]:
                    idxs.append(idx)
                    MeasuresReceiver.unsubscribe(topic)

        for idx in idxs:
            database_dict.pop(idx)

        json.dump(database_dict, open(database, "w"), indent=3)
        
        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "sensors": sensors,
            "timestamp": time.time()
        }
        return result


class MQTT_subscriber:

    def __init__(self, clientID, broker, port):
        self.client = MyMQTT(clientID, broker, port, self)

    def start (self):
        self.client.start()

    def subscribe(self, topic):
        self.client.mySubscribe(topic)

    def unsubscribe(self, topic):
        self.client.unsubscribe(topic)

    def stop (self):
        self.client.stop()

    def notify(self, topic, payload):
        measure = json.loads(payload)
        topic = topic.split("/")

        try:
            # Unit of measure of the measure
            # unit = measure['unit']
            value = measure["e"]['v']
            timestamp = measure["e"]['t']
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        send_to_Thingspeak(topic, value)


def refresh():
    """
    Registers the ThingSpeak Adaptor to the
    Resource Catalog making a post 
    """

    global database
    db_file = open(database, "r")
    db = json.load(db_file)
    db_file.close()

    payload = {
        'ip': db["ip"], 
        'port': db["port"],
        'functions': [db["function"]]}
    
    url = resCatEndpoints+'/thingspeak_adaptor'
    
    requests.post(url, json.dumps(payload))


def getBroker():
    """
    Retrieves from the Resource Catalog the endpoints
    (ip, port, timestamp) of the broker used in the system 
    """

    global database

    url = resCatEndpoints+'/broker'
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


def getTopics():
    """
    Retrieves all the topics present in the Resource Catalog
    Called at the BOOT
    """

    global database

    url = resCatEndpoints+'/device_connectors/adaptor'
    dev_conn = requests.get(url).json()

    topics_list = []
    new_topic = {
        "topic": "" 
    }
    for dev in dev_conn:
        try:
            userID = dev['userID']
            greenHouseID = dev["greenHouseID"]
            sensors = dev["sensors"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')
        else:
            for sensorType in sensors:
                topic = str(userID)+"/"+str(greenHouseID)+"/sensors/"+sensorType
                new_topic = {
                    "topic": topic
                }
                topics_list.append((new_topic))
                MeasuresReceiver.subscribe(topic)

    database_dict = json.load(open(database, "r"))
    database_dict["topics"] = topics_list
    json.dump(database_dict, open(database, "w"), indent=3)


def send_to_Thingspeak(topic, measure):
    """
    Sends the information received from 
    a MQTT topic to Thingspeak using REST (post)
    """

    global database

    db_file = open(database, "r")
    db = json.load(db_file)
    db_file.close()
    userID = topic.split("/")[0]
    greenHouseID = topic.split("/")[1]
    measureType = topic.split("/")[3]

    for user in db["users"]:
        if user["userID"] == userID:
            for greenhouse in user["greenHouses"]:
                if greenhouse["greenHouseID"] == greenHouseID:

                    thingspeak_key = user["KEY"]
                    field = greenhouse[measureType]

                    RequestToThingspeak = str(url_thingspeak+thingspeak_key+field).format(float(measure))
                    requests.post(RequestToThingspeak)  

        
        

if __name__ == "__main__":
    
    time.sleep(15)
    
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(regTopic(), '/addTopic', conf)

    cherrypy.config.update({'server.socket_host': '0.0.0.0'})

    cherrypy.engine.start()
    # cherrypy.engine.block()

    last_refresh = time.time() 
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    refresh()

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    getBroker()

    # BOOT FUNCTION TO RETRIEVE STARTING TOPICS
    getTopics()

    refresh_freq = 60
    
    broker_dict = json.load(open(database, "r"))["broker"]
    
    MeasuresReceiver = MQTT_subscriber(clientID, broker_dict["ip"], broker_dict["port"]) 
    MeasuresReceiver.start()
    
    while True:
        
        time.sleep(5)
    
    MQTTSubscriber.stop()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
