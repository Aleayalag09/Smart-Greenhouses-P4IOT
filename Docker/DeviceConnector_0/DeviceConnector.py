import json
import time
import requests
import cherrypy
import paho.mqtt.client as mqtt

from Devices import *

database = "db/device_connector_db.json"
resCatEndpoints = "http://resource_catalog:8080"
new_strat = False

window_ID = 0
humidifier_ID = 1
ac_ID = 2
pump_ID = 3
dht11_ID = 0

class RegTopic(object):
    exposed = True
 
    def POST(self, *path, **queries):
        """
        Logs a new strategy and subscribes to its MQTT topic. 
        """

        global database
        global new_strat
        input = json.loads(cherrypy.request.body.read())

        with open(database, "r") as file:
            db = json.load(file)

        # db_file = open(database, "r")
        # db = json.load(db_file)
        # db_file.close()

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
                newStrategy_topic = "IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/irrigation/"+str(strategyID)
                # Subscribe to the MQTT topics
                mqtt_handler.subscribe(newStrategy_topic)
                
                db["strategies"][strategyType].append(newStrategy_topic)

        elif strategyType == "environment":
            newStrategy_topic_temp = "IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/environment/temperature"
            newStrategy_topic_hum = "IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/environment/humidity"
            # Subscribe to the MQTT topics
            mqtt_handler.subscribe(newStrategy_topic_temp)
            mqtt_handler.subscribe(newStrategy_topic_hum)
            
            db["strategies"][strategyType].append(newStrategy_topic_temp)
            db["strategies"][strategyType].append(newStrategy_topic_hum)
        else:
            newStrategy_topic = "IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/"+strategyType
            # Subscribe to the MQTT topics
            mqtt_handler.subscribe(newStrategy_topic)
            
            db["strategies"][strategyType].append(newStrategy_topic)

        new_strat = True

        with open(database, "w") as file:
            json.dump(db, file, indent=3)

        # db_file = open(database, "w")
        # json.dump(db, db_file, indent=3)
        # db_file.close()
        
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

        with open(database, "r") as file:
            db = json.load(file)

        # db_file = open(database, "r")
        # db = json.load(db_file)
        # db_file.close()

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
                    if int(split_topic[4]) == int(strategyID):
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

        with open(database, "w") as file:
            json.dump(db, file, indent=3)

        # db_file = open(database, "w")
        # json.dump(db, db_file, indent=3)
        # db_file.close()
        
        result = {
            "strategyType": strategyType,
            "timestamp": time.time()
        }
        return result



class MQTT_subscriber_publisher(object):

    def __init__(self, broker, port):
        global database
        global window_ID
        global humidifier_ID
        global ac_ID
        global pump_ID
        global dht11_ID
        
        with open(database, "r") as file:
            db = json.load(file)

        # db_file = open(database, "r")
        # db = json.load(db_file)
        # db_file.close()
        
        self.client = mqtt.Client("DeviceConnector_"+str(db["userID"])+"_"+str(db["greenHouseID"]))
        self.broker = broker
        self.port = port
        self.topic = None

        # bn: measure type, e: events (objects), v: value(s), t: timestamp
        self.__message={'bn': None, 'e': {'t': None, 'v': None}}
        
        self.sensors = []
        for real_device in db["real_devices"]:
            if real_device == "DHT11":
                self.sensors.append(DHT11(dht11_ID))

        # If we want to add other sensors or actuators we just have to add the relative if condition

        self.actuators = []
        for real_device in db["real_devices"]:
            if real_device == "Window":
                self.actuators.append(Window(window_ID))
            elif real_device == "Humidifier":
                self.actuators.append(Humidifier(humidifier_ID))
            elif real_device == "AC":
                self.actuators.append(AC(ac_ID))
            elif real_device == "Pump":
                self.actuators.append(Pump(pump_ID))

        self.controller = Controller(self.sensors, self.actuators)
        self.enviroment = Environment(self.actuators, "Torino")

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

        global database
        global window_ID
        global humidifier_ID
        global ac_ID
        global pump_ID
        global dht11_ID

        with open(database, "r") as file:
            db = json.load(file)

        # db_file = open(database, "r")
        # db = json.load(db_file)
        # db_file.close()

        measure = json.loads(message.payload)

        try:
            value = measure['e']['v']
            timestamp = measure['e']['t']
            actuatorType = measure['bn']
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')
        
        # THE FUNCTION setActuator OF DEVICES TAKES THE ACTUATOR TYPE, THE VALUE TO BE SET
        # AND OUTPUTS THE RESULT OF THE OPERATION (the value that was set, C° for temp, ON/OFF for weather, ...)
        
        print(measure, self.topic)
        
        if actuatorType == "weather":
            if value == "open":
                result = self.controller.turn_on_actuator(window_ID)

                # If we open the window we must switch OFF Humidifier and AC
                for actuator in self.actuators:
                    if isinstance(actuator, AC):
                        result = result+" - "+self.controller.turn_off_actuator(ac_ID)
                    elif isinstance(actuator, Humidifier):
                        result = result+" - "+self.controller.turn_off_actuator(humidifier_ID)
                
                mqtt_handler.publish("IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/sensors/"+actuatorType, 1, actuatorType)

            elif value == "close":
                result = self.controller.turn_off_actuator(window_ID) 
                
                # If we close the window we must switch ON Humidifier and AC      
                for actuator in self.actuators:
                    if isinstance(actuator, AC):
                        result = result+" - "+self.controller.turn_on_actuator(ac_ID)
                    elif isinstance(actuator, Humidifier):
                        result = result+" - "+self.controller.turn_on_actuator(humidifier_ID)
                        
                mqtt_handler.publish("IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/sensors/"+actuatorType, 0, actuatorType)
            else:
                print("Invalid Value")
                
        elif actuatorType == "humidity":
            if isinstance(value, (float, int)):
                result = self.controller.set_value(humidifier_ID, value)     
            else:
                print("Invalid Value")
                
        elif actuatorType == "temperature":
            if isinstance(value, (float, int)):
                result = self.controller.set_value(ac_ID, value)     
            else:
                print("Invalid Value")
                
        elif actuatorType == "irrigation":
            if isinstance(value, (float, int)):
                result = self.controller.set_value(pump_ID, value)  
                
                mqtt_handler.publish("IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/sensors/"+actuatorType, value, actuatorType)  
            else:
                print("Invalid Value")

        # If the command was successfull it should be seen from the UTILITY TOPIC of the actuator
        # THE UTILITY TOPIC SHOULD BE ACCESSED TO SEE IF THE STRATEGIES' COMMAND WERE SUCCESSFULL
        mqtt_handler.publish("IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/utility/"+actuatorType, value, "utility")

    def publish(self, topic, value, measureType):
        self.client.loop_stop()
        self.__message["bn"] = measureType
        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        self.client.publish(topic, json.dumps(self.__message))

        self.client.loop_start()
    
    def publishSensorMeasure(self, measureType):
        """
        Publish the measure of the sensor passed in the input
        """
        
        global database

        with open(database, "r") as file:
            db = json.load(file)

        # db_file = open(database, "r")
        # db = json.load(db_file)
        # db_file.close()

        topic = "IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/sensors/"+measureType
        
        find = False
        for sensor in self.controller.sensors:
            
            if find == False:
                for key, value in sensor.value.items():
                    if key == measureType:
                        find = True
                        break

        if find == True:       
            sensor.read_measurements(self.enviroment)
            self.publish(topic, sensor.value[measureType], measureType)



