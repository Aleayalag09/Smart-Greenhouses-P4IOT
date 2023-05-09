import json
import time
import requests
import cherrypy
import Devices

from MQTT.MyMQTT import *

database = "src/db/device_connector_db.json"
resCatEndpoints = "http://127.0.0.1:4000"
new_strat = False

class RegStrategy(object):
    exposed = True
 
    def POST(self, *path, **queries):
        """
        Logs a new strategy and updates the state of activity of the greenhouse. 
        """

        global database
        global new_strat
        input = json.loads(cherrypy.request.body.read())
        db = json.load(open(database, "r"))

        try:
            strategyType = input['strategyType']
            # Check if the strategy type taken from the input exist in the dev conn database
            db["strategies"][strategyType]
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        
        if strategyType == "irrigation":
            try:
                strategyID = input["stratID"]
            except:
                raise cherrypy.HTTPError(400, 'Missing input')
            else:
                newStrategy_topic = str(db["userID"])+"/"+str(db["greenHouseID"])+"/irrigation/"+str(strategyID)
                mqtt_handler.subscribe(newStrategy_topic)

        elif strategyType == "environment":
            newStrategy_topic_temp = str(db["userID"])+"/"+str(db["greenHouseID"])+"/environment/temperature"
            newStrategy_topic_hum = str(db["userID"])+"/"+str(db["greenHouseID"])+"/environment/humidity"
            mqtt_handler.subscribe(newStrategy_topic_temp)
            mqtt_handler.subscribe(newStrategy_topic_hum)
        else:
            newStrategy_topic = str(db["userID"])+"/"+str(db["greenHouseID"])+"/"+strategyType
            mqtt_handler.subscribe(newStrategy_topic)

        # Subscribe to the MQTT topics

        db["strategies"][strategyType].append(newStrategy_topic)

        new_strat = True
        json.dump(db, open(database, "w"), indent=3)

    def DELETE(self, *path, **queries):
        """
        Delete a strategy.
        """

        global database
        global new_strat
        db = json.load(open(database, "r"))

        try:
            strategyType = queries['strategyType']
            db["strategies"][strategyType]
        except:
            raise cherrypy.HTTPError(400, 'Bad request')

        if strategyType == "irrigation":
            try:
                strategyID = queries["stratID"]
            except:
                db["strategies"]["irrigation"] = []
            else:
                for step, topic in enumerate(db["strategies"]["irrigation"]):
                    split_topic = topic.split("/")
                    if int(split_topic[3]) == strategyID:
                        db["strategies"]["irrigation"].pop(step)
                        mqtt_handler.unsubscribe(topic)
                        break

        elif strategyType == "environment":
            mqtt_handler.unsubscribe(db["strategies"]["environment"][0])
            mqtt_handler.unsubscribe(db["strategies"]["environment"][1])
            db["strategies"]["environment"] = []
        else:
            mqtt_handler.unsubscribe(db["strategies"][strategyType][0])
            db["strategies"][strategyType] = []

        new_strat = True
        json.dump(db, open(database, "w"), indent=3)



class MQTT_subscriber_publisher(object):
    def __init__(self, broker, port):
        # bn: measure type, e: events (objects), v: value(s), t: timestamp
        self.__message={'bn': None, 'e': {'t': None, 'v': None}}

        self.client=MyMQTT("DeviceConnector", broker, port, None)

    def start (self):
        self.client.start()

    def subscribe(self, topic):
        self.client.mySubscribe(topic)

    def unsubscribe(self, topic):
        self.client.unsubscribe(topic)

    def stop (self):
        self.client.stop()

    def notify(self, topic, payload):
        global database

        measure = json.loads(payload)
        # [0]: userID, [1]: greenHouseID, [2]: actuator type (temperature/humidity/weather/irrigation)
        topic = topic.split("/")

        try:
            value = measure['e']['v']
            timestamp = measure['e']['t']
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')
        
        # THE FUNCTION setActuator OF DEVICES TAKES THE ACTUATOR TYPE, THE VALUE TO BE SET
        # AND OUTPUTS THE RESULT OF THE OPERATION (the value that was set, C° for temp, ON/OFF for weather, ...)
        result = Devices.setActuator(topic[2], value)

        # If the command was successfull it should be seen from the UTILITY TOPIC of the actuator
        # THE UTILITY TOPIC SHOULD BE ACCESSED TO SEE IF THE STRATEGIES' COMMAND WERE SUCCESSFULL
        mqtt_handler.publish(topic[0]+"/"+topic[1]+"/"+topic[2]+"/utility", result, "utility")

    def publish(self, topic, value, measureType):
        self.__message["bn"] = measureType
        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        self.client.myPublish(topic, self.__message)



