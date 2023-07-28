import cherrypy
import requests
import time
import json
import paho.mqtt.client as mqtt

database = "db/thingspeak_adaptor_db.json"
resCatEndpoints = "http://resource_catalog:8080"
url_thingspeak = "https://api.thingspeak.com/update?api_key=YOUR_API_KEY

class regTopic(object):
    exposed = True
 
    def POST(self, *path, **queries):
        """
        Logs a new topic
        """
        
        global database
        input = json.loads(cherrypy.request.body.read())

        db_file = open(database, "r")
        db = json.load(db_file)
        db_file.close()

        try:
            # Da vedere che dati vengono inviati dal catalog e come => ogni volta che viene aggiunto un nuovo Device Connector deve essere fatto un POST qua
            userID = input["userID"]
            greenHouseID = input["greenHouseID"]
            sensors = input["sensors"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        
        for sensorType in sensors:

            topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/sensors/"+sensorType
            new_topic = {
                "topic": topic
            }
            db["topics"].append(new_topic)        

            MeasuresReceiver.subscribe(topic)

        db_file = open(database, "w")
        json.dump(db, db_file, indent=3)
        db_file.close()
        
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
        # input = json.loads(cherrypy.request.body.read())
        
        db_file = open(database, "r")
        db = json.load(db_file)
        db_file.close()

        try:
            userID = queries["userID"]
            greenHouseID = queries["greenHouseID"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        
        idxs = []
        for idx, topicdb in enumerate(db["topics"]):

            split_topic = topicdb["topic"].split("/")
            if int(userID) == int(split_topic[1]) and int(greenHouseID) == int(split_topic[2]):
                idxs.append(idx)
                MeasuresReceiver.unsubscribe(topicdb["topic"])

        idxs.sort(reverse=True)
        for idx in idxs:
            db["topics"].pop(idx)

        db_file = open(database, "w")
        json.dump(db, db_file, indent=3)
        db_file.close()
        
        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "timestamp": time.time()
        }
        return result


class MQTT_subscriber(object):

    def __init__(self, broker, port):
        
        db_file = open(database, "r")
        db = json.load(db_file)
        db_file.close()
        
        self.client = mqtt.Client("ThingSpeak_adaptor_"+str(db["ID"]))
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
    (ip, port, timestamp) of the broker used in the system.
    """

    global database

    url = resCatEndpoints+'/broker'
    broker = requests.get(url).json()

    try:
        ip = broker['ip']
        port = broker["port"]
    
    except:
        raise cherrypy.HTTPError(400, 'Wrong parameters')

    # Load the database
    db_file = open(database, "r")
    db = json.load(db_file)

    db["broker"]["ip"] = ip
    db["broker"]["port"] = port
    db["broker"]["timestamp"] = time.time()

    db_file.close()
    db_file = open(database, "w")
    json.dump(db, db_file, indent=3)
    db_file.close()


def getTopics():
    """
    Retrieves all the topics present in the Resource Catalog
    Called at the BOOT
    """

    global database

    url = resCatEndpoints+'/device_connectors/adaptor'
    dev_conn = requests.get(url).json()

    topics_list = []
    for dev in dev_conn:
        try:
            userID = dev['userID']
            greenHouseID = dev["greenHouseID"]
            sensors = dev["sensors"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')
        else:
            for sensorType in sensors:
                topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/sensors/"+sensorType
                topics_list.append({
                                    "topic": topic
                                })
                MeasuresReceiver.subscribe(topic)

    db_file = open(database, "r")
    db = json.load(db_file)
    db_file.close()

    db["topics"] = topics_list
    
    db_file = open(database, "w")
    json.dump(db, db_file, indent=3)
    db_file.close()


def send_to_Thingspeak(topic, measure):
    """
    Sends the information received from 
    a MQTT topic to Thingspeak using REST (post)
    """

    global database

    db_file = open(database, "r")
    db = json.load(db_file)
    db_file.close()

    userID = topic.split("/")[1]
    greenHouseID = topic.split("/")[2]
    measureType = topic.split("/")[4]

    for user in db["users"]:
        if user["userID"] == int(userID):
            for greenhouse in user["greenHouses"]:
                if greenhouse["greenHouseID"] == int(greenHouseID):

                    thingspeak_key = user["KEY"]
                    field = greenhouse[measureType]

                    RequestToThingspeak = str(url_thingspeak+thingspeak_key+field).format(float(measure))
                    requests.post(RequestToThingspeak)  

        
        

if __name__ == "__main__":
    
    time.sleep(10)
    
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

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    getBroker()

    db_file = open(database, "r")
    db = json.load(db_file)
    broker_dict = db["broker"]
    db_file.close()
    
    MeasuresReceiver = MQTT_subscriber(broker_dict["ip"], broker_dict["port"]) 
    MeasuresReceiver.start()

    last_refresh = time.time() 
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    time.sleep(0.5)
    refresh()

    # BOOT FUNCTION TO RETRIEVE STARTING TOPICS
    time.sleep(0.5)
    getTopics()

    refresh_freq = 60
    
    while True:
        timestamp = time.time()

        if timestamp-last_refresh >= refresh_freq:

            last_refresh = time.time()
            refresh()
    
    MQTTSubscriber.stop()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
