import time
import random
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
        self.value = {"temperature" : 0, "humidity" : 0}
        self.error_humidity = 0
        self.error_temperature = 0
    
    def read_measurements(self, environment):
        environment.update_environment()
        self.value["humidity"] = round(environment.humidity + self.error_humidity, 2)
        self.value["temperature"] = round(environment.temperature + self.error_temperature, 2)
                    
class Window(Actuator):
    def __init__(self, id: int, state: bool = False) -> None:
        super().__init__(id, state)
        
class Humidifier(Actuator):
    def __init__(self, id: int, state: bool = True, value = 0) -> None:
        self.value = value
        super().__init__(id, state)
    
    def set_value(self, value):
        self.value = value # Humidity set point
        
class AC(Actuator):
    def __init__(self, id: int, state: bool = True, value = 0) -> None:
        self.value = value
        super().__init__(id, state)
    
    def set_value(self, value):
        self.value = value # Temperature set point
    
class Pump(Actuator):
    def __init__(self, id: int, state: bool = True, value = 0) -> None:
        self.value = value
        super().__init__(id, state)
    
    def set_value(self, value):
        self.value = value # Water Quantity
        
class Environment(object):
    def __init__(self, actuators, city, temperature = round(random.uniform(0.0, 30.0),2), humidity = round(random.uniform(0.0, 1.0),2)):
        self.temperature = temperature
        self.humidity = humidity
        self.actuators = actuators
        self.last_change = time.time()
        self.city = city
        self.api = 'YOUR_API_KEY'
        self.city_temperature = 20
        self.city_humidity = 0.5
        self.flag = False
        
        # Hyperparameters
        self.window_factor = 3600 # How much time it takes to have the same temperature - humidity if the a window is open (1 hour)
        self.humidifier_factor = 60 # How much time it takes to have the same humidity as the set point (20 minutes)
        self.ac_factor = 60 # How much time it takes to have the same temperature as the set point (20 minutes)
        self.pump_humidity_factor = 0.001 # Proportion of the humidity that increase by second for the total amount of water quantity
        

        
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
        # print(f'Environment hum = {self.humidity}, Environment temp = {self.temperature}')

        window_intensity = 0

        humidifer_value = 0
        humidifier_intensity = 0

        pump_intensity = 0

        ac_value = 0
        ac_intensity = 0

        actual_time = time.time()
        
        for actuator in self.actuators:
            if actuator.state:
                if isinstance(actuator, Window):
                    window_intensity += 1
                if isinstance(actuator, Humidifier):
                    humidifier_intensity += 1
                    humidifer_value += actuator.value
                if isinstance(actuator, Pump):
                    pump_intensity += actuator.value
                if isinstance(actuator, AC):
                    ac_intensity += 1
                    ac_value += actuator.value
                    
        humidifer_value = humidifer_value/humidifier_intensity
        ac_value = ac_value/ac_intensity
        
        # To not overload the weather API            
        if self.flag:
            self.city_temperature, self.city_humidity = self.city_measurements()
            self.flag = False
            
        time_passed = actual_time - self.last_change
        
        window_humidity = window_intensity*((self.city_humidity - self.humidity)/self.window_factor)*time_passed + self.humidity
        humidifier_humidity = humidifier_intensity*((humidifer_value - window_humidity)/self.humidifier_factor)*time_passed + window_humidity
        pump_humidity = pump_intensity*self.pump_humidity_factor
        
        window_temperature = window_intensity*((self.city_temperature - self.temperature)/self.window_factor)*time_passed + self.temperature
        ac_temperature = ac_intensity*((ac_value - window_temperature)/self.ac_factor)*time_passed + window_temperature
        
        self.humidity = round(humidifier_humidity + pump_humidity, 5)
        self.temperature = round(ac_temperature, 2)
        
        print(f'humidity: {self.humidity}, temperature: {self.temperature}, time passed: {time_passed}')
        
        self.last_change = actual_time
        
        return
                    
class Controller(object):
    def __init__(self, sensors, actuators):
        self.sensors = sensors
        self.actuators = actuators
    
    def turn_on_actuator(self, id):
        for actuator in self.actuators:
            if actuator.id == id:
                actuator.turn_on()
                return f"actuator {actuator.__class__.__name__} : is on"
    
    def turn_off_actuator(self,id):
        for actuator in self.actuators:
            if actuator.id == id:
                actuator.turn_off()
                return f"actuator {actuator.__class__.__name__} : is off"
    
    def set_value(self, id, value):
        for actuator in self.actuators:
            if actuator.id == id:
                if not isinstance(actuator, Window):
                    actuator.set_value(value)
                    return f'{actuator.__class__.__name__} was set to: {actuator.value}'
                else:
                    return "Window can't have set point value"
    
    def read_sensor(self, id, environment):
        for sensor in self.sensors:
            if sensor.id == id:
                sensor.read_measurements(environment)
                return sensor.value
    
if __name__ == "__main__":
    num_windows = 1
    num_pumps = 1
    num_hum = 1
    num_ac = 1
    id = 0
    actuators = []
    for windows in range(num_windows):
        actuators.append(Window(id, False))
        id += 1
    for pump in range(num_pumps):
        actuators.append(Pump(id, True))
        id += 1
    for humidifier in range(num_hum):
        actuators.append(Humidifier(id, True))
        id += 1
    for ac in range(num_ac):
        actuators.append(AC(id, True))
        id += 1
        
    sensor_1 = DHT11(0)
    sensors = [sensor_1]
    env_1 = Environment(actuators, "Torino")
    raspberry = Controller(sensors, actuators)    
    
    last_time = time.time()
    timer = 5 # seg
    while True:
        actual_time = time.time()
        if (actual_time - last_time) >= timer:
            measurement = raspberry.read_sensor(0, env_1)
            print(f'sensor read: humidity = {measurement["humidity"]}, temperature = {measurement["temperature"]}')
            last_time = actual_time