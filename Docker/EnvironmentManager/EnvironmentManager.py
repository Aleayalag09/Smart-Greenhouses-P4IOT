import cherrypy
import requests
import time
from datetime import datetime
import json
import paho.mqtt.client as mqtt

# Global variables
new_strat = False
new_measures = {
    "new": False,
    "temperature": False,
    "humidity": False
}
database = "db/environment_manager_db.json"
resCatEndpoints = "http://resource_catalog:8080"

# Define a CherryPy class for handling strategy registration
class RegStrategy(object):
    exposed = True
 
    def POST(self, *path, **queries):
        """
        Logs a new strategy for a specific user and greenhouse
        and updates the state of activity of the greenhouse. 
        """

        global database
        global new_strat
        input = json.loads(cherrypy.request.body.read())

        try:
            userID = input['userID']
            greenHouseID = input['greenHouseID']
            active = input['active']
            temperature = input['temperature']
            humidity = input['humidity']
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        
        
        # Generate topic strings based on user and greenhouse IDs
        topic_act_temp = str(userID)+"/"+str(greenHouseID)+"/environment/temperature"
        topic_act_hum = str(userID)+"/"+str(greenHouseID)+"/environment/humidity"

        topic_sens_temp = str(userID)+"/"+str(greenHouseID)+"/sensors/temperature"
        topic_sens_hum = str(userID)+"/"+str(greenHouseID)+"/sensors/humidity"
        
        # Load the database JSON
        with open(database, "r") as file:
            db = json.load(file)

        # Create a new strategy object
        new_strategy = {
            "userID": int(userID),
            "greenHouseID": int(greenHouseID),
            "topic_sens": {
                "topic_temp": topic_sens_temp, 
                "topic_hum": topic_sens_hum, 
            },
            "topic_act": {
                "topic_temp": topic_act_temp, 
                "topic_hum": topic_act_hum, 
            }, 
            "temperature": float(temperature), 
            "humidity": float(humidity),
            "active": active, 
            "window_factor": 0,
            "humidifier_factor": 0,
            "ac_factor": 0,
            "window_open": False,
            "last_message_temp": 0,
            "last_message_hum": 0,
            "timestamp": time.time()
        }

        # Subscribe to the MQTT topics of humidity and temperature
        mqtt_handler.subscribe(topic_sens_temp)
        mqtt_handler.subscribe(topic_sens_hum)

        # Add the new strategy to the database
        db["strategies"].append(new_strategy)

        new_strat = True
        with open(database, "w") as file:
            json.dump(db, file, indent=3)

        time.sleep(0.5)
        getFactors(userID, greenHouseID)

        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "temperature": temperature, 
            "humidity": humidity,
            "active": active, 
            "timestamp": time.time()
        }
        return result

    def PUT(self, *path, **queries):
        """
        Modify the state of activity of the strategy 
        owned by a specific user and greenhouse.
        """

        global database 
        global new_strat
        input = json.loads(cherrypy.request.body.read())
        
        with open(database, "r") as file:
            db = json.load(file)

        # Extract input parameters from the request
        try:
            userID = input['userID']
            greenHouseID = input['greenHouseID']
            active = input['active']
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        else:
            # Update the state of activity for the matching strategy
            for strat in db["strategies"]:
                if strat["userID"] == int(userID) and strat["greenHouseID"] == int(greenHouseID):
                    strat["active"] = active
        
        new_strat = True
        with open(database, "w") as file:
            json.dump(db, file, indent=3)

        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "active": active, 
            "timestamp": time.time()
        }
        return result

    def DELETE(self, *path, **queries):
        """
        Delete a strategy owned by a specific user and greenhouse.
        """

        global database
        global new_strat
        
        # Extract input parameters from the request
        try:
            userID = queries['userID']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        with open(database, "r") as file:
            db = json.load(file)

        idx = 0
        for strat in db["strategies"]:
            # Check if the strategy matches the provided userID and greenHouseID
            if strat["userID"] == int(userID) and strat["greenHouseID"] == int(greenHouseID):
                # Unsubscribe from the sensors topics before removing completely the strategy from the db
                mqtt_handler.unsubscribe(strat["topic_sens"]["topic_temp"])
                mqtt_handler.unsubscribe(strat["topic_sens"]["topic_hum"])
                break
            else:
                idx += 1
        
        # Remove the strategy from the strategies list in the database
        db["strategies"].pop(idx)

        new_strat = True

        # Write the updated database back to the file
        with open(database, "w") as file:
            json.dump(db, file, indent=3)

        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "timestamp": time.time()
        }
        return result


