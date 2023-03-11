import sys
import cherrypy
import requests
import time
import json

from MQTT.MyMQTT import *

new_strat = False
strategies = json.load(open("plants_Irr_strategies.json", "r"))
        

class Strategy(object):
    exposed = True
 
    def POST(self, *path):
        input = json.loads(cherrypy.request.body.read())

        # 3 because: NAME OF THE PLANT, T_START, WATER_QNT corresponds to the first strategy
        if len(input)>3:
            Strategy_II(input)

        else:
            Strategy_I(input)


class MQTT_publisher(object):
    def __init__(self, broker, port):
        # bn: macro strategy name (irrigation), e: events (objects), v: value(s) (depends on what we want to set with the strategy),  t: timestamp
        self.__message={'bn': "IrrigationStrat", 'e': {'t': None, 'v': None}}

        self.client=MyMQTT("IrrigationStrat", broker, port, None)

    def start (self):
        self.client.start()

    def stop (self):
        self.client.stop()

    def publish(self, topic, value):
        self.__message["e"]["t"] = time.time()
        self.__message["e"]["v"] = value

        self.client.myPublish(topic, self.__message)


# IS IT A GLOBAL VARIABLE? DOES I CALL THE SAME INSTANCE OF MQTT_PUBLISHER EITHER IN THE MAIN AND IN THE DIFFERENT STRATEGIES 
publisher = MQTT_publisher()


def Strategy_I(input):
    global new_strat
    new_strat = True

    strategies_dict = json.load(open("plants_Irr_strategies.json", "r"))
    
    # FORMATTED INFO OF THE STRATEGY
    value = {"plant": input["plant"], "t_start": input["t_start"], "water_qnt": input["water_qnt"]}

    # IF IT IS PRESENT A STRATEGY OF ANY TYPE FOR THE SAME PLANT MUST BE FIRSTLY REMOVED
    for strat in strategies_dict["Strategy_II"]:

        if strat["plant"] == input["plant"]:
            strategies_dict["Strategy_II"].remove(strat)

    for strat in strategies_dict["Strategy_I"]:

        if strat["plant"] == input["plant"]:
            strat = value
            return

    strategies_dict["Strategy_I"].append(value)
    json.dump(strategies_dict, open("plants_Irr_strategies.json", "w"), indent=3)


def Strategy_II(input):
    global new_strat
    new_strat = True
    
    strategies_dict = json.load(open("plants_Irr_strategies.json", "r"))
    
    # FORMATTED INFO OF THE STRATEGY
    value = {"plant": input["plant"], "t_start": input["t_start"], "t_stop": input["t_stop"], "water_x_min": input["water_x_min"]}

    # IF IT IS PRESENT A STRATEGY OF ANY TYPE FOR THE SAME PLANT MUST BE FIRSTLY REMOVED
    for strat in strategies_dict["Strategy_I"]:

        if strat["plant"] == input["plant"]:
            strategies_dict["Strategy_II"].remove(strat)

    for strat in strategies_dict["Strategy_II"]:

        if strat["plant"] == input["plant"]:
            strat = value
            return

    strategies_dict["Strategy_II"].append(value)
    json.dump(strategies_dict, open("plants_Irr_strategies.json", "w"), indent=3)


# REGISTER CONTINOUSLY THE STRATEGIES TO THE ?????
def refresh():
    payload = {'ip': "IP of the RESOURCE_CATALOG", 'port': "PORT of the RESOURCE_CATALOG",
               'functions': ["user_manager", "device_manager", "broker"]}
    url = 'URL of the SERVICE_CATALOG (?)'
    
    requests.post(url, payload)


# DIRECT REQUEST TO THE RESOURCE CATALOG? IF WE USE THE SERVICE CATALOG WE NEED TO CONTACT IT BEFORE IN ORDER TO OBTAIN URL AND FUNCTIONS OF THE RESOURCE CATALOG
def broker():
    url = 'URL of the RESOURCE_CATALOG/broker'

    broker = requests.get(url)
    json.dump(broker, open("broker.json", "w"), indent=3)


if __name__=="__main__":

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(Strategy(), '/strategy', conf)

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()


    last_refresh = time.time() 
    # DO WE NEED TO CONTINOUSLY REGISTER THE STRATEGIES TO THE SERVICE/RESOURCE CATALOG?
    refresh()

    # CAN THE MQTT BROKER CHANGE THROUGH TIME? I SUPPOSE NOT IN THIS CASE
    # CONTROL OF THE CORRECT RECEPTION OF THE BROKER?
    broker()
    broker_dict = json.load(open("broker.json", "r"))
    
    publisher.__init__(broker_dict["broker"], broker_dict["port"])
    publisher.start()

    while True:
        time_start = time.time()

        if time_start-last_refresh >= 60:

            last_refresh = time.time()
            refresh()

        if new_strat:

            strategies = json.load(open("plants_Irr_strategies.json", "r"))

        # CYCLE OVER THE STRATEGY OF TYPE I: IF THE TIME OF THE SYSTEM CORRESPONDS WITH THE TYME IN WHICH THE PLANT HAS
        # TO RECEIVE THE WATER THE FUNCTION PUBLISH THE WATER QUANTITY ON A TOPIC SPECIFIC FOR THE PLANT
        for strat in strategies["Strategy_I"]:

            time_now = time.time()
            if time_start==strat["t_start"] or time_now==strat["t_start"] or (time_start<strat["t_start"] and time_now>strat["t_start"]):

                publisher.publish("Greenhouse1/Irr_Strategies/Strategy_I/"+strat["plant"], strat["water_qnt"])

        # CYCLE OVER THE STRATEGY OF TYPE II: IF THE TIME OF THE SYSTEM CORRESPONDS WITH THE TYME IN WHICH THE PLANT HAS
        # TO START RECEIVING THE WATER THE FUNCTION PUBLISH THE WATER X MINUTE NEEDED ON A TOPIC SPECIFIC FOR THE PLANT AND
        # WHEN THE SYSTEM TIME IS EQUAL TO THE STOP_TIME OF THE CONTROL STRATEGY IT PUBLISH A STOP FLAG ON THE (SAME) TOPIC
        for strat in strategies["Strategy_II"]:

            time_now = time.time()
            if time_start==strat["t_start"] or time_now==strat["t_start"] or (time_start<strat["t_start"] and time_now>strat["t_start"]):

                # the device connector will be able to handle different strategies depending on which topic is published anything
                publisher.publish("Greenhouse1/Irr_Strategies/Strategy_II/"+strat["plant"], strat["water_x_minute"])
            
            if time_start==strat["t_stop"] or time_now==strat["t_stop"] or (time_start<strat["t_stop"] and time_now>strat["t_stop"]):

                publisher.publish("Greenhouse1/Irr_Strategies/Strategy_II/"+strat["plant"], "STOP")