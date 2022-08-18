import json
import cherrypy
import time


class UserManager(object):
    exposed = True

    # RETRIEVE THE INFORMATIONS ABOUT THE REGISTERED USERS (query must be equal to "all" or "user_ID")
    def GET(self, *path, **queries):
        users = json.load(open("DATABASE/users.json", "r"))

        if queries=="all":
            return json.dumps(users, indent=3)

        else:
            return json.dumps(users[queries], indent=3)

    # INSERT A NEW USER OR UPDATE THE INFORMATIONS OF AN ALREADY EXISTING USER (if user_ID specified in queries)
    def PUT(self, *path, **queries):
        input = json.loads(cherrypy.request.body.read()) 
        users_dict = json.load(open("DATABASE/users.json", "r"))

        # If we assume that the information about a user can be changed only sending again all the informations 
        # (the entire json with the device description)
        if len(queries)==1:
            new_user = {"id": queries.split("_")[1], "name": input["name"], "surname": input["surname"], "n_rooms": input["n_rooms"], "email_addresses": input["email_addresses"], "timestamp": time.time()}
            users_dict[queries] = new_user
            json.dump(users_dict, open("DATABASE/users.json", "w"), indent=3)
        
        else:
            # Insert the first user 
            if len(users_dict) == 0:
                new_user_ID = "user_0"

            # Insert a new user with an ID = ID_of_the_last_user_in_json + 1
            else:
                n_user = 0
                for user in users_dict:
                    n_user += 1

                    # if user is the last user in the dict creates new_user with ID = user["id"] + 1
                    if n_user == len(users_dict):
                        new_user_ID = user["id"] + 1

            new_user = {"id": new_user_ID, "name": input["name"], "surname": input["surname"], "n_rooms": input["n_rooms"], "email_addresses": input["email_addresses"], "timestamp": time.time()}
            users_dict["user_"+str(new_user_ID)] = new_user
            json.dump(users_dict, open("DATABASE/users.json", "w"), indent=3)

            # initialize the strategies database (json) for the specific user and its rooms
            strategies_dict = json.load(open("DATABASE/strategies.json", "r"))
            strategies_dict[new_user_ID] = {}

            for n_rooms in range(input["n_rooms"]):
                strategies_dict[new_user_ID]["room_"+str(n_rooms)] = {}

                strategies_dict[new_user_ID]["room_"+str(n_rooms)]["Irr_strategy"] = {"active": "False", "ip": "", "port": "", "mqtt_topic_pub": "", "strategy": "", "timestamp": 0} 
                strategies_dict[new_user_ID]["room_"+str(n_rooms)]["Env_strategy"] = {"active": "False", "ip": "", "port": "", "mqtt_topic_pub": "", "strategy": "", "timestamp": 0} 
                strategies_dict[new_user_ID]["room_"+str(n_rooms)]["Wea_strategy"] = {"active": "False", "ip": "", "port": "", "mqtt_topic_pub": "", "strategy": "", "timestamp": 0} 

            json.dump(strategies_dict, open("DATABASE/strategies.json", "w"), indent=3)

            # initialize the devices database (json) for the specific user and its rooms
            devices_dict = json.load(open("DATABASE/devices.json", "r"))
            devices_dict[new_user_ID] = {}

            for n_rooms in range(input["n_rooms"]):
                devices_dict[new_user_ID]["room_"+str(n_rooms)] = {}

            json.dump(devices_dict, open("DATABASE/devices.json", "w"), indent=3)
    
    # DELETE AN USER (with user_ID = queries)
    def DELETE(self, *path, **queries):
        users_dict = json.load(open("DATABASE/users.json", "r"))

        users_dict.pop(queries)

        json.dump(users_dict, open("DATABASE/users.json", "w"), indent=3)


