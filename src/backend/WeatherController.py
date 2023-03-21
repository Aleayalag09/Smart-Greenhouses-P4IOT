import json
import urllib.request
import paho.mqtt.client as PahoMQTT
import time

class WeatherController():
    
    def __init__(self):
        self.clientID = "Smart_Greenhouses_P4IOT_Weather_Controller"
        self.catalog = None
        # create an instance of paho.mqtt.client
        self._paho_mqtt = PahoMQTT.Client(self.clientID,True)  
        self.__api = 'XCwVvAuSqXxYqR4WCvqLFk09phMRxtwA'
        self.cities = {}
        self.local_time = None
        self.percentage = 0.98
        
    def getCatalog(self):
        """
        GET THE CATALOG
        """
        catalog = json.loads(urllib.request.urlopen("http://127.0.0.1:8080/user_manager?id=all").read().decode())
        return catalog
        
    def getCities(self):
        """
        GET cities in the catalog
        """
        for user in self.catalog:
            for greenHouse in user['greenHouses']:
                self.cities[greenHouse['city']] = None                
        return self.cities
    
    def getlocation(self,city):
        """
        This method takes the name of a place and extract the
        code key of that place.
        """
        search_address = 'http://dataservice.accuweather.com/locations/v1/cities/search?apikey='+self.__api+'&q='+city+'&details=true'
        with urllib.request.urlopen(search_address) as search_address:
            data = json.loads(search_address.read().decode())
        location_key = data[0]['Key']
        return location_key
    
    def getWeather(self,city):
        """
        This method ask the API Accuweather the weather 
        conditions using the key code of the place 
        and get a json of all the measuraments.
        """
        key = self.getlocation(city)
        weatherUrl= 'http://dataservice.accuweather.com/currentconditions/v1/'+key+'?apikey='+self.__api+'&details=true'
        with urllib.request.urlopen(weatherUrl) as weatherUrl:
            data = json.loads(weatherUrl.read().decode())
        return data
    
    def getMeasurements(self,city):
        """
        This method extract from a json the measurements that our
        user is interest.
        """
        data = self.getWeather(city)
        temperature = data[0]['Temperature']['Metric']['Value']
        humidity = data[0]['RelativeHumidity'] / 100
        new_data = {}
        new_data["Temperature"] = temperature
        new_data["Humidity"] = humidity
        return new_data

    def getMeasurementsCities(self):
        cities = self.cities.keys()
        for city in cities:
            self.cities[city] = self.getMeasurements(city)
        return self.cities
    
    def getLocalTime(self):
        """
        
        """
        
        if time.localtime().tm_hour < 10:
            hour = "0" + str(time.localtime().tm_hour)
        else:
            hour = str(time.localtime().tm_hour)
        
        if time.localtime().tm_min < 10:
            min = "0" + str(time.localtime().tm_min)
        else:
            min = str(time.localtime().tm_min)
            
        if time.localtime().tm_sec < 10:
            sec = "0" + str(time.localtime().tm_sec)
        else:
            sec = str(time.localtime().tm_sec)

        self.local_time = hour + ":" + min + ":" + sec  
        
        return self.local_time
    
    def openWindowMQTT(self,service):
        self._paho_mqtt.connect(service['serviceIP'] , service['port'])
        self._paho_mqtt.loop_start()
        msg = {"Window" : 1}
        self._paho_mqtt.publish(service['topic'] + "actuators", json.dumps(msg), 2)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
        return "The window was opened"
    
    def openWindowREST(self,service):
        data = 1
        urllib.request(service['serviceIP']+":"+service['port']+service['path']+"/window", data=data) # this will make the method "POST"
        return "The window was opened"
    
    def updateWindows(self):
        
        new_catalog = self.getCatalog()
        if self.catalog != new_catalog:
            self.catalog = new_catalog
            self.getCities()

        self.getMeasurementsCities()
        self.getLocalTime()
        
        for user in self.catalog:
            if not user['greenHouses']:
                break
            for greenhouse in user['greenHouses']:
                if not greenhouse['devicesList']:
                    break
                for device in greenhouse['devicesList']:
                    if not device['strategies']:
                        break
                    strategies = sorted(device['strategies'], key=lambda d:d['time'], reverse=True)
                    for strategy in strategies:
                        if strategy['time'] < self.local_time:
                            open_window = True
                            for measurement in device['measureTypes']:
                                if self.cities[greenhouse['city']][measurement] < strategy[measurement]*(1-self.percentage) or self.cities[greenhouse['city']][measurement] > strategy[measurement]*(1+self.percentage):
                                    open_window = False
                            if open_window:
                                for service in device['servicesDetails']:
                                    if service['serviceType'] == "MQTT":
                                        self.openWindowMQTT(service)
                                    elif service['serviceType'] == "REST":
                                        self.openWindowREST(service)
                                    break
                                        
     
if __name__ == '__main__':
    weather_controller = WeatherController()
    weather_controller.updateWindows()
    
    