import cherrypy
import requests
import time
from datetime import datetime
import json
import urllib

from MQTT.MyMQTT import *

new_strat = False
database = "src/db/weather_manager_db.json"
resourceCatalogIP = ""
api = 'YOUR_API_KEY'

class RegStrategy(object):
    exposed = True
    
    def POST(self, *path, **queries):
        """
        This function logs a new strategy and updates the state of activity of the greenhouse 
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
            "timestamp": time.time()
        }
        database_dict["strategies"].append(new_strategy)

        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)

    def PUT(self, *path, **queries):
        """
        This function modify the state of activity of a strategy
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
                if split_topic[0] == userID and split_topic[1] == greenHouseID:
                    strat["active"] = active
        
        new_strat = True
        json.dump(database_dict, open(database, "w"), indent=3)

    def DELETE(self, *path, **queries):
        """
        This function delete a strategy
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
        # bn: macro strategy name (weather), e: events (objects), v: value(s) (depends on what we want to set with the strategy),  t: timestamp
        self.__message={'bn': "WeatherStrat", 'e': {'t': None, 'v': None}}

        self.client=MyMQTT("WeatherStrat", broker, port, None)

    def start (self):
        self.client.start()

    def stop (self):
        self.client.stop()

    def publish(self, topic, value):
        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        self.client.myPublish(topic, self.__message)
        
# REGISTER CONTINOUSLY THE MANAGER TO THE RESOURCE CATALOG
def refresh():
    payload = {'ip': "IP of the WeatherManager", 'port': "PORT of the WeatherManager",
               'functions': ["regStrategy"]}
    url = 'URL of the RESOURCE_CATALOG/POST managers'
    
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
    
# BOOT FUNCTION USED TO GET ACTIVE STRATEGIES FROM THE RESOURCE CATALOG
def getStrategies():
    global database

    url = 'URL of the RESOURCE_CATALOG/strategy/manager'
    params = {"strategyType": "weather"}
    strategies = requests.get(url, params=params).json()

    strategy_list = []
    strategy_dict = {
        "topic": "",
        "temperature": -1,
        "humidity": -1,
        "city": "",
        "active": False,
        "timestamp": -1 
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
    
def getlocation(city):
    """
    This method takes the name of a place and extract the
    code key of that place.
    """
    
    global api
    search_address = 'http://dataservice.accuweather.com/locations/v1/cities/search?apikey='+api+'&q='+city+'&details=true'
    with urllib.request.urlopen(search_address) as search_address:
        data = json.loads(search_address.read().decode())
    location_key = data[0]['Key']
    return location_key    
    
def getWeather(city):
    """
    This method ask to the API Accuweather the weather 
    conditions using the key code of the place 
    and get a json of all the measuraments.
    """
    
    global api
    key = getlocation(city)
    weatherUrl= 'http://dataservice.accuweather.com/currentconditions/v1/'+key+'?apikey='+api+'&details=true'
    with urllib.request.urlopen(weatherUrl) as weatherUrl:
        data = json.loads(weatherUrl.read().decode())
    return data

def getMeasurements(city):
    """
    This method extract from a json the measurements that our
    user is interest.
    """
    data = getWeather(city)
    temperature = data[0]['Temperature']['Metric']['Value']
    humidity = data[0]['RelativeHumidity'] / 100
    return temperature, humidity
                                        
     
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
    
    last_refresh = time.time() 
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    refresh()

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    getBroker()

    # BOOT FUNCTION TO RETRIEVE STARTING STRATEGIES
    getStrategies()

    refresh_freq = 60
    
    broker_dict = json.load(open(database, "r"))["broker"]
    strategies = json.load(open(database, "r"))["strategies"]
    
    publisher = MQTT_publisher()
    publisher.__init__(broker_dict["broker"], broker_dict["port"])
    publisher.start()
    
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

        for strat in strategies:
            
            if strat["active"] == True:
                temperature, humidity = getMeasurements(strat['city'])
                if temperature*(percentange) <= strat['temperature'] <= temperature*(2 - percentange) and humidity*(percentange) <= strat['humidity'] <= humidity*(2 - percentange):
                    # Still we have to see how the device connector is going to receive this message
                    publisher.publish(strat["topic"], 'open_window')
    
    
    
    
    