def refresh():
    """
    Registers the Weather Manager to the
    Resource Catalog making a post.
    """

    global database
    db = json.load(open(database, "r"))

    payload = {
        "userID": db["userID"],
        "greenHouseID": db["greenHouseID"], 
        'ip': db["ip"], 
        'port': db["port"],
        "sensors": db["devices"]["sensors"],
        "actuators": db["devices"]["actuators"], 
        'functions': ["regStrategy"]}
    
    url = resCatEndpoints+'/device_connectors'
    
    requests.post(url, payload)


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

    database_dict = json.load(open(database, "r"))
    database_dict["broker"]["ip"] = ip
    database_dict["broker"]["port"] = port
    database_dict["broker"]["timestamp"] = time.time()
    json.dump(database_dict, open(database, "w"), indent=3)


def getStrategies():
    """
    Retrieves all the strategies for the specific
    user ID and greenhouse ID in the Resource Catalog.
    Called at the BOOT.
    """

    global database
    db = json.load(open(database, "r"))

    url = resCatEndpoints+'/strategies'
    params = {"id": db["userID"], "greenHouseID": db["greenHouseID"], "strategyType": "all"}
    strategies = requests.get(url, params=params).json()

    try:
        irr_strat = strategies["irrigation"]
        env_strat = strategies["environment"]
        wea_strat = strategies["weather"]
    except:
        raise cherrypy.HTTPError(400, 'Wrong parameters')
    
    if irr_strat["strat"] != []:
        for strat in irr_strat["strat"]:
            topic = str(db["userID"])+"/"+str(db["greenHouseID"])+"/irrigation/"+str(strat["id"])
            db["strategies"]["irrigation"].append(topic)

    if env_strat["strat"] != []:
        for strat in env_strat["strat"]:
            topic_temp = str(db["userID"])+"/"+str(db["greenHouseID"])+"/environment/temperature"
            topic_hum = str(db["userID"])+"/"+str(db["greenHouseID"])+"/environment/humidity"
            db["strategies"]["environment"].append(topic_temp)
            db["strategies"]["environment"].append(topic_hum)

    if wea_strat["strat"] != []:
        for strat in wea_strat["strat"]:
            topic = str(db["userID"])+"/"+str(db["greenHouseID"])+"/weather"
            db["strategies"]["weather"].append(topic)

    json.dump(db, open(database, "w"), indent=3)



def publishSensorMeasure(sensor):
    """
    Publish the measure of the sensor passed in the input
    """
    
    global database
    db = json.load(open(database, "r"))
    
    timestamp = time.time()

    topic = str(db["userID"])+"/"+str(db["greenHouseID"])+"/sensors/"+sensor
    # THE FUNCTION getMeasure OF DEVICES TAKES THE MEASURE TYPE (temperature or humidity) AND THE TIMESTAMP (the function should
    # be based on some time values in order to produce realistic measures) AND OUTPUTS THE FLOAT VALUE OF THE MEASURE REQUIRED
    value = Devices.getMeasure(sensor, timestamp)

    mqtt_handler.publish(topic, value, sensor)


    
                        
if __name__ == '__main__':

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(RegStrategy(), '/regStrategy', conf)

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    # cherrypy.engine.block()

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    getBroker()

    broker_dict = json.load(open(database, "r"))["broker"]
    
    mqtt_handler = MQTT_subscriber_publisher()
    mqtt_handler.__init__(broker_dict["broker"], broker_dict["port"])
    mqtt_handler.start()

    last_refresh = time.time() 
    last_measure = time.time() 
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    refresh()

    # BOOT FUNCTION TO RETRIEVE STARTING STRATEGIES
    getStrategies()

    refresh_freq = 60
    measure_freq = 90

    sensors = json.load(open(database, "r"))["devices"]["sensors"]

    while True:
        timestamp = time.time()

        if timestamp-last_refresh >= refresh_freq:

            last_refresh = time.time()
            refresh()

        if timestamp-last_measure >= measure_freq:

            last_measure = time.time()
            for sensor in sensors:

                publishSensorMeasure(sensor)
            



        
        