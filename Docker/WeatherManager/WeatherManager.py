import cherrypy
import requests
import time
from datetime import datetime
import json
import urllib
import paho.mqtt.client as mqtt

new_strat = False
database = "db/weather_manager_db.json"
resCatEndpoints = "http://resource_catalog:8080"
api = 'YOUR_API_KEY'

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
            active = input['active']
            temperature = input['temperature']
            humidity = input['humidity']
            city = input['city']
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        
        topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/weather"
        
        with open(database, "r") as file:
            db = json.load(file)
    
        new_strategy = {
            "topic": topic,
            "temperature": temperature,
            "humidity": humidity,
            "city" : city,
            "active": active,
            "timestamp": time.time(),
            "open": False
        }
        db["strategies"].append(new_strategy)

        with open(database, "w") as file:
            json.dump(db, file, indent=3)
        
        with open(database, "r") as file:
            db_test = json.load(file)

        time.sleep(5)
        new_strat = True
        
        result = {
            "userID": userID,
            "greenHouseID": greenHouseID,
            "temperature": temperature,
            "humidity": humidity,
            "city" : city,
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
        global db_test
        input = json.loads(cherrypy.request.body.read())
        
        with open(database, "r") as file:
            db = json.load(file)

        try:
            userID = input['userID']
            greenHouseID = input['greenHouseID']
            active = input['active']
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')
        else:
            for strat in db["strategies"]:
                split_topic = strat["topic"].split("/")
                if int(split_topic[1]) == int(userID) and int(split_topic[2]) == int(greenHouseID):
                    strat["active"] = active
        
        with open(database, "w") as file:
            json.dump(db, file, indent=3)

        with open(database, "r") as file:
            db_test = json.load(file)

        time.sleep(5)
        new_strat = True
        
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
        global db_test

        try:
            userID = queries['userID']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/weather"
        
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

            with open(database, "w") as file:
                json.dump(db, file, indent=3)

            with open(database, "r") as file:
                db_test = json.load(file)

            time.sleep(5)
            new_strat = True
            
            result = {
                "userID": userID,
                "greenHouseID": greenHouseID,
                "timestamp": time.time()
            }
            return result
        except:
            print("No strategy registered")
    
    
class MQTT_publisher(object):
    def __init__(self, broker, port):
        
        with open(database, "r") as file:
            db = json.load(file)
        
        self.client = mqtt.Client("WeatherManager_"+str(db["ID"]))
        self.broker = broker
        self.port = port
        self.topic = None

        # bn: macro strategy name (irrigation), e: events (objects), v: value(s) (depends on what we want to set with the strategy),  t: timestamp
        self.__message={'bn': "weather", 'e': {'t': None, 'v': None}}

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
    Registers the Weather Manager to the
    Resource Catalog making a post.
    """

    global database
    
    with open(database, "r") as file:
        db = json.load(file)

    payload = {
        'ip': db["ip"], 
        'port': db["port"],
        'functions': [db["function"]]}
    
    url = resCatEndpoints+'/weather_manager'
    
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
    Retrieves all the weather strategies plus the 
    relative city present in the Resource Catalog.
    Called at the BOOT.
    """

    global database
    global new_strat
    global db_test

    url = resCatEndpoints+'/strategy/manager'
    params = {"strategyType": "weather"}
    strategies = requests.get(url, params=params).json()

    strategy_list = []
    for strat in strategies:
        try:
            userID = strat['userID']
            greenHouseID = strat["greenHouseID"]
            temperature = strat["strat"]["temperature"]
            humidity = strat["strat"]["humidity"]
            city = strat["city"]
            active = strat["active"]
        except:
            print('Wrong parameters')
        else:
            topic = "IoT_project_29/"+str(userID)+"/"+str(greenHouseID)+"/weather"
            strategy_list.append({
                                    "topic": topic,
                                    "temperature": temperature,
                                    "humidity": humidity,
                                    "city": city,
                                    "active": active,
                                    "timestamp": time.time(),
                                    "open": False
                                })

    with open(database, "r") as file:
        db = json.load(file)

    db["strategies"] = strategy_list
    
    with open(database, "w") as file:
        json.dump(db, file, indent=3)

    with open(database, "r") as file:
        db_test = json.load(file)

    time.sleep(5)
    new_strat = True
    

def getlocation(city):
    """
    This method takes the name of a place and 
    extract the code key of that place.
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
    time.sleep(1)
    weatherUrl= 'http://dataservice.accuweather.com/currentconditions/v1/'+key+'?apikey='+api+'&details=true'
    with urllib.request.urlopen(weatherUrl) as weatherUrl:
        data = json.loads(weatherUrl.read().decode())
    return data

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
    
    time.sleep(9)
    	
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
    
    with open(database, "r") as file:
        db = json.load(file)

    broker_dict = db["broker"]
    
    publisher = MQTT_publisher(broker_dict["ip"], broker_dict["port"])
    publisher.start()
    
    percentange = 0.95
    
    flag_API = True
    time_flag = time.time()
    
    while True:
        timestamp = time.time()
        time_start = datetime.fromtimestamp(timestamp)
        time_start = time_start.strftime("%H:%M:%S")
        
        if time.time() - time_flag >= 300:
            flag_API = True

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
            
            if strat["active"] == True:
                if flag_API:
                    temperature, humidity = getMeasurements(strat['city']) 
                    flag_API = False
                    time_flag = time.time()

                # If the window is open we control if it should be closed
                if strat["open"] == True:
                    if strat["temperature"] < temperature*(percentange) or strat["temperature"] > temperature*(2 - percentange) or \
                    strat['humidity'] < humidity*(percentange) or strat['humidity'] > humidity*(2 - percentange):
                        publisher.publish(strat["topic"], 'close')
                        
                        split_topic = strat["topic"].split("/")

                        payload = {
                            'userID': split_topic[1], 
                            'greenHouseID': split_topic[2],
                            'state': "CLOSE"
                        }
                        
                        url = resCatEndpoints+"/window_state"
                        requests.post(url, json.dumps(payload))

                        strat["open"] = False
                        new_strat = True
                        # time.sleep(0.5)
                # If the window is closed we control if it should be opened
                else: 
                    if (temperature*(percentange) <= strat['temperature'] and strat['temperature'] <= temperature*(2 - percentange)) and (humidity*(percentange) <= strat['humidity'] and strat['humidity'] <= humidity*(2 - percentange)):
                    # if float(temperature) == float(strat["temperature"]) and float(humidity) == float(strat["humidity"]):
                        publisher.publish(strat["topic"], 'open')
                        
                        split_topic = strat["topic"].split("/")

                        payload = {
                            'userID': split_topic[1], 
                            'greenHouseID': split_topic[2],
                            'state': "OPEN"
                        }
                        
                        url = resCatEndpoints+"/window_state"
                        requests.post(url, json.dumps(payload))
                        
                        strat["open"] = True
                        new_strat = True
                        # time.sleep(0.5)

        if new_strat == True:
            # time.sleep(1)
            with open(database, "w") as file:
                json.dump(db_test, file, indent=3)

                
    
    
    
    
    