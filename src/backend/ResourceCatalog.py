import json
import cherrypy
import time


class UserManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get an especific user or all the users, each user will be call by his id
        """
        users = json.load(open("src/db/users.json", "r"))
        
        try:
            id = queries['id']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        else:
            if queries['id']== "all":
                return json.dumps(users, indent=3)
        
            for user in users:
                if user['id'] == int(id):
                    return json.dumps(user, indent=3)
                
            raise cherrypy.HTTPError(400, 'No user found')
    
    @cherrypy.tools.json_in()
    def POST(self, *path, **queries):
        """
        This function create a new user
        """
        users = json.load(open("src/db/users.json", "r"))
        new_user = {
            "userName": "userName",
            "password": "password",
            "super_User": False,
            "id": users[len(users)-1]['id'] + 1,
            "name": "name",
            "surname": "surname",
            "email_addresses": "email",
            "country": "country",
            "city": "city",
            "greenHouses": [],
            "timestamp": time.time()
        }
        input = cherrypy.request.json
        try:
            new_user["userName"] = input['userName']
            new_user["password"] = input['password']
            new_user["name"] = input['name']
            new_user["surname"] = input['surname']
            new_user["email_addresses"] = input['email_addresses']
            new_user["country"] = input['country']
            new_user["city"] = input['city']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect parameter')
        else:
            users.append(new_user)
            json.dump(users, open("src/db/users.json", "w"), indent=3)
            output=str(type(input))+"<br>"+str(input)
            return output
            

    # INSERT A NEW USER OR UPDATE THE INFORMATIONS OF AN ALREADY EXISTING USER (if user_ID specified in queries)
    @cherrypy.tools.json_in()
    def PUT(self, *path, **queries): 
        """
        This function modify the personal data of the user
        """
        try: 
            id = queries['id']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        input = cherrypy.request.json
        
        users = json.load(open("src/db/users.json", "r"))
        
        keys_to_change = input.keys()
            
        key_not_allowed = ["id","super_User","greenHouses","timestamp"]
        
        keys = list(set(keys_to_change)-set(key_not_allowed))
        
        if not keys:
            raise cherrypy.HTTPError(400, 'Not value to change found')
        
        for user in users:
            if user['id'] == int(id):
                for key in keys:
                    user[key] = type(user[key])(input[key])
                user["timestamp"] = time.time()
                json.dump(users, open("src/db/users.json", "w"), indent=3)
                output = str(type(user))+"<br>"+str(user)
                return output
            
        raise cherrypy.HTTPError(400, 'No user found')
    
    def DELETE(self, *path, **queries):
        """
        This function delete an user by id
        """
        
        try: 
            id = queries['id']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        users = json.load(open("src/db/users.json", "r"))
        
        for idx, user in enumerate(users):
            if user['id'] == int(id):
                output = str(type(user))+"<br>"+str(user)
                users.pop(idx)
                json.dump(users, open("src/db/users.json", "w"), indent=3)
                return output
            
        raise cherrypy.HTTPError(400, 'No user found')
    
class GreenHouseManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get an especific user or all the users, each user will be call by his id
        """
        users = json.load(open("src/db/users.json", "r"))
        
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        else:
            if queries['greenHouseID']== "all":
                for user in users:
                    if user['id'] == int(id):
                        return json.dumps(user['greenHouses'], indent=3)
            
            for user in users:
                if user['id'] == int(id):
                    for greenhouse in user['greenHouses']:
                        if greenhouse['greenHouseID'] == int(greenHouseID):
                            return json.dumps(greenhouse, indent=3)
                
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
                        
    
    @cherrypy.tools.json_in()
    def POST(self, *path, **queries):
        """
        This function create a new user
        """
        users = json.load(open("src/db/users.json", "r"))
        try:
            id = queries['id']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        for user in users:
            if user['id'] == int(id):
                greenHouseID = user['greenHouses'][len(user['greenHouses'])-1]['greenHouseID'] + 1
                break
        
        new_greenhouse = {
            "greenHouseName": "greenHouseName",
            "greenHouseID": greenHouseID,
            "city": "city",
            "devicesList": []
            }
        
        input = cherrypy.request.json
        try:
            new_greenhouse["greenHouseName"] = input['greenHouseName']
            new_greenhouse["city"] = input['city']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect parameter')
        else:
            user['greenHouses'].append(new_greenhouse)
            user["timestamp"] = time.time()
            json.dump(users, open("src/db/users.json", "w"), indent=3)
            output=str(type(input))+"<br>"+str(input)
            return output
            

    # INSERT A NEW USER OR UPDATE THE INFORMATIONS OF AN ALREADY EXISTING USER (if user_ID specified in queries)
    @cherrypy.tools.json_in()
    def PUT(self, *path, **queries): 
        """
        This function modify the personal data of the user
        """
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        input = cherrypy.request.json
        
        users = json.load(open("src/db/users.json", "r"))
        
        keys_to_change = input.keys()
            
        key_not_allowed = ["greenHouseID","devicesList"]
        
        keys = list(set(keys_to_change)-set(key_not_allowed))
        
        if not keys:
            raise cherrypy.HTTPError(400, 'Not value to change found')
        
        for user in users:
            if user['id'] == int(id):
                for greenHouse in user['greenHouses']:
                    if greenHouse['greenHouseID'] == int(greenHouseID):
                        for key in keys:
                            greenHouse[key] = type(greenHouse[key])(input[key])
                user["timestamp"] = time.time()
                json.dump(users, open("src/db/users.json", "w"), indent=3)
                output = str(type(user))+"<br>"+str(user)
                return output
            
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
    
    def DELETE(self, *path, **queries):
        """
        This function delete an user by id
        """
        
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        users = json.load(open("src/db/users.json", "r"))
        
        for user in users:
            if user['id'] == int(id):
                for idx, greenHouse in enumerate(user['greenHouses']):
                    if greenHouse['greenHouseID'] == int(greenHouseID):
                        output = str(type(greenHouse))+"<br>"+str(greenHouse)
                        user['greenHouses'].pop(idx)
                        json.dump(users, open("src/db/users.json", "w"), indent=3)
                        return output
                    
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')

