import json
import time
import requests
import cherrypy

from MQTT.MyMQTT import *

database = "src/db/device_connector_db.json"
resourceCatalogIP = ""

class Device():
    def __init__(self, userID, greenHouseID, deviceID, city):
        self.path = '/' + str(userID) + '/' + str(greenHouseID) + '/' + str(deviceID)
        self.measurements = {}
        self.actuators = {}
        self.meteorological_measurements = {}
        self.__api = 'YOUR_API_KEY'
        self.city = city

        
    def initActuators(self,actuators):
        """
        This method initialize the possible actuators
        that a device could have
        """
        for actuator in actuators:
            self.actuators[actuator] = 0  
            
    def readMeasurement(self):
        """
        This method simulates the read of the measurements. 
        """
        actuators = self.actuators.keys()
        measurements = self.measurements.keys()
        if "Window" in actuators and self.actuators['Window'] == 1:
            #Here should call the method environmentMeasurements, however the free trial doesn't allow too many requests.
            for measure in measurements:
                self.measurements[measure] = (self.measurements[measure] + self.meteorological_measurements[measure]) / 2
        else:
            if "Humidifier" in actuators and self.actuators['Humidifier'] == 1:
                if "Humidity" in measurements:
                    self.measurements['Humidity'] = self.measurements["Humidity"] + "x" #insert value
                if "Temperature" in measurements:
                    self.measurements['Temperature'] = self.measurements["Temperature"] + "x" #insert value
            #Keep with each actuator, each variable that affects            
            pass
            
    def updateActuators(self):
        """
        This method change the values of each actuator.
        """
        pass
    
    def environmentMeasurements(self):
        """
        This method get the weather variables of the city.
        """
        self.meteorological_measurements = self.getMeasurements()
    
    def sentMeasurements(self):
        """
        This method will change depending on the communication of the device.
        """
    
    # WHY FROM A JSON?
    def getMeasurements(self):
        """
        This method extract from a json the measurements that our
        user is interest.
        """
        data = self.getWeather()
        temperature = data[0]['Temperature']['Metric']['Value']
        humidity = data[0]['RelativeHumidity'] / 100
        new_data = {}
        new_data["Temperature"] = temperature
        new_data["Humidity"] = humidity
        return new_data

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

    last_refresh = time.time() 
    # WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG
    refresh()

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    getBroker()

    # BOOT FUNCTION TO RETRIEVE STARTING TOPICS
    BOOT_FUNCTION()

    refresh_freq = 60
    
    broker_dict = json.load(open(database, "r"))["broker"]
    
        
        