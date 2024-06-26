import cherrypy
import requests
import time
from datetime import datetime
import json
import paho.mqtt.client as mqtt

from MQTT.MyMQTT import *

new_strat = False
database = "src/db_examples/irrigation_manager_db_ex.json"
resCatEndpoints = "http://127.0.0.1:4000"

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
            activeIrr = input['active']
            stratID = input['stratID']
            time_start = input['time']
            water_quantity = input['water_quantity']
            activeStrat = input['activeStrat']
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        
        topic = str(userID)+"/"+str(greenHouseID)+"/irrigation/"+str(stratID)
        database_dict = json.load(open(database, "r"))
    
        new_strategy = {
            "topic": topic, 
            "time": time_start, 
            "water_quantity": water_quantity, 
            "active": activeStrat, 
            "timestamp": time.time()
        }
        database_dict["strategies"].append(new_strategy)

        if activeIrr == False:
            for strat in database_dict["strategies"]:
                split_topic = strat["topic"].split("/")
                if int(split_topic[0]) == userID and int(split_topic[1]) == greenHouseID:
                    strat["active"] = activeIrr

        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)

    def PUT(self, *path, **queries):
        """
        Modify the state of activity of one or all the strategies 
        owned by a specific user and greenhouse.
        """

        global database 
        global new_strat
        input = json.loads(cherrypy.request.body.read())
        database_dict = json.load(open(database, "r"))

        try:
            userID = input['userID']
            greenHouseID = input['greenHouseID']
            activeIrr = input['active']
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        try:
            stratID = input['stratID']
            activeStrat = input['activeStrat']
        except:
            for strat in database_dict["strategies"]:
                split_topic = strat["topic"].split("/")
                if int(split_topic[0]) == userID and int(split_topic[1]) == greenHouseID:
                    strat["active"] = activeIrr
        else:
            for strat in database_dict["strategies"]:
                split_topic = strat["topic"].split("/")
                if int(split_topic[0]) == userID and int(split_topic[1]) == greenHouseID and int(split_topic[3]) == stratID:
                    strat["active"] = activeStrat
        
        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)

    def DELETE(self, *path, **queries):
        """
        Delete one or all the strategies
        owned by a specific user and greenhouse.
        """

        global database
        global new_strat

        try:
            userID = queries['userID']
            greenHouseID = queries['greenHouseID']
            stratID = queries['stratID']
        except:
            try:
                # If no stratID is passed it means that all the strategies must be eliminated
                userID = queries['userID']
                greenHouseID = queries['greenHouseID']
            except: 
                pass
            else:
                database_dict = json.load(open(database, "r"))

                idxs = []
                for idx, strat in enumerate(database_dict["strategies"]):
                    split_topic = strat["topic"].split("/")
                    if int(split_topic[0]) == userID and int(split_topic[1]) == greenHouseID:
                        idxs.append(idx)

                for idx in idxs:
                    database_dict["strategies"].pop(idx)
                
                new_strat = True
                json.dump(database_dict, open(database, "w"), indent=3)

            raise cherrypy.HTTPError(400, 'Bad request')
        else:
            topic = str(userID)+"/"+str(greenHouseID)+"/irrigation/"+str(stratID)
            database_dict = json.load(open(database, "r"))

            idx = 0
            for strat in database_dict["strategies"]:
                if strat["topic"] == topic:
                    break
                else:
                    idx += 1
            database_dict["strategies"].pop(idx)

            for strat in database_dict["strategies"]:
                split_topic = strat["topic"].split("/")
                if int(split_topic[0]) == userID and int(split_topic[1]) == greenHouseID and int(split_topic[3]) > stratID:
                    strat["topic"] = userID+"/"+greenHouseID+"/irrigation/"+str(int(split_topic[3])-1)
            
            new_strat = True
            json.dump(database_dict, open(database, "w"), indent=3)


