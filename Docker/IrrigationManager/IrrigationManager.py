import cherrypy
import requests
import time
from datetime import datetime
import json

from MyMQTT import *

new_strat = False
database = "irrigation_manager_db.json"

class Strategy(object):
    exposed = True
 
    def POST(self, *path):
        global database
        global new_strat
        input = json.loads(cherrypy.request.body.read())

        try:
            id = input['id']
            greenHouseID = input['greenHouseID']
            deviceID = input['deviceID']
            time_start = input['time']
            water_quantity = input['water_quantity']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        topic = id+"/"+greenHouseID+"/"+deviceID+"/irrigation/"

        database_dict = json.load(open(database, "r"))

        update = False
        for strategy in database_dict["strategies"]:

            if strategy[0] == topic:
                strategy[1] = time_start
                strategy[2] = water_quantity
                strategy[3] = time.time()

                update = True

        if update == False:
            new_strategy = {"topic": topic, "time": time_start, "water_quantity": water_quantity, "last_update": time.time()}
            database_dict["strategy"].append(new_strategy)

        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)


class MQTT_publisher(object):
    def __init__(self, broker, port):
        # bn: macro strategy name (irrigation), e: events (objects), v: value(s) (depends on what we want to set with the strategy),  t: timestamp
        self.__message={'bn': "IrrigationStrat", 'e': {'t': None, 'v': None}}

        self.client=MyMQTT("IrrigationStrat", broker, port, None)

    def start (self):
        self.client.start()

    def stop (self):
        self.client.stop()

    def publish(self, topic, value):
        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        self.client.myPublish(topic, self.__message)


# REGISTER CONTINOUSLY THE STRATEGIES TO THE RESOURCE CATALOG
def refresh():
    payload = {'ip': "IP of the IrrigationManager", 'port': "PORT of the IrrigationManager",
               'functions': ["strategy"]}
    url = 'URL of the RESOURCE_CATALOG/POST managers'
    
    requests.post(url, payload)


# DIRECT REQUEST TO THE RESOURCE CATALOG? IF WE USE THE SERVICE CATALOG WE NEED TO CONTACT IT BEFORE IN ORDER TO OBTAIN URL AND FUNCTIONS OF THE RESOURCE CATALOG
def broker():
    global database

    url = 'URL of the RESOURCE_CATALOG/GET broker'
    broker = requests.get(url)

    try:
        ip = broker['ip']
        port = broker["port"]
    
    except:
        raise cherrypy.HTTPError(400, 'Bad request')

    database_dict = json.load(open(database, "r"))
    database_dict["broker"] = broker
    json.dump(database_dict, open(database, "w"), indent=3)


if __name__=="__main__":

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(Strategy(), '/strategy', conf)

    cherrypy.config.update({'server.socket_host': '127.18.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()


    last_refresh = time.time() 
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    refresh()

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    broker()
    broker_dict = json.load(open(database, "r"))["broker"]
    
    publisher = MQTT_publisher()
    publisher.__init__(broker_dict["broker"], broker_dict["port"])
    publisher.start()

    while True:
        timestamp = time.time()
        time_start = datetime.fromtimestamp(timestamp)
        time_start = time_start.strftime("%H:%M:%S")

        if timestamp-last_refresh >= 300:

            last_refresh = time.time()
            refresh()

        if new_strat:

            strategies = json.load(open(database, "r"))[strategies]
            new_strat = False

        for strat in strategies:

            if time_start==strat["time"]:
                publisher.publish(strat["topic"], strat["water_qnt"])