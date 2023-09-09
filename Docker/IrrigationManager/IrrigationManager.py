import cherrypy
import requests
import time
from datetime import datetime
import json
import paho.mqtt.client as mqtt

new_strat = False
database = "db/irrigation_manager_db.json"
resCatEndpoints = "http://resource_catalog:8080"

with open(database, "r") as file:
    db_test = json.load(file)

class RegStrategy(object):
    exposed = True
 
    def POST(self, *path, **queries):
        """
        Logs a new strategy for a specific user and greenhouse
        and updates the state of activity of the greenhouse.
        """

        global database
        global new_strat
        global db_test
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
        
        topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/irrigation/"+str(stratID)

        with open(database, "r") as file:
            db = json.load(file)

        new_strategy = {
            "topic": topic, 
            "time": time_start, 
            "water_quantity": water_quantity, 
            "active": activeStrat, 
            "timestamp": time.time()
        }
        db["strategies"].append(new_strategy)

        if activeIrr == False:
            for strat in db["strategies"]:
                split_topic = strat["topic"].split("/")
                if int(split_topic[1]) == int(userID) and int(split_topic[2]) == int(greenHouseID):
                    strat["active"] = activeIrr

        new_strat = True

        with open(database, "w") as file:
            json.dump(db, file, indent=3)

        with open(database, "r") as file:
            db_test = json.load(file)
        
        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "time": time_start, 
            "water_quantity": water_quantity, 
            "active": activeStrat, 
            "timestamp": time.time()
        }
        return result

    def PUT(self, *path, **queries):
        """
        Modify the state of activity of one or all the strategies 
        owned by a specific user and greenhouse.
        """

        global database 
        global new_strat
        global db_test
        input = json.loads(cherrypy.request.body.read())

        with open(database, "r") as file:
            db = json.load(file)

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
            for strat in db["strategies"]:
                split_topic = strat["topic"].split("/")
                if int(split_topic[1]) == int(userID) and int(split_topic[2]) == int(greenHouseID):
                    strat["active"] = activeIrr
        else:
            for strat in db["strategies"]:
                split_topic = strat["topic"].split("/")
                if int(split_topic[1]) == int(userID) and int(split_topic[2]) == int(greenHouseID) and int(split_topic[4]) == int(stratID):
                    strat["active"] = activeStrat
        
        new_strat = True

        with open(database, "w") as file:
            json.dump(db, file, indent=3)
            
        with open(database, "r") as file:
            db_test = json.load(file)
        
        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "active": activeIrr, 
            "timestamp": time.time()
        }
        return result

    def DELETE(self, *path, **queries):
        """
        Delete one or all the strategies
        owned by a specific user and greenhouse.
        """

        global database
        global new_strat
        global db_test

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
                with open(database, "r") as file:
                    db = json.load(file)

                idxs = []
                for idx, strat in enumerate(db["strategies"]):
                    split_topic = strat["topic"].split("/")
                    if int(split_topic[1]) == int(userID) and int(split_topic[2]) == int(greenHouseID):
                        idxs.append(idx)

                idxs.sort(reverse=True)
                for idx in idxs:
                    db["strategies"].pop(idx)
                
                new_strat = True

                with open(database, "w") as file:
                    json.dump(db, file, indent=3)
                    
                with open(database, "r") as file:
                    db_test = json.load(file)
        
                return

            raise cherrypy.HTTPError(400, 'Bad request')
        else:
            topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/irrigation/"+str(stratID)

            with open(database, "r") as file:
                db = json.load(file)

            idx = 0
            for strat in db["strategies"]:
                if strat["topic"] == topic:
                    break
                else:
                    idx += 1

            try:
                db["strategies"].pop(idx)

                for strat in db["strategies"]:
                    split_topic = strat["topic"].split("/")
                    if int(split_topic[1]) == int(userID) and int(split_topic[2]) == int(greenHouseID) and int(split_topic[4]) > int(stratID):
                        strat["topic"] = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/irrigation/"+str(int(split_topic[4])-1)
                
                new_strat = True

                with open(database, "w") as file:
                    json.dump(db, file, indent=3)
                    
                with open(database, "r") as file:
                    db_test = json.load(file)

            except:
                print("No strategy registered")
        
        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "timestamp": time.time()
        }
        return result