class DeviceManager(object):
    exposed = True

    # RETRIEVE THE INFORMATIONS ABOUT THE REGISTERED DEVICES 
    # (queries[0] = user_ID, queries[1] = room_ID, queries[2] = device_ID)
    def GET(self, *path, **queries):
        devices_dict = json.load(open("DATABASE/devices.json", "r"))

        # Returns all the devices info divided by room and for a specific user
        if len(queries) == 1:
            return json.dumps(devices_dict[queries], indent=3)

        # Returns all the devices info for a specific user and room
        elif len(queries) == 2:
            return json.dumps(devices_dict[queries[0]][queries[1]], indent=3)

        # Returns device info for a specific user, room and device
        elif len(queries) == 3:
            return json.dumps(devices_dict[queries[0]][queries[1]][queries[2]], indent=3)

    # INSERT A NEW DEVICE OR UPDATE THE INFORMATIONS OF AN ALREADY EXISTING DEVICE 
    # (queries[0] = user_ID, queries[1] = room_ID, queries[2] = device_ID (choosen by the user => CONTROL IF IT IS CORRECT?))
    def PUT(self, *path, **queries):
        input = json.loads(cherrypy.request.body.read()) 
        devices_dict = json.load(open("DATABASE/devices.json", "r"))

        new_device = {"active": input["active"], "ip": input["ip"], "port": input["port"], "mqtt_topic_pub": input["mqtt_topic_pub"], "mqtt_topic_sub": input["mqtt_topic_sub"], "resources": input["resources"], "timestamp": time.time()}

        # If we assume that the information about a device can be changed only sending again all the informations 
        # (the entire json with the device description)
        devices_dict[queries[0]][queries[1]][queries[2]] = new_device
        json.dump(devices_dict, open("DATABASE/devices.json", "w"), indent=3)


class StrategiesManager(object):
    exposed = True

    # RETRIEVE THE INFORMATIONS ABOUT THE REGISTERED STRATEGIES (query must be equal to the "user_ID")
    def GET(self, *path, **queries):
        # The user wants all the strategies for each room he manages
        if len(queries) == 1:
            strategies = json.load(open("DATABASE/strategies.json", "r"))[queries]

        return json.dumps(strategies, indent=3)

    # INSERT A NEW STRATEGY OR UPDATE THE INFORMATIONS OF AN ALREADY EXISTING STRATEGY
    # (queries[0] = user_ID, queries[1] = room_ID, queries[2] = strategy_ID (Irr, Env, Wea_strategy))
    def PUT(self, *path, **queries):
        input = json.loads(cherrypy.request.body.read()) 
        strategies_dict = json.load(open("DATABASE/strategies.json", "r"))

        new_strategy = {"active": input["active"], "ip": input["ip"], "port": input["port"], "mqtt_topic_pub": input["mqtt_topic_pub"], "strategy": input["strategy"], "timestamp": time.time()}

        # If we assume that the information about a device can be changed only sending again all the informations 
        # (the entire json with the strategy description)

        # THE JSON FILE HAS A STANDARD FORMAT IN WHICH THE SECTION FOR EACH STRATEGY ARE ALREADY DEFINED WITH DEFAULT VALUES (SEE catalog.json)
        # (Every time a user registers, hence defining the number of rooms, the entries for the strategies are created in catalog.json)
        strategies_dict[queries[0]][queries[1]][queries[2]] = new_strategy
        json.dump(strategies_dict, open("DATABASE/strategies.json", "w"), indent=3)
        return


class BrokerManager(object):
    exposed = True

    # Retrieve IP address and port of the broker in the platform
    def GET(self, *path):
        broker_dict = json.load(open("DATABASE/broker.json", "r"))

        return json.dumps(broker_dict, indent=3)

    # Adds (or updates) IP address and port of the broker as a json string using PUT
    def PUT(self, *path):
        input = json.loads(cherrypy.request.body.read())
        broker = {"ip": input["ip"], "port": input["port"]}

        json.dump(broker, open("DATABASE/broker.json", "w"), indent=3)


class ThingSpeakBridgeManager(object):
    exposed = True

    # Retrieve IP address, port and methods of the ThingSpeak_bridge in the platform
    def GET(self, *path):
        ThingSpeak_bridge_dict = json.load(open("DATABASE/ThingSpeak_bridge.json", "r"))

        return json.dumps(ThingSpeak_bridge_dict, indent=3)

    # Adds (or updates) IP address, port and methods (as a list) of the broker as a json string using PUT
    def PUT(self, *path):
        input = json.loads(cherrypy.request.body.read())
        ThingSpeak_bridge = {"ip": input["ip"], "port": input["port"], "methods": input["methods"], "timestamp": time.time()}

        json.dump(ThingSpeak_bridge, open("DATABASE/ThingSpeak_bridge.json", "w"), indent=3)