class MQTT_publisher(object):
    def __init__(self, broker, port):
        self.client=mqtt.Client("IrrigationStrat")
        self.broker = broker
        self.port = port
        
        # bn: macro strategy name (irrigation), e: events (objects), v: value(s) (depends on what we want to set with the strategy),  t: timestamp
        self.message={'bn': "IrrigationStrat", 'e': {'t': None, 'v': None}}

    def start(self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()

    def publish(self, topic, value):
        self.client.loop_stop()
        self.message["e"]["t"] = time.time()
        self.message["e"]["v"] = value

        self.client.publish(topic, json.dumps(self.message))
        print(f'irrigation manager sent to topic: {topic}, value: {self.message}')
        self.client.loop_start()


def refresh():
    """
    Registers the Irrigation Manager to the
    Resource Catalog making a post.
    """
    
    global database
    db = json.load(open(database, "r"))

    payload = {
        'ip': db["ip"], 
        'port': db["port"],
        'functions': ["regStrategy"]}
    
    url = resCatEndpoints+'/irrigation_manager'
    
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
    Retrieves all the irrigation strategies 
    present in the Resource Catalog.
    Called at the BOOT.
    """

    global database

    url = resCatEndpoints+'/strategy/manager'
    params = {"strategyType": "irrigation"}
    strategies = requests.get(url, params=params).json()

    strategy_list = []
    strategy_dict = {
        "topic": "",
        "time": "00:00:00",
        "water_quantity": -1,
        "active": False,
        "timestamp": -1 
    }
    for strat in strategies:
        try:
            userID = strat['userID']
            greenHouseID = strat["greenHouseID"]
            stratID = strat["strat"]["id"]
            time_start = strat["strat"]["time"]
            water_quantity = strat["strat"]["water_quantity"]
            active_strat = strat["strat"]["active"]
            active = strat["active"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')
        else:
            topic = str(userID)+"/"+str(greenHouseID)+"/irrigation/"+str(stratID)
            strategy_dict["topic"] = topic
            strategy_dict["time"] = time_start
            strategy_dict["water_quantity"] = water_quantity
            if active == False:
                strategy_dict["active"] = False
            else:
                strategy_dict["active"] = active_strat
            strategy_dict["timestamp"] = time.time()
            strategy_list.append(strategy_dict)

    database_dict = json.load(open(database, "r"))
    database_dict["strategies"] = strategy_list
    json.dump(database_dict, open(database, "w"), indent=3)


if __name__=="__main__":

    # conf = {
    #     '/': {
    #         'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
    #         'tools.sessions.on': True,
    #     }
    # }
    # cherrypy.tree.mount(RegStrategy(), '/regStrategy', conf)

    # cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    # cherrypy.config.update({'server.socket_port': 8080})

    # cherrypy.engine.start()
    # # cherrypy.engine.block()


    # last_refresh = time.time() 
    # # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    # refresh()

    # # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    # getBroker()

    # # BOOT FUNCTION TO RETRIEVE STARTING STRATEGIES
    # getStrategies()

    refresh_freq = 10
    
    broker_dict = json.load(open(database, "r"))["broker"]
    strategies = json.load(open(database, "r"))["strategies"]
    
    publisher = MQTT_publisher(broker_dict["ip"], broker_dict["port"])
    publisher.start()
    
    last_refresh = time.time()
    istime = True
    while True:
        timestamp = time.time()
        time_start = datetime.fromtimestamp(timestamp)
        time_start = time_start.strftime("%H:%M:%S")

        if timestamp-last_refresh >= refresh_freq:

            last_refresh = time.time()
            # refresh()

        if new_strat:

            strategies = json.load(open(database, "r"))["strategies"]
            new_strat = False

        for strat in strategies:
            # AGGIUNGERE UN RANGE DI CONTROLLO IN MODO DA NON RISCHIARE DI PERDERE IL COMANDO PER QUESTIONE DI SECONDI
            # Just for prove changed and for or here
            
            # if strat["time"] == time_start and strat["active"] == True:
            if istime and strat["active"] == True:
                publisher.publish(strat["topic"], strat["water_quantity"])
                istime = False