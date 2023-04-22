import time
import random
import urllib
import urllib.request
import json

class Actuator(object):
    def __init__(self, id: int, state: bool = False) -> None:
        self.id = id
        self.state = state
        
    def turn_on(self):
        self.state = True
        
    def turn_off(self):
        self.state = False
        
class Sensor(object):
    def __init__(self, id: int) -> None:
        self.id = id

class DHT11(Sensor):
    def __init__(self, id: int) -> None:
        super().__init__(id)
        self.humidity = None
        self.temperature = None
        self.error_humidity =round(random.uniform(-0.04, 0.04),2)
        self.error_temperature = round(random.uniform(-2.0, 2.0),2)
    
    def read_measurements(self, environment):
        environment.update_environment()
        
        self.humidity = round(environment.humidity + self.error_humidity, 2)
        self.temperature = round(environment.temperature + self.error_temperature, 2)
                    
class Window(Actuator):
    def __init__(self, id: int, state: bool) -> None:
        super().__init__(id, state)
        
class Humidifier(Actuator):
    def __init__(self, id: int, state: bool, value = -1) -> None:
        self.value = value
        super().__init__(id, state)
    
    def set_value(self, value):
        self.value = value # -1 for dehumidify 1 for humidify
    
class Pump(Actuator):
    def __init__(self, id: int, state: bool, water_quantity = 0) -> None:
        self.water_quantity = water_quantity
        super().__init__(id, state)
    
    def set_value(self, water_quantity):
        self.water_quantity = water_quantity # Amout of water that was used
        
class Environment(object):
    def __init__(self, actuators, city, temperature = round(random.uniform(0.0, 30.0),2), humidity = round(random.uniform(0.0, 1.0),2)):
        self.temperature = temperature
        self.humidity = humidity
        self.actuators = actuators
        self.last_change = time.time()
        self.city = city
        self.api = 'YOUR_API_KEY'
        self.city_temperature = None
        self.city_humidity = None
        self.flag = 1
        
        # Hyperparameters
        self.window_factor = 3600 # How much time it takes to have the same temperature - humidity if the a window is open
        self.humidifier_humidity_countribuition = 0.001 # Proportion of the humidity that increase by second if a humidifier is on
        self.pump_humidity_countribuition = 0.001 # Proportion of the humidity that increase by second for the total amount of water quantity
        self.humidifier_temperature_countribuition = 0.3 # Proportion of the temperature that increase by second if a humidifier is on

        
    def city_measurements(self):
        search_address = 'http://dataservice.accuweather.com/locations/v1/cities/search?apikey='+self.api+'&q='+self.city+'&details=true'
        with urllib.request.urlopen(search_address) as search_address:
            data = json.loads(search_address.read().decode())
        location_key = data[0]['Key']
        weatherUrl= 'http://dataservice.accuweather.com/currentconditions/v1/'+location_key+'?apikey='+self.api+'&details=true'
        with urllib.request.urlopen(weatherUrl) as weatherUrl:
            data = json.loads(weatherUrl.read().decode())
        temperature = data[0]['Temperature']['Metric']['Value']
        humidity = data[0]['RelativeHumidity'] / 100
        return temperature, humidity
        
        
    def update_environment(self):
        print(f'Environment hum = {self.humidity}, Environment temp = {self.temperature}')
        window_intensity = 0
        humidifier_intensity = 0
        pump_intensity = 0
        actual_time = time.time()
        
        for actuator in self.actuators:
            if actuator.state:
                if isinstance(actuator, Window):
                    window_intensity += 1
                if isinstance(actuator, Humidifier):
                    humidifier_intensity += actuator.value
                if isinstance(actuator, Pump):
                    pump_intensity += actuator.water_quantity
        
        # To not overload the weather API            
        if self.flag:
            self.city_temperature, self.city_humidiy = self.city_measurements()
            self.flag = 0
            
        time_passed = actual_time - self.last_change  
        
        window_humidity = window_intensity*((self.city_humidiy - self.humidity)/self.window_factor)*time_passed + self.humidity
        humidifier_humidity = humidifier_intensity*self.humidifier_humidity_countribuition
        pump_humidity = pump_intensity*self.pump_humidity_countribuition
        
        window_temperature = window_intensity*((self.city_temperature - self.temperature)/self.window_factor)*time_passed + self.temperature
        humidifier_temperature = humidifier_intensity*self.humidifier_temperature_countribuition   
         
        
        
        self.humidity = round(window_humidity + humidifier_humidity + pump_humidity, 2)
        self.temperature = round(window_temperature + humidifier_temperature, 2)
        
        self.last_change = actual_time
                    
class Controller(object):
    def __init__(self, sensors, actuators):
        self.sensors = sensors
        self.actuators = actuators
    
    def turn_on_actuator(self, id):
        for actuator in self.actuators:
            if actuator.id == id:
                actuator.turn_on()
                break
    
    def turn_off_actuator(self,id):
        for actuator in self.actuators:
            if actuator.id == id:
                actuator.turn_off()
                break
    
    def humidify(self,id):
        for actuator in self.actuators:
            if actuator.id == id:
                actuator.set_value(1)
                break
            
    def dehumidify(self,id):
        for actuator in self.actuators:
            if actuator.id == id:
                actuator.set_value(-1)
                break
            
    def water_quantity(self, id, water_quantity):
        for actuator in self.actuators:
            if actuator.id == id:
                actuator.set_water_quantity(water_quantity)
                break
    
    def read_sensor(self, id, environment):
        for sensor in self.sensors:
            if sensor.id == id:
                sensor.read_measurements(environment)
                return sensor.humidity, sensor.temperature
    
if __name__ == "__main__":
    num_windows = 3
    num_pumps = 3
    num_hum = 3
    id = 0
    actuators = []
    for windows in range(num_windows):
        actuators.append(Window(id, True))
        id += 1
    for pump in range(num_pumps):
        actuators.append(Pump(id, True))
        id += 1
    for humidifier in range(num_hum):
        actuators.append(Humidifier(id, True))
        id += 1
        
    sensor_1 = DHT11(1)
    sensors = [sensor_1]
    env_1 = Environment(actuators, "Torino")
    raspberry = Controller(sensors, actuators)    
    
    last_time = time.time()
    timer = 5 # seg
    while True:
        actual_time = time.time()
        if (actual_time - last_time) >= timer:
            humidity, temperature = raspberry.read_sensor(1, env_1)
            print(f'sensor read: humidity = {humidity}, temperature = {temperature}')
            last_time = actual_time