class WebPageManager(object):
    exposed = True

    # Retrieve IP address and port of the webPage in the platform
    def GET(self, *path):
        webPage_dict = json.load(open("DATABASE/webPage.json", "r"))

        return json.dumps(webPage_dict, indent=3)

    # Adds (or updates) IP address and port of the webPage as a json string using PUT
    def PUT(self, *path):
        input = json.loads(cherrypy.request.body.read())
        webPage = {"ip": input["ip"], "port": input["port"], "timestamp": time.time()}

        json.dump(webPage, open("DATABASE/webPage.json", "w"), indent=3)


class WeatherAPIManager(object):
    exposed = True

    # Retrieve IP address and port of the weather_API used by the WEATHER_STRATEGIES
    def GET(self, *path):
        weather_API_dict = json.load(open("DATABASE/weather_API.json", "r"))

        return json.dumps(weather_API_dict, indent=3)

    # Adds (or updates) IP address and port of the weather_API as a json string using PUT
    def PUT(self, *path):
        input = json.loads(cherrypy.request.body.read())
        weather_API = {"ip": input["ip"], "port": input["port"], "timestamp": time.time()}

        json.dump(weather_API, open("DATABASE/weather_API.json", "w"), indent=3)



# Function used to remove the devices registered from more than 2 minutes
def remove_oldest_device():
    devices_dict = json.load(open("DATABASE/devices.json", "r"))

    for user in devices_dict:

        for room in user:

            for device in room:

               if time.time()-device["timestamp"]>=9999999999:
                    room.pop("device_"+str(device["id"]))

    json.dump(devices_dict, open("DATABASE/devices.json", "w"), indent=3)


# Function used to remove the strategies registered from more than X minutes
def remove_oldest_strategy():
    strategies_dict = json.load(open("DATABASE/strategies.json", "r"))

    for user in strategies_dict:

        for room in user:

            for strategy in room:

               if time.time()-strategy["timestamp"]>=9999999999:
                    strategy = {"active": "False", "ip": "", "port": "", "mqtt_topic_pub": "", "strategy": "", "timestamp": 0}

    json.dump(strategies_dict, open("DATABASE/strategies.json", "w"), indent=3)


# Function used to remove the ThingSpeak_bridge registered from more than X minutes
def remove_oldest_ThingSpeak_bridge():
    TS_bridge_dict = json.load(open("DATABASE/ThingSpeak_bridge.json", "r"))

    if time.time()-TS_bridge_dict["timestamp"]>=9999999999:
        TS_bridge_dict = {"ip": "", "port": "", "methods": [], "timestamp": 0}

    json.dump(TS_bridge_dict, open("DATABASE/ThingSpeak_bridge.json", "w"), indent=3)


# Function used to remove the webPage registered from more than X minutes
def remove_oldest_webPage():
    webPage_dict = json.load(open("DATABASE/webPage.json", "r"))

    if time.time()-webPage_dict["timestamp"]>=9999999999:
        webPage_dict = {"ip": "", "port": "", "timestamp": 0}

    json.dump(webPage_dict, open("DATABASE/webPage.json", "w"), indent=3)



if __name__=="__main__":

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(UserManager(), '/user_manager', conf)
    cherrypy.tree.mount(DeviceManager(), '/device_manager', conf)
    cherrypy.tree.mount(StrategiesManager(), '/strategies_manager', conf)
    cherrypy.tree.mount(BrokerManager(), '/broker_manager', conf)
    cherrypy.tree.mount(ThingSpeakBridgeManager(), '/thingspeak_bridge_manager', conf)
    cherrypy.tree.mount(WebPageManager(), '/webppage_manager', conf)
    cherrypy.tree.mount(WeatherAPIManager(), '/weatherAPI_manager', conf)


    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()


    last_remove_device = time.time()
    last_remove_strategy = time.time()
    last_remove_TS_bridge = time.time()
    last_remove_webPage = time.time()

    while True:
        # Every 60 seconds it calls the function to remove the oldest device registered
        if time.time()-last_remove_device >= 60:

            last_remove_device = time.time()
            remove_oldest_device()

        # Every X seconds it calls the function to remove the oldest strategy registered
        if time.time()-last_remove_strategy >= 360:

            last_remove_strategy = time.time()
            remove_oldest_strategy()

        # Every X seconds it calls the function to remove the oldest ThingSpeak_bridge registered
        if time.time()-last_remove_TS_bridge >= 360:

            last_remove_TS_bridge = time.time()
            remove_oldest_ThingSpeak_bridge()

        # Every X seconds it calls the function to remove the oldest webPage registered
        if time.time()-last_remove_webPage >= 360:

            last_remove_webPage = time.time()
            remove_oldest_webPage()