class DeviceManager(object):
    exposed = True

    # RETRIEVE THE INFORMATIONS ABOUT THE REGISTERED DEVICES 
    # (queries[0] = user_ID, queries[1] = room_ID, queries[2] = device_ID)
    def GET(self, *path, **queries):
        devices_dict = json.load(open("src/db/devices.json", "r"))

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
        devices_dict = json.load(open("src/db/devices.json", "r"))

        new_device = {"active": input["active"], "ip": input["ip"], "port": input["port"], "mqtt_topic_pub": input["mqtt_topic_pub"], "mqtt_topic_sub": input["mqtt_topic_sub"], "resources": input["resources"], "timestamp": time.time()}

        # If we assume that the information about a device can be changed only sending again all the informations 
        # (the entire json with the device description)
        devices_dict[queries[0]][queries[1]][queries[2]] = new_device
        json.dump(devices_dict, open("src/db/devices.json", "w"), indent=3)


class StrategiesManager(object):
    exposed = True

    # RETRIEVE THE INFORMATIONS ABOUT THE REGISTERED STRATEGIES (query must be equal to the "user_ID")
    def GET(self, *path, **queries):
        # The user wants all the strategies for each room he manages
        if len(queries) == 1:
            strategies = json.load(open("src/db/strategies.json", "r"))[queries]

        return json.dumps(strategies, indent=3)

    # INSERT A NEW STRATEGY OR UPDATE THE INFORMATIONS OF AN ALREADY EXISTING STRATEGY
    # (queries[0] = user_ID, queries[1] = room_ID, queries[2] = strategy_ID (Irr, Env, Wea_strategy))
    def PUT(self, *path, **queries):
        input = json.loads(cherrypy.request.body.read()) 
        strategies_dict = json.load(open("src/db/strategies.json", "r"))

        new_strategy = {"active": input["active"], "ip": input["ip"], "port": input["port"], "mqtt_topic_pub": input["mqtt_topic_pub"], "strategy": input["strategy"], "timestamp": time.time()}

        # If we assume that the information about a device can be changed only sending again all the informations 
        # (the entire json with the strategy description)

        # THE JSON FILE HAS A STANDARD FORMAT IN WHICH THE SECTION FOR EACH STRATEGY ARE ALREADY DEFINED WITH DEFAULT VALUES (SEE catalog.json)
        # (Every time a user registers, hence defining the number of rooms, the entries for the strategies are created in catalog.json)
        strategies_dict[queries[0]][queries[1]][queries[2]] = new_strategy
        json.dump(strategies_dict, open("src/db/strategies.json", "w"), indent=3)
        return


