#Estoy haciendo una prueba
from MQTT.MyMQTT import *
import time
import json
import requests
'''
TO DO

(OK) Make a GET to the Catalog (< Web Page) to know the strategy, the topics.

(OK) RECEIVES (MQTT subscription) a flag from the Weather Controller that says if the window is open 
(therefore if the Environment manager has to be active or not).

While flag= 1 each 5 seg.

(OK) RECEIVES (MQTT subscription) the real-time measures about Temp, Hum,.. 
from the devices.

(OK) PUBLISH (MQTT PUBLISH), it activate actuators according to the real-time measures and the strategy.
If needed, new real-time parameters to the Devices 
(received Temp = 20 but the strategy says 22 so ⇒ 
publish actuation to Device Temp = 22 and hence the device changes the temp, 
until the next actuation)
'''

class ActivateEnvMgr:
    def __init__(self, clientID, topic,broker,port):
        self.client=MyMQTT(clientID,broker,port,self)
        self.topic=topic
        self.status=None

    def start (self):
        self.client.start()
        self.client.mySubscribe(self.topic)

    def stop (self):
        self.client.stop()
            
    def notify(self,topic,msg):
        #print('funcionando el on')
		# I reuse el name 'msg', it's not really necessary the same name
        msg=json.loads(msg)
        self.status=msg['value']
		# If we are going to use different env_mgr for one clients, I should add thar variable too.
        client=msg['client']
        timestamp=msg['timestamp']
        print(f'The Environment has been set to {self.status} at time {timestamp} by the client {client}')

class DataCollector():
	"""docstring for Sensor"""
	def __init__(self,clientID,broker,port,baseTopic):
		self.clientID=clientID
		self.baseTopic=baseTopic
		self.client=MyMQTT(clientID,broker,port, self)
		self.payload=None
		self.temp=None
		self.hum=None
	def run(self):
		self.client.start()
		print('{} has started'.format(self.clientID))
	def end(self):
		self.client.stop()
		print('{} has stopped'.format(self.clientID))
	def follow(self,topic):
		self.client.mySubscribe(topic)
	def notify(self,topic,msg):
		#Decode the JSON string
		self.payload=json.loads(msg)
		#encoding to JSON objects
		self.temp=self.payload['temp']
		self.hum=self.payload['hum']
		print(json.dumps(self.payload,indent=4))

class CatalogRequest():
	exposed = True
	def __init__(self, uri, headers):
		self.uri = uri
		self.headers = headers
	def GET(self):
		response = requests.get(self.uri, self.headers)
		return response.json()

class ControlActuators:
	# Publish control strategies on raspberry
	
	def __init__(self, clientID, topic,broker,port):
		self.topic=topic
        # SenML format: JSON - double underscore "self.__message" to avoid naming collisions in subclasses
		self.__message={'client': clientID,'value':None, 'timestamp':''}
		{
			'client':self.clientID,
			'timestamp':'',
			'value': [None,None,None]
			}
        # To define MQTT object, sending notification deactivated
		self.client=MyMQTT(clientID,broker,port,self) 
		self.statusToBool={"on":1,"off":0}

	def start (self):
		self.client.start()

	def stop (self):
		self.client.stop()

	def publish(self,value):
		message=self.__message
		message['timestamp']=str(time.time())
		message['value']=self.statusToBool[value]
		self.client.myPublish(self.topic,message)
		print("published")
 
if __name__ == "__main__":
	#Conf MQTT
	conf = json.load(open("settings.json"))
	broker = conf["broker"]
	port = conf["port"]
	uri = conf["uri"]
	headers = conf ["headers"]

	#GET from the catalog
	catalog = CatalogRequest(uri,headers)
	strategies= catalog.GET()
	temp_max = strategies['crops']["temp_min"]
	temp_min = strategies['crops']["temp_max"]
	hum_max= strategies['crops']["hum_max"] 
	hum_min= strategies['crops']["hum_max"]

	userID = "1"
	cropID = "1"
	topic_status = userID+"/"+cropID+"/env_mgr/status"
	topic_measures= userID+"/"+cropID+"/env_mgr/measures"
	done=True

	while done:
		flag=True
		while flag:
			#Activate or deactivate env_mgr from Weather Controller
			status_envMgr = ActivateEnvMgr("OnOffEnvMgr",topic_status,broker,port)
			status_envMgr.start()
			flag= status_envMgr.status

			if flag:
				# To read variables
				measures=DataCollector(userID,broker,port,topic_measures)
				measures.run()
				# Review for what the next line and where to use it (No relation with the project, just learning)
				measures.client.unsubscribe()
				measures.follow(topic_measures)

				temp=measures.temp
				hum=measures.temp
				
				
				# To send control to Rpi
				control_envMgr = ControlActuators("Strt1","IoT/Valen/actuator",broker,port)
				control_envMgr.client.start()

				'''
				Actuador 0, Humidifier:
				Value: 0. Humidifier OFF.
				Value: 1. Decrease temperature, water droplets, humidity are not affected.
				Value: 2. Increase humidity. More abundant water droplet flow
				Actuador 1, Deshumidifier:
				Value: 0. Deshumidifier OFF.
				Value: 1. Deshumidifier ON.
				Actuador 2, Modulo Peltier:
				Value: 0. Modulo OFF.
				Value: 1. Decrease temperature.
				Value: 2. Increase temperature.
				'''
				 
				if temp>temp_max and hum_min>hum>hum_max:
					control_envMgr.publish([1,0,0])
				elif temp>temp_max and hum>hum_max:
					control_envMgr.publish([0,0,1])
				elif temp<temp_min and hum_min>hum>hum_max:
					control_envMgr.publish([0,0,2])
				elif temp<temp_min and hum<hum_min:
					control_envMgr.publish([2,0,2])
				elif temp<temp_min and hum>hum_max:
					control_envMgr.publish([0,1,2])
				elif temp>temp_max and hum<hum_min:
					control_envMgr.publish([2,0,0])
				else:
					print('Error - no condition was met')
				
			else:
				control_envMgr.client.stop()   
				pass
		