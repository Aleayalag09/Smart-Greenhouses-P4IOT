import json
import time
import requests
import cherrypy
import Devices

from MQTT.MyMQTT import *

database = "src/db/device_connector_db.json"
resourceCatalogIP = ""
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

        # measure = json.loads(payload)
        # # [0]: userID, [1]: greenHouseID, [2]: "sensors", [3]: sensor type (temperature/humidity)
        # topic = topic.split("/")

        # try:
        #     # Unit of measure of the measure
        #     # unit = measure['unit']
        #     value = measure['value']
        #     timestamp = measure['timestamp']
        # except:
        #     raise cherrypy.HTTPError(400, 'Wrong parameters')

        # db = json.load(open(database, "r"))
        # for actualValues in db["actual_"+topic[3]]:
        #     if actualValues["userID"] == topic[0] and actualValues["greenHouseID"] == topic[1]:
        #         actualValues[topic[3]] = value
        #         actualValues["timestamp"] = timestamp
        #         new_measures["new"] = True
        #         new_measures[topic[3]] = True
        #         break
        # json.dump(db, open(database, "w"), indent=3)

    def publish(self, topic, value, measureType):
        self.__message["bn"] = measureType
        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        self.client.myPublish(topic, self.__message)


# REGISTER CONTINOUSLY THE MANAGER TO THE RESOURCE CATALOG
def refresh():
    payload = {'ip': "IP of the DeviceConnector", 'port': "PORT of the DeviceConnector",
               'functions': [""]}
    url = 'URL of the RESOURCE_CATALOG/device_connectors'
    
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


# FUNCTION NEEDED AT THE BOOT TO REGISTER ALL THE DEVICES THIS SCRIPT CAN CONTROL
def BOOT_FUNCTION():
    pass

    
                        
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
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    refresh()

    # BOOT FUNCTION TO RETRIEVE STARTING STRATEGIES
    BOOT_FUNCTION()

    strategies = json.load(open(database, "r"))["strategies"]
        
        