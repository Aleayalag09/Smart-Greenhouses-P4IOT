import cherrypy
import requests
import time
from datetime import datetime
import json
import urllib
import paho.mqtt.client as mqtt

from MQTT.MyMQTT import *

new_strat = False
database = "src/db_examples/weather_manager_db_ex.json"
resCatEndpoints = "http://127.0.0.1:4000"
api = 'YOUR_API_KEY'

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
            city = input['city']
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        
        topic = str(userID)+"/"+str(greenHouseID)+"/weather"
        database_dict = json.load(open(database, "r"))
    
        new_strategy = {
            "topic": topic,
            "temperature": temperature,
            "humidity": humidity,
            "city" : city,
            "active": active,
            "timestamp": time.time(),
            "open": False
        }
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
                split_topic = strat["topic"].split("/")
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
        
        topic = str(userID)+"/"+str(greenHouseID)+"/weather"
        database_dict = json.load(open(database, "r"))

        idx = 0
        for strat in database_dict:
            if strat["topic"] == topic:
                break
            else:
                idx += 1
        database_dict["strategies"].pop(idx)

        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)
    
    
class MQTT_publisher(object):
    def __init__(self, broker, port):
        self.client=mqtt.Client("WeatherManager")
        self.broker = broker
        self.port = port
        
        # bn: macro strategy name (weather), e: events (objects), v: value(s) (depends on what we want to set with the strategy),  t: timestamp
        self.message={'bn': "WeatherStrat", 'e': {'t': None, 'v': None}}


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
        print(f'weatheer manager sent to topic: {topic}, value: {self.message}')
        self.client.loop_start()
    
        
def refresh():
    """
    Registers the Weather Manager to the
    Resource Catalog making a post.
    """

    global database
    db = json.load(open(database, "r"))

    payload = {
        'ip': db["ip"], 
        'port': db["port"],
        'functions': ["regStrategy"]}
    
    url = resCatEndpoints+'/weather_manager'
    
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
    Retrieves all the weather strategies plus the 
    relative city present in the Resource Catalog.
    Called at the BOOT.
    """

    global database

    url = resCatEndpoints+'/strategy/manager'
    params = {"strategyType": "weather"}
    strategies = requests.get(url, params=params).json()

    strategy_list = []
    strategy_dict = {
        "topic": "",
        "temperature": -1,
        "humidity": -1,
        "city": "",
        "active": False,
        "timestamp": -1,
        "open": False
    }
    for strat in strategies:
        try:
            userID = strat['userID']
            greenHouseID = strat["greenHouseID"]
            temperature = strat["strat"]["temperature"]
            humidity = strat["strat"]["humidity"]
            city = strat["city"]
            active = strat["active"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')
        else:
            topic = str(userID)+"/"+str(greenHouseID)+"/weather"
            strategy_dict["topic"] = topic
            strategy_dict["temperature"] = temperature
            strategy_dict["humidity"] = humidity
            strategy_dict["city"] = city
            strategy_dict["active"] = active
            strategy_dict["timestamp"] = time.time()
            strategy_list.append(strategy_dict)

    database_dict = json.load(open(database, "r"))
    database_dict["strategies"] = strategy_list
    json.dump(database_dict, open(database, "w"), indent=3)


def getMeasurements(city):
    """
    This method extract from a json the measurements of
    temperature and humidity of the specified city.
    """
    search_address = 'http://dataservice.accuweather.com/locations/v1/cities/search?apikey='+api+'&q='+city+'&details=true'
    hdr = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    req = urllib.request.Request(search_address, headers=hdr)
    with urllib.request.urlopen(req) as search_address:
        data = json.loads(search_address.read().decode())
    location_key = data[0]['Key']
    weatherUrl= 'http://dataservice.accuweather.com/currentconditions/v1/'+location_key+'?apikey='+api+'&details=true'
    req = urllib.request.Request(weatherUrl,headers=hdr)
    with urllib.request.urlopen(req) as weatherUrl:
        data = json.loads(weatherUrl.read().decode())
    temperature = data[0]['Temperature']['Metric']['Value']
    humidity = data[0]['RelativeHumidity'] / 100
    # temperature, humidity = 20, 0.2
    return temperature, humidity                                       
     
if __name__ == '__main__':
    	
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

    # refresh_freq = 10
    
    # broker_dict = json.load(open(database, "r"))["broker"]
    # strategies = json.load(open(database, "r"))["strategies"]
    
    # publisher = MQTT_publisher(broker_dict["ip"], broker_dict["port"])
    # publisher.start()
    
    # percentange = 0.98
    # last_refresh = time.time()
    
    # while True:
    #     timestamp = time.time()
    #     time_start = datetime.fromtimestamp(timestamp)
    #     time_start = time_start.strftime("%H:%M:%S")

    #     if timestamp-last_refresh >= refresh_freq:

    #         last_refresh = time.time()
    #         # refresh()

    #     if new_strat:
    #         db = json.load(open(database, "r"))
    #         new_strat = False

    #     for strat in strategies:
            
    #         if strat["active"] == True:
    #             temperature, humidity = getMeasurements(strat['city'])

    #             # If the window is open we control if it should be closed
    #             if strat["open"] == True:
    #                 if strat["temperature"] < temperature*(percentange) or strat["temperature"] > temperature*(2 - percentange) or \
    #                 strat['humidity'] < humidity*(percentange) or strat['humidity'] > humidity*(2 - percentange):
    #                     publisher.publish(strat["topic"], 'close')
    #                     strat["open"] = False
    #                     new_strat = True
    #             # If the window is closed we control if it should be opened
    #             else: 
    #                 if temperature*(percentange) <= strat['temperature'] <= temperature*(2 - percentange) and humidity*(percentange) <= strat['humidity'] <= humidity*(2 - percentange):
    #                     # Still we have to see how the device connector is going to receive this message
    #                     publisher.publish(strat["topic"], 'open')
    #                     strat["open"] = True
    #                     new_strat = True

    #     if new_strat == True:
    #         # json.dump(db, open(database, "w"), indent=3)
    #         pass
    
    print(getMeasurements('Turin'))

                
    
    
    
    
    