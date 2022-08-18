from MQTT.MyMQTT import *
import board
import Adafruit_DHT
import time
import json

#version1

class SuscribeControlActuator():
    def __init__(self, clientID, topic, broker, port, pin):
        self.client = MyMQTT(clientID, broker, port, self)
        self.topic = topic
        self.status = None
        self.pin = pin

    def start(self):
        self.client.start()
        self.client.mySubscribe(self.topic)

    def stop(self):
        self.client.stop()

    def notify(self, topic, msg):
        print('hola')
        d = json.loads(msg)
        self.status = d['value']
        client = d['client']
        timestamp = d['timestamp']
        print(
            f'The output {self.pin} has been set to {self.status} at time {timestamp} by the client {client}')

class ReadSensor():
    def __init__(self, pin):
        self.pin = pin
        self.humidity = None
        self.temperature = None
    def read(self):
        # read temperature and humidity from Raspberry
        
        # pin - input assigned to sensor in Raspberry 
        # Input format (e.g. pin= board.D23)
        
        pin = self.pin

        # En caso de que no se leyera
        i=1
        while i < 3: 
            if self.humidity is not None and self.temperature is not None:
                print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
                return humidity,temperature
            else:
                sensor = Adafruit_DHT.DHT11(board.pin)
                humidity = sensor.humidity
                temperature = sensor.temperature
            i += 1
        else:
            return print("The sensor could not be read, try again.")

if __name__ == "__main__":

    conf = json.load(open("settings.json"))
    broker = conf["broker"]
    port = conf["port"]
    test = SuscribeControlActuator("MyFirstbby", "IoT/Valen/actuator", broker, port,24)
    test.start()

    done = False
    
    while not done:
        rd = ReadSensor("D23")
        humidity, temperature = rd.read()
        print("Humidity and Temperature check")
        print("press e to exit")           
        user_input = input()
        if user_input == "e":
            done = True
        else:
            pass
        time.sleep(1)
    test.stop()