import json
import time
import requests
import cherrypy

from MyMQTT import *
from Devices import *

database = "db/device_connector_db.json"
resCatEndpoints = "http://resource_catalog:8080"
new_strat = False

window_ID = 0
humidifier_ID = 1
ac_ID = 2
pump_ID = 3
dht11_ID = 0

class RegStrategy(object):
    exposed = True
 
    def POST(self, *path, **queries):
        """
        Logs a new strategy and updates the state of activity of the greenhouse. 
        """

        global database
        global new_strat
        input = json.loads(cherrypy.request.body.read())
        db_file = open(database, "r")
        db = json.load(db_file)
        db_file.close()

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
        
        result = {
            "strategyType": strategyType,
            "timestamp": time.time()
        }
        return result

    def DELETE(self, *path, **queries):
        """
        Delete a strategy.
        """

        global database
        global new_strat
        db_file = open(database, "r")
        db = json.load(db_file)
        db_file.close()

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
        
        result = {
            "strategyType": strategyType,
            "timestamp": time.time()
        }
        return result



class MQTT_subscriber_publisher(object):
    def __init__(self, broker, port):
        # bn: measure type, e: events (objects), v: value(s), t: timestamp
        self.__message={'bn': None, 'e': {'t': None, 'v': None}}

        global database
        global window_ID
        global humidifier_ID
        global ac_ID
        global pump_ID
        global dht11_ID

        db_file = open(database, "r")
        db = json.load(db_file)
        db_file.close()

        self.client=MyMQTT("DeviceConnector_"+str(db["userID"])+"_"+str(db["greenHouseID"]), broker, port, None)
        
        sensors = []
        for real_device in db["real_devices"]:
            if real_device == "DHT11":
                sensors.append(DHT11(dht11_ID))

        # If we want to add other sensors or actuators we just have to add the relative if condition

        actuators = []
        for real_device in db["real_devices"]:
            if real_device == "Window":
                sensors.append(Window(window_ID))
            elif real_device == "Humidifier":
                sensors.append(Humidifier(humidifier_ID))
            elif real_device == "AC":
                sensors.append(AC(ac_ID))
            elif real_device == "Pump":
                sensors.append(Pump(pump_ID))

        self.controller = Controller(sensors, actuators)
        self.enviroment = Environment(actuators, "Torino")

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
        global window_ID
        global humidifier_ID
        global ac_ID
        global pump_ID
        global dht11_ID

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
        
        if topic[2] == "weather":
            if value == "on":
                result = self.controller.turn_on_actuator(window_ID)
            elif value == "off":
                result = self.controller.turn_off_actuator(window_ID)       
            else:
                print("Invalid Value")
                
        elif topic[2] == "humidity":
            if isinstance(value, (float, int)):
                result = self.controller.set_value(humidifier_ID, value)     
            else:
                print("Invalid Value")
                
        elif topic[2] == "temperature":
            if isinstance(value, (float, int)):
                result = self.controller.set_value(ac_ID, value)     
            else:
                print("Invalid Value")
                
        elif topic[2] == "irrigation":
            if isinstance(value, (float, int)):
                result = self.controller.set_value(pump_ID, value)     
            else:
                print("Invalid Value")

        # If the command was successfull it should be seen from the UTILITY TOPIC of the actuator
        # THE UTILITY TOPIC SHOULD BE ACCESSED TO SEE IF THE STRATEGIES' COMMAND WERE SUCCESSFULL
        mqtt_handler.publish(topic[0]+"/"+topic[1]+"/"+topic[2]+"/utility", result, "utility")

    def publish(self, topic, value, measureType):
        self.__message["bn"] = measureType
        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        self.client.myPublish(topic, self.__message)
    
    def publishSensorMeasure(self, measureType):
        """
        Publish the measure of the sensor passed in the input
        """
        
        global database
        db_file = open(database, "r")
        db = json.load(db_file)
        db_file.close()

        topic = str(db["userID"])+"/"+str(db["greenHouseID"])+"/sensors/"+measureType
        
        find = False
        for sensor in self.controller.sensors:
            
            if find == False:
                for key, value in sensor.value.items():
                    if key == measureType:
                        find = True
                        break

            if find == True:       
                sensor.read_measurements(self.enviroment)
                self.publish(topic, sensor.value[measureType])
                break



def refresh():
    """
    Registers the Weather Manager to the
    Resource Catalog making a post.
    """

    global database
    db_file = open(database, "r")
    db = json.load(db_file)
    db_file.close()

    payload = {
        "userID": db["userID"],
        "greenHouseID": db["greenHouseID"], 
        'ip': db["ip"], 
        'port': db["port"],
        "sensors": db["devices"]["sensors"],
        "actuators": db["devices"]["actuators"],
        'functions': [db["function"]]}
    
    url = resCatEndpoints+'/device_connectors'
    
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
    db_file = open(database, "r")
    db = json.load(db_file)
    db_file.close()

    url = resCatEndpoints+'/strategy'
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


    
                        
if __name__ == '__main__':
    
    time.sleep(30)

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(RegStrategy(), '/regStrategy', conf)

    cherrypy.config.update({'server.socket_host': '0.0.0.0'})

    cherrypy.engine.start()
    # cherrypy.engine.block()

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    getBroker()

    broker_dict = json.load(open(database, "r"))["broker"]
    
    mqtt_handler = MQTT_subscriber_publisher(broker_dict["ip"], broker_dict["port"])
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
            for measureType in sensors:

                mqtt_handler.publishSensorMeasure(measureType)
            



        
        