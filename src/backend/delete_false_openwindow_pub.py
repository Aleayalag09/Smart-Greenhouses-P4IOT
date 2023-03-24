
import paho.mqtt.client as PahoMQTT
import time
import json

if __name__ == "__main__":
    
    broker = "test.mosquitto.org"
    port = "1883"

    client = PahoMQTT.Client("Window")
    client.connect(broker)
    #window=[0,1,1,0,1,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0]
    temperature=[0,1,1,0,1,0,0,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0]
    humidity=[2,3,2,3,31,31,23,31,411,61,41,1,1,0,4.5,0,0,0,5.60,2.0,0.1]    
    while True:
        for flag in temperature:
            #msg = {"Window" : flag}
            msg ={"Temperature":temperature[flag],"Humidity":humidity[flag]}
            client.publish("Smart_GreenHouses_P4IOT/0/1/0", json.dumps(msg))
            print("Published" + str(msg))
            time.sleep(1)
   
    