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
        database_dict = json.load(open(database, "r"))

        # Create a new strategy object
        new_strategy = {
            "topic_sens": {
                "topic_temp": topic_sens_temp, 
                "topic_hum": topic_sens_hum, 
            },
            "topic_act": {
                "topic_temp": topic_act_temp, 
                "topic_hum": topic_act_hum, 
            }, 
            "temperature": temperature, 
            "humidity": humidity,
            "active": active, 
            "timestamp": time.time()
        }

        # Subscribe to the MQTT topics of humidity and temperature
        mqtt_handler.subscribe(topic_sens_temp)
        mqtt_handler.subscribe(topic_sens_hum)

        # Add the new strategy to the database
        database_dict["strategies"].append(new_strategy)

        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)

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
        database_dict = json.load(open(database, "r"))

        # Extract input parameters from the request
        try:
            userID = input['userID']
            greenHouseID = input['greenHouseID']
            active = input['active']
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        else:
            # Update the state of activity for the matching strategy
            for strat in database_dict["strategies"]:
                split_topic = strat["topic_sens"]["topic_temp"].split("/")
                if int(split_topic[0]) == userID and int(split_topic[1]) == greenHouseID:
                    strat["active"] = active
        
        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)

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
        
        database_dict = json.load(open(database, "r"))

        idx = 0
        for strat in database_dict:
            # Check if the strategy matches the provided userID and greenHouseID
            if strat["topic_sens"]["topic_temp"].split("/")[0] == userID and strat["topic_sens"]["topic_temp"].split("/")[1] == greenHouseID:
                # Unsubscribe from the sensors topics before removing completely the strategy from the db
                mqtt_handler.unsubscribe(strat["topic_sens"]["topic_temp"])
                mqtt_handler.unsubscribe(strat["topic_sens"]["topic_hum"])
                break
            else:
                idx += 1
        
        # Remove the strategy from the strategies list in the database
        database_dict["strategies"].pop(idx)

        new_strat = True

        # Write the updated database back to the file
        json.dump(database_dict, open(database, "w"), indent=3)

        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "timestamp": time.time()
        }
        return result


class MQTT_subscriber_publisher(object):
    
    def __init__(self, broker, port):
        
        db_file = open(database, "r")
        db = json.load(db_file)
        db_file.close()
        
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
        db_file = open(database, "r")
        db = json.load(db_file)
        db_file.close()

        # Update the corresponding actual value in the database
        for actualValues in db["actual_"+measuretype]:
            if actualValues["userID"] == int(topic[0]) and actualValues["greenHouseID"] == int(topic[1]):
                actualValues[measuretype] = value
                actualValues["timestamp"] = timestamp
                new_measures["new"] = True
                new_measures[measuretype] = True
                break

        # Write the updated database back to the file
        json.dump(db, open(database, "w"), indent=3)

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
    db_file = open(database, "r")
    db = json.load(db_file)
    db_file.close()

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
    database_dict = json.load(open(database, "r"))

    # Update the broker information in the database
    database_dict["broker"]["ip"] = ip
    database_dict["broker"]["port"] = port
    database_dict["broker"]["timestamp"] = time.time()
    json.dump(database_dict, open(database, "w"), indent=3)


def getStrategies():
    """
    Retrieves all the environment strategies present in the 
    Resource Catalog and creates the relative topics.
    Called at the BOOT.
    """

    global database

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
            topic_sens_hum = str(userID)+"/"+str(greenHouseID)+"/sensors/temperature"

            strategy_list.append({
                                    "topic_sens": {
                                        "topic_temp": topic_sens_temp, 
                                        "topic_hum": topic_sens_hum, 
                                    },
                                    "topic_act": {
                                        "topic_temp": topic_act_temp, 
                                        "topic_hum": topic_act_hum, 
                                    }, 
                                    "temperature": temperature,
                                    "humidity": humidity,
                                    "active": active,
                                    "timestamp": time.time() 
                                })

            # Subscribe to the MQTT topics of humidity and temperature
            mqtt_handler.subscribe(topic_sens_temp)
            mqtt_handler.subscribe(topic_sens_hum)

    database_dict = json.load(open(database, "r"))
    database_dict["strategies"] = strategy_list
    json.dump(database_dict, open(database, "w"), indent=3)



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

    # Initialize the MQTT handler with the broker information
    broker_dict = json.load(open(database, "r"))["broker"]
    mqtt_handler = MQTT_subscriber_publisher(broker_dict["ip"], broker_dict["port"])
    mqtt_handler.start()

    last_refresh = time.time() 

    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    refresh()

    # BOOT FUNCTION TO RETRIEVE STARTING STRATEGIES
    getStrategies()

    strategies = json.load(open(database, "r"))["strategies"]
    
    refresh_freq = 60
    percentange = 0.98

    while True:
        timestamp = time.time()
        time_start = datetime.fromtimestamp(timestamp)
        time_start = time_start.strftime("%H:%M:%S")

        if timestamp-last_refresh >= refresh_freq:

            last_refresh = time.time()
            refresh()

        if new_strat:
            # Update the strategies if there are any changes
            strategies = json.load(open(database, "r"))["strategies"]
            new_strat = False

        # At the beginning we don't have any measures but we could already have some strategies
        # => we cannot enter this for if we don't have any new actual measure (if we already have some actual measures
        # but they are not new it's useless to send new commands, they were already sent previously)
        if new_measures["new"]:
            for strat in strategies:

                if strat["active"] == True:
                    # [0]: userID, [1]: greenHouseID, [2]: "sensors", [3]: sensor type (temperature/humidity)
                    split_topic = strat["topic_sens"]["topic_temp"].split("/")
                    
                    # Accessible only if we have a new measure for the temperature
                    if new_measures["temperature"]:
                        actual_temp = json.load(open(database, "r"))["actual_temperature"]
                        new_measures["temperature"] = False
                        new_measures["new"] = False

                        for temp in actual_temp:
                            if temp["userID"] == int(split_topic[0]) and temp["greenHouseID"] == int(split_topic[1]):

                                if temp["temperature"] > percentange*strat["temperature"] or temp["temperature"] < percentange*strat["temperature"]:
                                    mqtt_handler.publish(strat["topic_act"]["topic_temp"], strat["temperature"], "temperature")

                    # Accessible only if we have a new measure for the humidity
                    if new_measures["humidity"]:
                        actual_hum = json.load(open(database, "r"))["actual_humidity"]
                        new_measures["humidity"] = False
                        new_measures["new"] = False

                        for hum in actual_hum:
                            if hum["userID"] == int(split_topic[0]) and hum["greenHouseID"] == int(split_topic[1]):

                                if hum["humidity"] > percentange*strat["humidity"] or hum["humidity"] < percentange*strat["humidity"]:
                                    mqtt_handler.publish(strat["topic_act"]["topic_hum"], strat["humidity"], "humidity")