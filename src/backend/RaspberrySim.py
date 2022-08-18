import random
import json
from MQTT.MyMQTT import *
import time

class Controller():
    def __init__(self,clientID,rpiID,broker,port):
        self.clientID = clientID
        self.rpiID = rpiID
        self.ttopic = '/'.join([self.clientID,self.rpiID]) + '/measurements'
        self.rtopic = '/'.join([self.clientID,self.rpiID]) + '/actuators'
        self.client = MyMQTT(clientID + rpiID,broker,port,None)
        self.__message = {
			'clientID':self.clientID,
			'rpiID':self.rpiID,
			'Measurements':
				[
					{'n':'temperature','value':'', 'timestamp':'','unit':'C'},
					{'n':'humidity','value':'', 'timestamp':'','unit':'%'}
					]
		    }
        self.flg = True
        
    def readMeasurement(self):
        """
        This method simulates how the raspberry pi take the
        measurements from the DHT sensor.
        """
        
        if self.flg:
            self.__message['Measurements'][0]['value']=random.randint(10,30)
            self.__message['Measurements'][1]['value']=random.randint(50,90)
            self.__message['Measurements'][0]['timestamp']=str(time.time())
            self.__message['Measurements'][1]['timestamp']=str(time.time())
            self.flg = False
        else:
            if self.__message['Measurements'][0]['value'] > 30 or self.__message['Measurements'][1]['value'] > 90:
                self.__message['Measurements'][0]['value']= self.__message['Measurements'][0]['value'] - 1
                self.__message['Measurements'][1]['value']= self.__message['Measurements'][1]['value'] - 1
            elif self.__message['Measurements'][0]['value'] < 10 or self.__message['Measurements'][1]['value'] < 50:
                self.__message['Measurements'][0]['value']= self.__message['Measurements'][0]['value'] + 1
                self.__message['Measurements'][1]['value']= self.__message['Measurements'][1]['value'] + 1
            else:
                self.__message['Measurements'][0]['value']= self.__message['Measurements'][0]['value'] + random.randint(-1,1)
                self.__message['Measurements'][1]['value']= self.__message['Measurements'][1]['value'] + random.randint(-1,1)
            self.__message['Measurements'][0]['timestamp']=str(time.time())
            self.__message['Measurements'][1]['timestamp']=str(time.time())
    
    def setActuators(self):
        """
        This method simulates the different actuators that the
        greenhouse should have, such as: fans, lights, windows, sinks,
        etc.
        """
        None        
      
    def start(self):
        self.client.start()

    def stop(self):
        self.client.stop()
        
    def publish(self):
        message=self.__message
        self.client.myPublish(self.ttopic,message) 
        #print('published: ', message)
        
    def subscribe(self):
        self.client.mySubscribe(self.rtopic)
                        
if __name__ == '__main__':
    conf=json.load(open("src/backend/settings.json"))
    broker=conf["broker"]
    port=conf["port"]
    last_refresh = time.time()
    controller = Controller("Pepoclown","0",broker,port)
    controller.start()
    
    while True:
        
        time_start = time.time()
        
        if time_start-last_refresh >= 2:
            controller.readMeasurement()
            controller.publish()
            last_refresh = time.time()

        
        