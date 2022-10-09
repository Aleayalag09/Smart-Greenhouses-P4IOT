import random
import json
import time
import urllib.request
import paho.mqtt.client as PahoMQTT

class Device():
    def __init__(self, userID, greenHouseID, deviceID, city):
        self.path = '/' + str(userID) + '/' + str(greenHouseID) + '/' + str(deviceID)
        self.measurements = {}
        self.actuators = {}
        self.meteorological_measurements = {}
        self.__api = 'YOUR_API_KEY'
        self.city = city

    def initMeasurements(self,measurements):
        """
        This method initializate the possible measurements
        that a device could have.
        """
        
        temperature_range = [1.0,30.0]
        humidity_range = [0.0,1.0]
        wind_range = [0.0,80.0]
        pressure_range = [1000.0, 1100.0]
        precipitation_range = [0.0,4.0]
        
        for measure in measurements:
            if measure == "Temperature":
                self.measurements[measure] = round(random.uniform(temperature_range[0], temperature_range[1]),2)
            elif measure == "Humidity":
                self.measurements[measure] = round(random.uniform(humidity_range[0], humidity_range[1]),2)
            elif measure == "Wind":
                self.measurements[measure] = round(random.uniform(wind_range[0], wind_range[1]),2)
            elif measure == "Pressure":
                self.measurements[measure] = round(random.uniform(pressure_range[0], pressure_range[1]),2)
            elif measure == "Precipitation":
                self.measurements[measure] = round(random.uniform(precipitation_range[0], precipitation_range[1]),2)
            else:
                print("Bad measurement")
        
        self.environmentMeasurements()
        self.measurements['timestamp'] = time.time()
        
    def initActuators(self,actuators):
        """
        This method initializate the possible actuators
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
        
    def getlocation(self):
        """
        This method takes the name of a place and extract the
        code key of that place.
        """
        search_address = 'http://dataservice.accuweather.com/locations/v1/cities/search?apikey='+self.__api+'&q='+self.city+'&details=true'
        with urllib.request.urlopen(search_address) as search_address:
            data = json.loads(search_address.read().decode())
        location_key = data[0]['Key']
        return location_key
    
    def getWeather(self):
        """
        This method ask the API Accuweather the weather 
        conditions using the key code of the place 
        and get a json of all the measuraments.
        """
        key = self.getlocation()
        weatherUrl= 'http://dataservice.accuweather.com/currentconditions/v1/'+key+'?apikey='+self.__api+'&details=true'
        with urllib.request.urlopen(weatherUrl) as weatherUrl:
            data = json.loads(weatherUrl.read().decode())
        return data
    
    def getMeasurements(self):
        """
        This method extract from a json the measurements that our
        user is interest.
        """
        data = self.getWeather()
        temperature = data[0]['Temperature']['Metric']['Value']
        humidity = data[0]['RelativeHumidity'] / 100
        wind = data[0]["Wind"]["Speed"]['Metric']['Value']
        pressure = data[0]['Pressure']['Metric']['Value']
        precipitation = data[0]['PrecipitationSummary']['Precipitation']['Metric']['Value']
        new_data = {}
        new_data["Temperature"] = temperature
        new_data["Humidity"] = humidity
        new_data["Wind"] = wind
        new_data["Pressure"] = pressure
        new_data["Precipitation"] = precipitation
        return new_data

class DeviceMQTT(Device):
    """
    Device that send measurements and receive actuators values throught MQTT
    """
    def __init__(self, userID, greenHouseID, deviceID, city, serviceIP, port):
        super().__init__(userID, greenHouseID, deviceID, city)
        self._paho_mqtt = PahoMQTT.Client("Smart_Greenhouses_P4IOT_Weather_Controller" + self.path ,True)
        self.serviceIP = serviceIP
        self.port = port
        self.topic = "Smart_GreenHouses_P4IOT" + self.path
        
    def sentMeasurements(self):
        self._paho_mqtt.connect(self.serviceIP, self.port)
        self._paho_mqtt.loop_start()
        self._paho_mqtt.publish(self.topic, json.dumps(self.measurements), 2)
        self._paho_mqtt.loop_stop()
        self._paho_mqtt.disconnect()
        
    def updateActuators(self):
        pass
    
    def simulate(self,measurements,actuators):
        self.initMeasurements(measurements)
        self.initActuators(actuators)
        while True:
            self.sentMeasurements()
            self.updateActuators()
            self.readMeasurement()
            time.sleep(1)
        
    
class DeviceREST(Device):
    def __init__(self, userID, greenHouseID, deviceID, city):
        super().__init__(userID, greenHouseID, deviceID, city)
    pass
    
                        
if __name__ == '__main__':
    measurements = ["Temperature", "Humidity"]
    actuators = ['Fan', 'Humidifier']
    Device1 = DeviceMQTT(0,0,0,"Torino","mqtt.eclipse.org","1883")
    Device1.simulate(measurements,actuators)
    # Device1.initActuators(actuators)
    # print(Device1.measurements)     
    # print(Device1.actuators)
        
        