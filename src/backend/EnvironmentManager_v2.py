import cherrypy
import requests
import time
from datetime import datetime
import json

from MQTT.MyMQTT import *

new_strat = False
new_measures = {
    "new": False,
    "temperature": False,
    "humidity": False
}
database = "src/db/environment_manager_db.json"
resourceCatalogIP = ""

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
        
        topic_act_temp = str(userID)+"/"+str(greenHouseID)+"/environment/temperature"
        topic_act_hum = str(userID)+"/"+str(greenHouseID)+"/environment/humidity"

        topic_sens_temp = str(userID)+"/"+str(greenHouseID)+"/sensors/temperature"
        topic_sens_hum = str(userID)+"/"+str(greenHouseID)+"/sensors/humidity"
        database_dict = json.load(open(database, "r"))
    
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

        database_dict["strategies"].append(new_strategy)

        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)

    def PUT(self, *path, **queries):
        """
        Modify the state of activity of the strategy 
        owned by a specific user and greenhouse.
        """

        global database 
        global new_strat
        input = json.loads(cherrypy.request.body.read())
        database_dict = json.load(open(database, "r"))

        try:
            userID = input['userID']
            greenHouseID = input['greenHouseID']
            active = input['active']
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        else:
            for strat in database_dict["strategies"]:
                split_topic = strat["topic_sens"]["topic_temp"].split("/")
                if int(split_topic[0]) == userID and int(split_topic[1]) == greenHouseID:
                    strat["active"] = active
        
        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)

    def DELETE(self, *path, **queries):
        """
        Delete a strategy owned by a specific user and greenhouse.
        """

        global database
        global new_strat

        try:
            userID = queries['userID']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        database_dict = json.load(open(database, "r"))

        idx = 0
        for strat in database_dict:
            if strat["topic_sens"]["topic_temp"].split("/")[0] == userID and strat["topic_sens"]["topic_temp"].split("/")[1] == greenHouseID:
                # Unsubscribe from the sensors topics before removing completely the strategy from the db
                mqtt_handler.unsubscribe(strat["topic_sens"]["topic_temp"])
                mqtt_handler.unsubscribe(strat["topic_sens"]["topic_hum"])
                break
            else:
                idx += 1
        database_dict["strategies"].pop(idx)

        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)


class MQTT_subscriber_publisher(object):
    def __init__(self, broker, port):
        # bn: macro strategy name (environment), e: events (objects), v: value(s) (depends on what we want to set with the strategy), t: timestamp
        self.__message={'bn': "EnvironmentStrat", 'e': {'t': None, 'v': None}}

        self.client=MyMQTT("EnvironmentStrat", broker, port, None)

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
        global new_measures

        measure = json.loads(payload)
        # [0]: userID, [1]: greenHouseID, [2]: "sensors", [3]: sensor type (temperature/humidity)
        topic = topic.split("/")

        try:
            # Unit of measure of the measure
            # unit = measure['unit']
            value = measure['e']['v']
            timestamp = measure['e']['t']
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        db = json.load(open(database, "r"))
        for actualValues in db["actual_"+topic[3]]:
            if actualValues["userID"] == topic[0] and actualValues["greenHouseID"] == topic[1]:
                actualValues[topic[3]] = value
                actualValues["timestamp"] = timestamp
                new_measures["new"] = True
                new_measures[topic[3]] = True
                break
        json.dump(db, open(database, "w"), indent=3)

    def publish(self, topic, value):
        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        self.client.myPublish(topic, self.__message)


def refresh():
    """
    Registers the Environment Manager to the
    Resource Catalog making a post.
    """
    global database
    db = json.load(open(database, "r"))

    payload = {
        'ip': db["ip"], 
        'port': db["port"],
        'functions': ["regStrategy"]}
    
    url = 'URL of the RESOURCE_CATALOG/environment_manager'
    
    requests.post(url, payload)


def getBroker():
    """
    Retrieves from the Resource Catalog the endpoints
    (ip, port, timestamp) of the broker used in the system.
    """

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


def getStrategies():
    """
    Retrieves all the environment strategies present in the 
    Resource Catalog and creates the relative topics.
    Called at the BOOT.
    """

    global database

    url = 'URL of the RESOURCE_CATALOG/strategy/manager'
    params = {"strategyType": "environment"}
    strategies = requests.get(url, params=params).json()

    strategy_list = []
    strategy_dict = {
        "topic_sens": {
            "topic_temp": "", 
            "topic_hum": "", 
        },
        "topic_act": {
            "topic_temp": "", 
            "topic_hum": "", 
        }, 
        "temperature": -1,
        "humidity": -1,
        "active": False,
        "timestamp": -1 
    }
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

            strategy_dict["topic_sens"]["topic_temp"] = topic_sens_temp
            strategy_dict["topic_sens"]["topic_hum"] = topic_sens_hum
            strategy_dict["topic_act"]["topic_temp"] = topic_act_temp
            strategy_dict["topic_act"]["topic_hum"] = topic_act_hum
            strategy_dict["temperature"] = temperature
            strategy_dict["humidity"] = humidity
            strategy_dict["active"] = active
            strategy_dict["timestamp"] = time.time()
            strategy_list.append(strategy_dict)

            # Subscribe to the MQTT topics of humidity and temperature
            mqtt_handler.subscribe(topic_sens_temp)
            mqtt_handler.subscribe(topic_sens_hum)

    database_dict = json.load(open(database, "r"))
    database_dict["strategies"] = strategy_list
    json.dump(database_dict, open(database, "w"), indent=3)



if __name__=="__main__":

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
                                    mqtt_handler.publish(strat["topic_act"]["topic_temp"], strat["temperature"])

                    # Accessible only if we have a new measure for the humidity
                    if new_measures["humidity"]:
                        actual_hum = json.load(open(database, "r"))["actual_humidity"]
                        new_measures["humidity"] = False
                        new_measures["new"] = False

                        for hum in actual_hum:
                            if hum["userID"] == int(split_topic[0]) and hum["greenHouseID"] == int(split_topic[1]):

                                if hum["humidity"] > percentange*strat["humidity"] or hum["humidity"] < percentange*strat["humidity"]:
                                    mqtt_handler.publish(strat["topic_act"]["topic_hum"], strat["humidity"])