class BrokerManager(object):
    exposed = True

    # Retrieve IP address and port of the broker in the platform
    def GET(self, *path):
        broker_dict = json.load(open("src/db/broker.json", "r"))

        return json.dumps(broker_dict, indent=3)

    # Adds (or updates) IP address and port of the broker as a json string using PUT
    def PUT(self, *path):
        input = json.loads(cherrypy.request.body.read())
        broker = {"ip": input["ip"], "port": input["port"]}

        json.dump(broker, open("src/db/broker.json", "w"), indent=3)


class ThingSpeakBridgeManager(object):
    exposed = True

    # Retrieve IP address, port and methods of the ThingSpeak_bridge in the platform
    def GET(self, *path):
        ThingSpeak_bridge_dict = json.load(open("src/db/ThingSpeak_bridge.json", "r"))

        return json.dumps(ThingSpeak_bridge_dict, indent=3)

    # Adds (or updates) IP address, port and methods (as a list) of the broker as a json string using PUT
    def PUT(self, *path):
        input = json.loads(cherrypy.request.body.read())
        ThingSpeak_bridge = {"ip": input["ip"], "port": input["port"], "methods": input["methods"], "timestamp": time.time()}

        json.dump(ThingSpeak_bridge, open("src/db/ThingSpeak_bridge.json", "w"), indent=3)


class WebPageManager(object):
    exposed = True

    # Retrieve IP address and port of the webPage in the platform
    def GET(self, *path):
        webPage_dict = json.load(open("src/db/webPage.json", "r"))

        return json.dumps(webPage_dict, indent=3)

    # Adds (or updates) IP address and port of the webPage as a json string using PUT
    def PUT(self, *path):
        input = json.loads(cherrypy.request.body.read())
        webPage = {"ip": input["ip"], "port": input["port"], "timestamp": time.time()}

        json.dump(webPage, open("src/db/webPage.json", "w"), indent=3)


class WeatherAPIManager(object):
    exposed = True

    # Retrieve IP address and port of the weather_API used by the WEATHER_STRATEGIES
    def GET(self, *path):
        weather_API_dict = json.load(open("src/db/weather_API.json", "r"))

        return json.dumps(weather_API_dict, indent=3)

    # Adds (or updates) IP address and port of the weather_API as a json string using PUT
    def PUT(self, *path):
        input = json.loads(cherrypy.request.body.read())
        weather_API = {"ip": input["ip"], "port": input["port"], "timestamp": time.time()}

        json.dump(weather_API, open("src/db/weather_API.json", "w"), indent=3)



# Function used to remove the devices registered from more than 2 minutes
def remove_oldest_device():
    devices_dict = json.load(open("src/db/devices.json", "r"))

    for user in devices_dict:

        for room in user:

            for device in room:

               if time.time()-device["timestamp"]>=9999999999:
                    room.pop("device_"+str(device["id"]))

    json.dump(devices_dict, open("src/db/devices.json", "w"), indent=3)


# Function used to remove the strategies registered from more than X minutes
def remove_oldest_strategy():
    strategies_dict = json.load(open("src/db/strategies.json", "r"))

    for user in strategies_dict:

        for room in user:

            for strategy in room:

               if time.time()-strategy["timestamp"]>=9999999999:
                    strategy = {"active": "False", "ip": "", "port": "", "mqtt_topic_pub": "", "strategy": "", "timestamp": 0}

    json.dump(strategies_dict, open("src/db/strategies.json", "w"), indent=3)


# Function used to remove the ThingSpeak_bridge registered from more than X minutes
def remove_oldest_ThingSpeak_bridge():
    TS_bridge_dict = json.load(open("src/db/ThingSpeak_bridge.json", "r"))

    if time.time()-TS_bridge_dict["timestamp"]>=9999999999:
        TS_bridge_dict = {"ip": "", "port": "", "methods": [], "timestamp": 0}

    json.dump(TS_bridge_dict, open("src/db/ThingSpeak_bridge.json", "w"), indent=3)


# Function used to remove the webPage registered from more than X minutes
def remove_oldest_webPage():
    webPage_dict = json.load(open("src/db/webPage.json", "r"))

    if time.time()-webPage_dict["timestamp"]>=9999999999:
        webPage_dict = {"ip": "", "port": "", "timestamp": 0}

    json.dump(webPage_dict, open("src/db/webPage.json", "w"), indent=3)



if __name__=="__main__":

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(UserManager(), '/user_manager', conf)
    cherrypy.tree.mount(GreenHouseManager(), '/greenhouse_manager', conf)
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