class MQTT_subscriber_publisher(object):
    
    def __init__(self, broker, port):
        
        with open(database, "r") as file:
            db = json.load(file)
        
        self.client = mqtt.Client("EnvironmentManager_"+str(db["ID"]))
        self.broker = broker
        self.port = port
        self.topic = None

        # bn: macro strategy name (environment), e: events (objects), v: value(s) (depends on what we want to set with the strategy), t: timestamp
        self.__message={'bn': None, 'e': {'t': None, 'v': None}}

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

    def on_message(self, client, userdata, message):
        global database
        global new_measures

        measure = json.loads(message.payload)
        topic = message.topic.split("/")

        try:
            # Unit of measure of the measure
            # unit = measure['unit']
            value = measure['e']['v']
            timestamp = measure['e']['t']
            measuretype = measure['bn']
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        # Load the database
        with open(database, "r") as file:
            db = json.load(file)

        # If the message is received from the weather manager the script must change the parameter
        # related to the window for the strategy of that user and greenhouse
        if measuretype == "weather":
            for strat in db["strategies"]:
                if strat["userID"] == int(topic[0]) and strat["greenHouseID"] == int(topic[1]):
                    if value == "open":
                        strat["window_open"] == True
                    elif value == "close":
                        strat["window_open"] == False
        else:
            # Update the corresponding actual value in the database
            if len(db["actual_"+measuretype]) != 0:
                for actualValue in db["actual_"+measuretype]:
                    if actualValue["userID"] == int(topic[0]) and actualValue["greenHouseID"] == int(topic[1]):
                        actualValue[measuretype] = float(value)
                        actualValue["timestamp"] = timestamp
                        new_measures["new"] = True
                        new_measures[measuretype] = True

            else:
                actual_value = {
                    "userID": int(topic[0]),
                    "greenHouseID": int(topic[1]),
                    measuretype: float(value),
                    "timestamp": timestamp
                }
                db["actual_"+measuretype].append(actual_value)
            
                new_measures["new"] = True
                new_measures[measuretype] = True

        # Write the updated database back to the file
        with open(database, "w") as file:
            json.dump(db, file, indent=3)

    def publish(self, topic, value, actuatorType):
        self.client.loop_stop()
        # Update the message with the current timestamp and value
        self.__message["bn"] = actuatorType
        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        # Publish the message to the specified topic
        self.client.publish(topic, json.dumps(self.__message))
        
        self.client.loop_start()


def refresh():
    """
    Registers the Environment Manager to the
    Resource Catalog making a post.
    """
    global database
    
    with open(database, "r") as file:
        db = json.load(file)

    payload = {
        'ip': db["ip"], 
        'port': db["port"],
        'functions': [db["function"]]}
    
    url = resCatEndpoints+'/environment_manager'
    
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