def refresh():
    """
    Registers the Weather Manager to the
    Resource Catalog making a post.
    """

    global database
    
    with open(database, "r") as file:
        db = json.load(file)

    # db_file = open(database, "r")
    # db = json.load(db_file)
    # db_file.close()

    payload = {
        "userID": db["userID"],
        "greenHouseID": db["greenHouseID"], 
        'ip': db["ip"], 
        'port': db["port"],
        "sensors": db["devices"]["sensors"],
        "actuators": db["devices"]["actuators"],
        'functions': [db["function"]],
        'window_factor': db["window_factor"],
        'humidifier_factor': db["humidifier_factor"],
        'ac_factor': db["ac_factor"]
    }
    
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
    
    with open(database, "r") as file:
        db = json.load(file)

    # db_file = open(database, "r")
    # db = json.load(db_file)
    # db_file.close()

    db["broker"]["ip"] = ip
    db["broker"]["port"] = port
    db["broker"]["timestamp"] = time.time()

    with open(database, "w") as file:
        json.dump(db, file, indent=3)
        
    # db_file = open(database, "w")
    # json.dump(db, db_file, indent=3)
    # db_file.close()


def getTopics():
    """
    Retrieves all the topics for the specific
    user ID and greenhouse ID in the Resource Catalog.

    Called at the BOOT.
    """

    global database
    global new_strat

    with open(database, "r") as file:
        db = json.load(file)

    # db_file = open(database, "r")
    # db = json.load(db_file)
    # db_file.close()

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
            topic = "IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/irrigation/"+str(strat["id"])
            db["strategies"]["irrigation"].append(topic)
            mqtt_handler.subscribe(topic)

    if env_strat["strat"] != []:
        topic_temp = "IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/environment/temperature"
        topic_hum = "IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/environment/humidity"
        db["strategies"]["environment"].append(topic_temp)
        db["strategies"]["environment"].append(topic_hum)
        mqtt_handler.subscribe(topic_temp)
        mqtt_handler.subscribe(topic_hum)

    if wea_strat["strat"] != []:
        topic = "IoT_project_29_test/"+str(db["userID"])+"/"+str(db["greenHouseID"])+"/weather"
        db["strategies"]["weather"].append(topic)
        mqtt_handler.subscribe(topic)
    
    new_strat = True

    with open(database, "w") as file:
        json.dump(db, file, indent=3)

    # db_file = open(database, "w")
    # json.dump(db, db_file, indent=3)
    # db_file.close()


    
                        
if __name__ == '__main__':
    
    time.sleep(15)

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(RegTopic(), '/regTopic', conf)

    cherrypy.config.update({'server.socket_host': '0.0.0.0'})

    cherrypy.engine.start()
    # cherrypy.engine.block()

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    getBroker()
    
    with open(database, "r") as file:
        db = json.load(file)

    # db_file = open(database, "r")
    # db = json.load(db_file)
    # db_file.close()

    broker_dict = db["broker"]
    
    mqtt_handler = MQTT_subscriber_publisher(broker_dict["ip"], broker_dict["port"])
    mqtt_handler.start()

    last_refresh = time.time() 
    last_measure = time.time() 
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    time.sleep(0.5)
    refresh()

    # BOOT FUNCTION TO RETRIEVE STARTING STRATEGIES
    time.sleep(0.5)
    getTopics()

    refresh_freq = 60
    measure_freq = 20

    sensors = db["devices"]["sensors"]

    while True:
        timestamp = time.time()

        if timestamp-last_refresh >= refresh_freq:

            last_refresh = time.time()
            refresh()
            print(mqtt_handler.topic)

        if timestamp-last_measure >= measure_freq:

            last_measure = time.time()
            for measureType in sensors:

                mqtt_handler.publishSensorMeasure(measureType)
                time.sleep(1.5)
            



        
        