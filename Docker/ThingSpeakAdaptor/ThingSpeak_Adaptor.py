import cherrypy
import requests
import time
import json
import paho.mqtt.client as mqtt

database = "db/thingspeak_adaptor_db.json"
resCatEndpoints = "http://resource_catalog:8080"
url_thingspeak = "https://api.thingspeak.com/update?api_key=YOUR_API_KEY

measures = {"temperature": 0, "humidity": 0, "weather": -1, "irrigation": 0}


class regTopic(object):
    exposed = True
 
    def POST(self, *path, **queries):
        """
        Logs a new topic
        """
        
        global database
        input = json.loads(cherrypy.request.body.read())
        
        with open(database, "r") as file:
            db = json.load(file)

        try:
            userID = input["userID"]
            greenHouseID = input["greenHouseID"]
            sensors = input["sensors"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')

        topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/sensors/#"
        new_topic = {
            "topic": topic
        }
        db["topics"].append(new_topic)   

        MeasuresReceiver.subscribe(topic)
        
        with open(database, "w") as file:
            json.dump(db, file, indent=3)
        
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
        
        with open(database, "r") as file:
            db = json.load(file)

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

        with open(database, "w") as file:
            json.dump(db, file, indent=3)
        
        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "timestamp": time.time()
        }
        return result


class MQTT_subscriber(object):

    def __init__(self, broker, port):
        
        with open(database, "r") as file:
            db = json.load(file)
        
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
    
    with open(database, "r") as file:
        db = json.load(file)

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
    
    with open(database, "r") as file:
        db = json.load(file)

    db["broker"]["ip"] = ip
    db["broker"]["port"] = port
    db["broker"]["timestamp"] = time.time()

    with open(database, "w") as file:
        json.dump(db, file, indent=3)


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

            topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/sensors/#"
            topics_list.append({
                "topic": topic
            })
            
            MeasuresReceiver.subscribe(topic)

    with open(database, "r") as file:
        db = json.load(file)

    db["topics"] = topics_list
    
    with open(database, "w") as file:
        json.dump(db, file, indent=3)


def send_to_Thingspeak(topic, measure):
    """
    Sends the information received from 
    a MQTT topic to Thingspeak using REST (post)
    """

    global database

    with open(database, "r") as file:
        db = json.load(file)

    userID = topic.split("/")[1]
    greenHouseID = topic.split("/")[2]

    measureType = topic.split("/")[4]

    measures[measureType] = measure

    for user in db["users"]:
        if user["userID"] == int(userID):
            for greenhouse in user["greenHouses"]:
                if greenhouse["greenHouseID"] == int(greenHouseID):

                    if measures["temperature"] != 0 and measures["humidity"] != 0:
                        thingspeak_key = greenhouse["KEY"]
                        field_temp = greenhouse["temperature"]
                        field_hum = greenhouse["humidity"]

                        if measures["irrigation"] != 0 and measures["weather"] != -1:
                            field_irr = greenhouse["irrigation"]
                            field_wea = greenhouse["weather"]

                            RequestToThingspeak = str(url_thingspeak+thingspeak_key+field_temp+field_hum+field_wea+field_irr).format(float(measures["temperature"]), float(measures["humidity"]), float(measures["weather"]), float(measures["irrigation"]))
                            measures["weather"] = -1
                            measures["irrigation"] = 0

                        elif measures["weather"] != -1:
                            field_wea = greenhouse["weather"]

                            RequestToThingspeak = str(url_thingspeak+thingspeak_key+field_temp+field_hum+field_wea).format(float(measures["temperature"]), float(measures["humidity"]), float(measures["weather"]))
                            measures["weather"] = -1    

                        elif measures["irrigation"] != 0:
                            field_irr = greenhouse["irrigation"]

                            RequestToThingspeak = str(url_thingspeak+thingspeak_key+field_temp+field_hum+field_irr).format(float(measures["temperature"]), float(measures["humidity"]), float(measures["irrigation"]))
                            measures["irrigation"] = 0    
                        
                        else:
                            RequestToThingspeak = str(url_thingspeak+thingspeak_key+field_temp+field_hum).format(float(measures["temperature"]), float(measures["humidity"]))
                       
                        measures["temperature"] = 0
                        measures["humidity"] = 0
                        
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

    getBroker()

    with open(database, "r") as file:
        db = json.load(file)

    broker_dict = db["broker"]
    
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