class MQTT_publisher(object):

    def __init__(self, broker, port):

        with open(database, "r") as file:
            db = json.load(file)

        self.client = mqtt.Client("IrrigationManager_"+str(db["ID"]))
        self.broker = broker
        self.port = port
        self.topic = None

        # bn: macro strategy name (irrigation), e: events (objects), v: value(s) (depends on what we want to set with the strategy),  t: timestamp
        self.__message={'bn': "irrigation", 'e': {'t': None, 'v': None}}

    def start (self):
        self.client.connect(self.broker, self.port)
        self.client.loop_start()

    def stop (self):
        self.client.loop_stop()

    def publish(self, topic, value):
        self.client.loop_stop()

        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        self.client.publish(topic, json.dumps(self.__message))
        
        self.client.loop_start()


def refresh():
    """
    Registers the Irrigation Manager to the
    Resource Catalog making a post.
    """
    
    global database

    with open(database, "r") as file:
        db = json.load(file)

    payload = {
        'ip': db["ip"], 
        'port': db["port"],
        'functions': [db["function"]]}
    
    url = resCatEndpoints+'/irrigation_manager'
    
    requests.post(url, json.dumps(payload))


def getBroker():
    """
    Retrieves from the Resource Catalog the endpoints
    (ip, port, timestamp) of the broker used in the system.
    """

    global database
    global db_test

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
        
    with open(database, "r") as file:
        db_test = json.load(file)
        


def getStrategies():
    """
    Retrieves all the irrigation strategies 
    present in the Resource Catalog.
    Called at the BOOT.
    """

    global database
    global new_strat
    global db_test

    url = resCatEndpoints+'/strategy/manager'
    params = {"strategyType": "irrigation"}
    strategies = requests.get(url, params=params).json()

    strategy_list = []
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
            print('Wrong parameters')
        else:
            topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/irrigation/"+str(stratID)
            if active == True:
                active = active_strat

            strategy_list.append({
                                    "topic": topic,
                                    "time": time_start,
                                    "water_quantity": water_quantity,
                                    "active": active,
                                    "timestamp": time.time()
                                })

    with open(database, "r") as file:
        db = json.load(file)

    db["strategies"] = strategy_list
    new_strat = True

    with open(database, "w") as file:
        json.dump(db, file, indent=3)
        
    with open(database, "r") as file:
        db_test = json.load(file)




if __name__=="__main__":

    time.sleep(5)

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

    getBroker()

    last_refresh = time.time() 
    
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    time.sleep(0.5)
    refresh()

    # BOOT FUNCTION TO RETRIEVE STARTING STRATEGIES
    time.sleep(0.5)
    getStrategies()

    refresh_freq = 60
    cooldown = 80
    water_released = 0

    with open(database, "r") as file:
        db = json.load(file)

    broker_dict = db["broker"]
    
    publisher = MQTT_publisher(broker_dict["ip"], broker_dict["port"])
    publisher.start()

    while True:
        timestamp = time.time()
        time_start = datetime.fromtimestamp(timestamp+7200)
        time_start = time_start.strftime("%H:%M")

        if timestamp-last_refresh >= refresh_freq:

            last_refresh = time.time()
            refresh()

        if new_strat:

            try:
                with open(database, "r") as file:
                    db = json.load(file)

            except:
                new_strat = True
            else:
                new_strat = False

        for strat in db_test["strategies"]:
            
            strat_time = datetime.strptime(strat["time"], "%H:%M:%S")
            strat_time = strat_time.strftime("%H:%M")

            if str(strat_time) == str(time_start) and strat["active"] == True and timestamp > water_released+cooldown:
                publisher.publish(strat["topic"], strat["water_quantity"])
                water_released = time.time()