def getStrategies():
    """
    Retrieves all the environment strategies present in the 
    Resource Catalog and creates the relative topics.
    Called at the BOOT.
    """

    global database
    global new_strat

    url = resCatEndpoints+'/strategy/manager'
    params = {"strategyType": "environment"}
    strategies = requests.get(url, params=params).json()

    strategy_list = []
    for strat in strategies:
        try:
            userID = strat['userID']
            greenHouseID = strat["greenHouseID"]
            temperature = strat["strat"]["temperature"]
            humidity = strat["strat"]["humidity"]
            active = strat["active"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')
        else:
            topic_act_temp = str(userID)+"/"+str(greenHouseID)+"/environment/temperature"
            topic_act_hum = str(userID)+"/"+str(greenHouseID)+"/environment/humidity"

            topic_sens_temp = str(userID)+"/"+str(greenHouseID)+"/sensors/temperature"
            topic_sens_hum = str(userID)+"/"+str(greenHouseID)+"/sensors/humidity"

            strategy_list.append({
                                    "userID": int(userID),
                                    "greenHouseID": int(greenHouseID),
                                    "topic_sens": {
                                        "topic_temp": topic_sens_temp, 
                                        "topic_hum": topic_sens_hum, 
                                    },
                                    "topic_act": {
                                        "topic_temp": topic_act_temp, 
                                        "topic_hum": topic_act_hum, 
                                    }, 
                                    "temperature": float(temperature),
                                    "humidity": float(humidity),
                                    "active": active,
                                    "window_factor": 0,
                                    "humidifier_factor": 0,
                                    "ac_factor": 0,
                                    "window_open": False,
                                    "last_message_temp": 0,
                                    "last_message_hum": 0,
                                    "timestamp": time.time() 
                                })

            # Subscribe to the MQTT topics of humidity and temperature
            mqtt_handler.subscribe(topic_sens_temp)
            mqtt_handler.subscribe(topic_sens_hum)

            topic_weather = str(userID)+"/"+str(greenHouseID)+"/weather"
            mqtt_handler.subscribe(topic_weather)
    
    with open(database, "r") as file:
        db = json.load(file)
    
    db["strategies"] = strategy_list
    new_strat = True
    
    with open(database, "w") as file:
        json.dump(db, file, indent=3)


def getFactors(userID, greenHouseID):
    """
    Retrieves from the Resource Catalog the hyperparameters
    of a specific greenhouse of a user.
    """

    global database

    url = resCatEndpoints+'/device_connectors'
    params = {"id": userID, "greenHouseID": greenHouseID}
    devConn = requests.get(url, params=params).json()

    if len(devConn) == 1:
        try:
            window_factor = devConn[0]['window_factor']
            humidifier_factor = devConn[0]['humidifier_factor']
            ac_factor = devConn[0]['ac_factor']
        
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        # Load the database
        with open(database, "r") as file:
            db = json.load(file)

        for strat in db["strategies"]:
            if strat["userID"] == int(userID) and strat["greenHouseID"] == int(greenHouseID):
                strat["window_factor"] = int(window_factor)
                strat["humidifier_factor"] = int(humidifier_factor)
                strat["ac_factor"] = int(ac_factor)
                strat["timestamp"] = time.time()

        with open(database, "w") as file:
            json.dump(db, file, indent=3)
    else:
        # For now, we have just 1 device connector even if we obtain a list from the GET
        pass


def setLastMessage(userID, greenHouseID, type):
    """
    Set the time for the last message of type <type>.
    """

    global database

    # Load the database
    with open(database, "r") as file:
        db = json.load(file)

    for strat in db["strategies"]:
        if strat["userID"] == int(userID) and strat["greenHouseID"] == int(greenHouseID):
            strat["last_message_"+type] = time.time()

    with open(database, "w") as file:
        json.dump(db, file, indent=3)



if __name__=="__main__":
    
    time.sleep(7)

    # Configure CherryPy
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

    # Get the broker information from the Resource Catalog
    getBroker()
    
    with open(database, "r") as file:
        db = json.load(file)

    # Initialize the MQTT handler with the broker information
    broker_dict = db["broker"]
    mqtt_handler = MQTT_subscriber_publisher(broker_dict["ip"], broker_dict["port"])
    mqtt_handler.start()

    last_refresh = time.time() 

    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    time.sleep(0.5)
    refresh()

    # BOOT FUNCTION TO RETRIEVE STARTING STRATEGIES
    time.sleep(0.5)
    getStrategies()
    
    refresh_freq = 60
    percentange = 0.95

    while True:
        timestamp = time.time()
        time_start = datetime.fromtimestamp(timestamp)
        time_start = time_start.strftime("%H:%M:%S")

        if timestamp-last_refresh >= refresh_freq:

            last_refresh = time.time()
            refresh()

        if new_strat:
            # Update the strategies if there are any changes
            with open(database, "r") as file:
                db = json.load(file)

            new_strat = False

        # At the beginning we don't have any measures but we could already have some strategies
        # => we cannot enter this for if we don't have any new actual measure (if we already have some actual measures
        # but they are not new it's useless to send new commands, they were already sent previously)
        if new_measures["new"]:
            time.sleep(0.5)
            for strat in db["strategies"]:

                # If the window is opened the strategy must stop to not waste energy
                if strat["active"] == True and strat["window_open"] == False:
                    
                    # Accessible only if we have a new measure for the temperature and if it's passed enough time from the last message 
                    if new_measures["temperature"] and (timestamp - strat["last_message_temp"]) > strat["ac_factor"]:
                        with open(database, "r") as file:
                            db = json.load(file)

                        actual_temp = db["actual_temperature"]
                        new_measures["temperature"] = False
                        new_measures["new"] = False

                        for temp in actual_temp:
                            if temp["userID"] == strat["userID"] and temp["greenHouseID"] == strat["greenHouseID"]:
                                
                                # If the hyperparameters are not yet present we must retrieve them first
                                if strat["ac_factor"] == 0:
                                    getFactors(strat["userID"], strat["greenHouseID"])
                                    time.sleep(0.5)

                                if temp["temperature"] > (2-percentange)*strat["temperature"] or temp["temperature"] < percentange*strat["temperature"]:
                                    mqtt_handler.publish(strat["topic_act"]["topic_temp"], strat["temperature"], "temperature")
                                    
                                    setLastMessage(strat["userID"], strat["greenHouseID"], "temp")
                                    new_strat = True


                    # Accessible only if we have a new measure for the humidity and if it's passed enough time from the last message 
                    if new_measures["humidity"] and (timestamp - strat["last_message_hum"]) > strat["humidifier_factor"]:
                        with open(database, "r") as file:
                            db = json.load(file)

                        actual_hum = db["actual_humidity"]
                        new_measures["humidity"] = False
                        new_measures["new"] = False

                        for hum in actual_hum:
                            if hum["userID"] == strat["userID"] and hum["greenHouseID"] == strat["greenHouseID"]:

                                if strat["ac_factor"] == 0:
                                    getFactors(strat["userID"], strat["greenHouseID"])
                                    time.sleep(0.5)

                                if hum["humidity"] > (2-percentange)*strat["humidity"] or hum["humidity"] < percentange*strat["humidity"]:
                                    mqtt_handler.publish(strat["topic_act"]["topic_hum"], strat["humidity"], "humidity")
                                    
                                    setLastMessage(strat["userID"], strat["greenHouseID"], "hum")
                                    new_strat = True