import json
import cherrypy
import time
import requests


class User(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get a specific user or all the users, each user will be called by his id
        """
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        
        try:
            id = queries['id']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        else:
            if queries['id']== "all":
                return json.dumps(users, indent=3)
            try:
                for user in users:
                    if user['id'] == int(id):
                        return json.dumps(user, indent=3)
            except:
                raise cherrypy.HTTPError(400, 'No user found')
            
        raise cherrypy.HTTPError(400, 'No user found')
    
    def POST(self, *path, **queries):
        """
        This function create a new user
        """
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        new_user = {
            "userName": "userName",
            "password": "password",
            "super_User": False,
            "id": -1,
            "name": "name",
            "surname": "surname",
            "email_addresses": "email",
            "country": "country",
            "city": "city",
            "MQTTBaseTopic": "baseTopic/",
            "greenHouses": [],
            "timestamp": time.time()
        }
        input = json.loads(cherrypy.request.body.read())
        try:
            new_user["userName"] = input['userName']
            new_user["password"] = input['password']
            new_user["id"] = input["id"]
            new_user["name"] = input['name']
            new_user["surname"] = input['surname']
            new_user["email_addresses"] = input['email_addresses']
            new_user["country"] = input['country']
            new_user["city"] = input['city']
            new_user["MQTTBaseTopic"] = input['MQTTBaseTopic']+"/"
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameter')
        else:
            users.append(new_user)
            db["users"] = users
            json.dump(db, open("src/db/catalog.json", "w"), indent=3)
            output=str(type(input))+"<br>"+str(input)
            return output
            
    def PUT(self, *path, **queries): 
        """
        This function modify the personal data of the user
        """
        try: 
            id = queries['id']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        input = json.loads(cherrypy.request.body.read())
        
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        
        keys_to_change = input.keys()
        key_not_allowed = ["id","super_User","greenHouses","timestamp"]
        keys = list(set(keys_to_change)-set(key_not_allowed))
        
        if not keys:
            raise cherrypy.HTTPError(400, 'No value to change found')  
        try:
            for user in users:
                if user['id'] == int(id):
                    for key in keys:
                        try:
                            user[key] = type(user[key])(input[key])
                        except:
                            raise cherrypy.HTTPError(400, 'No valid key')
                    user["timestamp"] = time.time()
                    db["users"] = users
                    json.dump(db, open("src/db/catalog.json", "w"), indent=3)
                    output = str(type(user))+"<br>"+str(user)
                    return output
        except:
            raise cherrypy.HTTPError(400, 'No user found')
        
        raise cherrypy.HTTPError(400, 'No user found')
    
    def DELETE(self, *path, **queries):
        """
        This function delete an user by id
        """
        
        try: 
            id = queries['id']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        
        for idx, user in enumerate(users):
            if user['id'] == int(id):
                users.pop(idx)
                db["users"] = users
                json.dump(db, open("src/db/catalog.json", "w"), indent=3)

                for i in range(len(user["greenHouses"])):
                    delete_manager_dict = {
                        'userID': id, 
                        'greenHouseID': i
                    }
                    delete_to_manager_and_adaptor("irrigation", delete_manager_dict)
                    delete_to_manager_and_adaptor("environment", delete_manager_dict)
                    delete_to_manager_and_adaptor("weather", delete_manager_dict)

                output = str(type(user))+"<br>"+str(user)
                return output
            
        raise cherrypy.HTTPError(400, 'No user found')
    

class GreenHouse(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get a specific greenhouse or all the greenhouses from an user.
        """
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        else:
            try:
                if queries['greenHouseID']== "all":
                    for user in users:
                        if user['id'] == int(id):
                            return json.dumps(user['greenHouses'], indent=3)
                
                for user in users:
                    if user['id'] == int(id):
                        for greenhouse in user['greenHouses']:
                            if greenhouse['greenHouseID'] == int(greenHouseID):
                                return json.dumps(greenhouse, indent=3)
            except:
                raise cherrypy.HTTPError(400, 'No user or greenhouse found')
            
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
                        
    def POST(self, *path, **queries):
        """
        This function create a new greenhouse
        """
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        try:
            id = int(queries['id'])
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')

        for user in users:
            if user['id'] == int(id):

                strat_dict = {
                    "strat": [],
                    "active": False,
                    "timestamp": -1
                }
                
                new_greenhouse = {
                    "greenHouseName": "greenHouseName",
                    "greenHouseID": -1,
                    "city": "city",
                    "deviceConnectors": [],
                    "strategies": {"irrigation": strat_dict, "environment": strat_dict, "weather": strat_dict}
                }
                
                input = json.loads(cherrypy.request.body.read())
                try:
                    new_greenhouse["greenHouseName"] = input['greenHouseName']
                    new_greenhouse["city"] = input['city']
                    new_greenhouse["greenHouseID"] = input["greenHouseID"]
                except:
                    raise cherrypy.HTTPError(400, 'Wrong parameter')
                else:
                    user['greenHouses'].append(new_greenhouse)
                    user["timestamp"] = time.time()
                    db["users"] = users
                    json.dump(db, open("src/db/catalog.json", "w"), indent=3)
                    output=str(type(input))+"<br>"+str(input)
                    return output
        
        raise cherrypy.HTTPError(400, 'No user found')
            
    def PUT(self, *path, **queries): 
        """
        This function modify the information of the greenhouse
        """
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        input = json.loads(cherrypy.request.body.read())
        
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        
        keys_to_change = input.keys()
        key_not_allowed = ["greenHouseID","deviceConnectors", "strategies"]  
        keys = list(set(keys_to_change)-set(key_not_allowed))
        
        if not keys:
            raise cherrypy.HTTPError(400, 'No value to change found')
        try:
            for user in users:
                if user['id'] == int(id):
                    for greenHouse in user['greenHouses']:
                        if greenHouse['greenHouseID'] == int(greenHouseID):
                            for key in keys:
                                try:
                                    greenHouse[key] = type(greenHouse[key])(input[key])
                                except:
                                    raise cherrypy.HTTPError(400, 'No valid key')
                            user["timestamp"] = time.time()
                            db["users"] = users
                            json.dump(db, open("src/db/catalog.json", "w"), indent=3)
                            output = str(type(user))+"<br>"+str(user)
                            return output
        except:  
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
        
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
    
    def DELETE(self, *path, **queries):
        """
        This function delete a greenhouse
        """
        
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        try: 
            for user in users:
                if user['id'] == int(id):
                    for idx, greenHouse in enumerate(user['greenHouses']):
                        if greenHouse['greenHouseID'] == int(greenHouseID):
                            user['greenHouses'].pop(idx)
                            user["timestamp"] = time.time()
                            db["users"] = users
                            json.dump(db, open("src/db/catalog.json", "w"), indent=3)

                            delete_manager_dict = {
                                'userID': id, 
                                'greenHouseID': greenHouseID
                            }
                            delete_to_manager_and_adaptor("irrigation", delete_manager_dict)
                            delete_to_manager_and_adaptor("environment", delete_manager_dict)
                            delete_to_manager_and_adaptor("weather", delete_manager_dict)

                            output = str(type(greenHouse))+"<br>"+str(greenHouse)
                            return output
        except:     
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
        
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')


# If path[0] is equal to manager it means that it is the boot request of a manager, therefore it needs all the strategies present
class Strategy(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get a specific strategy (Irrigation, Environment, Weather) or all the strategies for a specific user and greenhouse.
        """
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            strategyType = queries['strategyType']
        except:
            try:
                if path[0] != "manager":
                    raise Exception
                strategyType = queries['strategyType']
                if strategyType != "irrigation" and strategyType != "environment" and strategyType != "weather":
                    raise Exception
            except:
                pass
            else:
                strategy_list = []
                strategy_dict = {
                    "userID": -1,
                    "greenHouseID": -1,
                    "strat": {},
                    "active": False
                }
                try:
                    for user in users:
                        for greenhouse in user['greenHouses']:
                            
                            if strategyType == "irrigation":
                                for strat in greenhouse["strategies"]["irrigation"]["strat"]:
                                    strategy_dict["userID"] = user["id"]
                                    strategy_dict["greenHouseID"] = greenhouse["greenHouseID"]
                                    strategy_dict["strat"] = strat
                                    strategy_dict["active"] = greenhouse["strategies"]["irrigation"]["active"]
                                    strategy_list.append(strategy_dict)
                            elif strategyType == "weather":
                                strategy_dict = {
                                    "userID": -1,
                                    "greenHouseID": -1,
                                    "strat": {},
                                    "city": "",
                                    "active": False
                                }
                                strategy_dict["userID"] = user["id"]
                                strategy_dict["greenHouseID"] = greenhouse["greenHouseID"]
                                strategy_dict["strat"] = greenhouse["strategies"]["weather"]["strat"]
                                # Must be added the information of the city that is not present inside the strategy in the catalog db 
                                strategy_dict["city"] = user["city"]
                                strategy_dict["active"] = greenhouse["strategies"]["weather"]["active"]
                                strategy_list.append(strategy_dict)
                            else:
                                strategy_dict["userID"] = user["id"]
                                strategy_dict["greenHouseID"] = greenhouse["greenHouseID"]
                                strategy_dict["strat"] = greenhouse["strategies"][strategyType]["strat"]
                                strategy_dict["active"] = greenhouse["strategies"][strategyType]["active"]
                                strategy_list.append(strategy_dict)

                    return json.dumps(strategy_list, indent=3)
                except:
                    raise cherrypy.HTTPError(400, 'No user or greenhouse found')

            raise cherrypy.HTTPError(400, 'Bad request')
        
        else:
            try:
                if queries['strategyType']== "all":
                    for user in users:
                        if user['id'] == int(id):
                            for greenhouse in user['greenHouses']:
                                if greenhouse['greenHouseID'] == int(greenHouseID):
                                    return json.dumps(greenhouse['strategies'], indent=3)
                            
                for user in users:
                    if user['id'] == int(id):
                        for greenhouse in user['greenHouses']:
                            if greenhouse['greenHouseID'] == int(greenHouseID):
                                try:
                                    strategy = greenhouse['strategies'][strategyType]
                                except:
                                    raise cherrypy.HTTPError(400, 'Wrong strategy type')
                                else:
                                    return json.dumps(strategy, indent=3)
            except:
                raise cherrypy.HTTPError(400, 'No user or greenhouse found')
            
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
                        
    def POST(self, *path, **queries):
        """
        This function create a new strategy (if you want to update one strategy you must first delete it and then create a new one)
        """
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            strategyType = queries['strategyType']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        input = json.loads(cherrypy.request.body.read())

        if strategyType == "irrigation":
            try:
                for user in users:
                    if user['id'] == int(id):
                        for greenhouse in user['greenHouses']:
                            if greenhouse['greenHouseID'] == int(greenHouseID):
                                if len(greenhouse['strategies']['irrigation']['strat']) == 0:
                                    strategyID = 0
                                else:                           
                                    strategyID = int(greenhouse['strategies']['irrigation']['strat'][len(greenhouse['strategies']['irrigation']['strat'])-1]['id']) + 1

                                try: 
                                    stime = input["time"]
                                    water_quantity = input["water_quantity"]
                                    activeStrat = input["active"]
                                except:
                                    raise cherrypy.HTTPError(400, 'Wrong parameters')
                                else:
                                    new_strat = {
                                        "id": strategyID,
                                        "time" : stime,
                                        "water_quantity": water_quantity,
                                        "active" : activeStrat
                                    }

                                    greenhouse['strategies']['irrigation']['strat'].append(new_strat)

                                    # If the new strategy is set to be active then the Irrigation strategy as a whole turn active to (if other single strategies are off remains off)

                                    if activeStrat:
                                        greenhouse['strategies']['irrigation']['active'] = activeStrat
                                    activeIrr = greenhouse['strategies']['irrigation']['active']
                                    greenhouse['strategies']['irrigation']['timestamp'] = time.time()

                                    user['timestamp'] = time.time()
                                    db["users"] = users
                                    json.dump(db, open("src/db/catalog.json", "w"), indent=3)

                                    post_manager_dict = {
                                        'userID': id, 
                                        'greenHouseID': greenHouseID,
                                        'active': activeIrr, 
                                        'stratID': strategyID,
                                        'time': stime, 
                                        'water_quantity': water_quantity,
                                        'activeStrat': activeStrat
                                    }
                                    post_to_manager_and_adaptor("irrigation", post_manager_dict)

                                    output=str(type(input))+"<br>"+str(input)
                                    return output
            except:
                raise cherrypy.HTTPError(400, 'No user or greenhouse found')

        elif strategyType == "environment" or strategyType == "weather": 
            try:  
                for user in users:
                    if user['id'] == int(id):
                        for greenhouse in user['greenHouses']:
                            if greenhouse['greenHouseID'] == int(greenHouseID):

                                try:
                                    temperature = input["temperature"]
                                    humidity = input["humidity"]
                                    active = input["input"]
                                except:
                                    raise cherrypy.HTTPError(400, 'Wrong parameters')
                                else:
                                    new_strat = {
                                        "temperature": temperature,
                                        "humidity" : humidity
                                    }

                                    greenhouse['strategies'][strategyType]["strat"] = new_strat
                                    greenhouse['strategies'][strategyType]['active'] = active
                                    greenhouse['strategies'][strategyType]['timestamp'] = time.time()
                                    post_manager_dict = {
                                        'userID': id, 
                                        'greenHouseID': greenHouseID,
                                        'active': active,
                                        "temperature": temperature,
                                        "humidity": humidity
                                    }
                                
                                user['timestamp'] = time.time()
                                db["users"] = users
                                json.dump(db, open("src/db/catalog.json", "w"), indent=3)

                                post_to_manager_and_adaptor(strategyType, post_manager_dict)

                                output=str(type(input))+"<br>"+str(input)
                                return output
            except: 
                raise cherrypy.HTTPError(400, 'No user or greenhouse found')            
        else:
            raise cherrypy.HTTPError(400, 'Wrong strategy type')
        
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')

    def PUT(self, *path, **queries): 
        """
        This function modify the state of activity of a strategy
        """
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            strategyType = queries['strategyType']
            active = queries['active']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]

        try:
            for user in users:
                if user['id'] == int(id):
                    for greenhouse in user['greenHouses']:
                        if greenhouse['greenHouseID'] == int(greenHouseID):
                            
                            if strategyType == "irrigation":
                                flagIrr = False
                                try:
                                    input = json.loads(cherrypy.request.body.read())
                                    strategyID = int(input["strategyID"])
                                    activeStrat = input["activeStrat"]
                                except:
                                    pass
                                else:
                                    greenhouse['strategies']['irrigation']["strat"][strategyID]['active'] = activeStrat
                                    flagIrr = True
    
                            try:
                                greenhouse['strategies'][strategyType]["active"] = active
                                greenhouse['strategies'][strategyType]["timestamp"] = time.time()
                            except:
                                raise cherrypy.HTTPError(400, 'Wrong strategy type')
                            else:
                                user["timestamp"] = time.time()
                                db["users"] = users
                                json.dump(db, open("src/db/catalog.json", "w"), indent=3)

                                if flagIrr:
                                    put_manager_dict = {
                                        'userID': id, 
                                        'greenHouseID': greenHouseID,
                                        'active': active,
                                        'stratID': strategyID,
                                        'activeStrat': activeStrat
                                    }
                                else:
                                    put_manager_dict = {
                                        'userID': id, 
                                        'greenHouseID': greenHouseID,
                                        'active': active
                                    }
                                put_to_manager(strategyType, put_manager_dict)

                                output = str(type(user))+"<br>"+str(user)
                                return output
        except:
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
                
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
    
    # For the irrigation strategies you can specify the strategy ID
    def DELETE(self, *path, **queries):
        """
        This function delete a strategy (if you want to modify one you must delete it before and then create a new one)
        """
        
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            strategyType = queries['strategyType']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]

        strat_dict = {
                "strat": [],
                "active": False,
                "timestamp": time.time()
            }
        try:
            for user in users:
                if user['id'] == int(id):
                    for greenhouse in user['greenHouses']:
                        if greenhouse['greenHouseID'] == int(greenHouseID):
                            
                            if strategyType == "irrigation":
                                try:
                                    strategyID = queries["strategyID"]
                                except:
                                    greenhouse['strategies']['irrigation'] = strat_dict
                                    user["timestamp"] = time.time()
                                    db["users"] = users
                                    json.dump(db, open("src/db/catalog.json", "w"), indent=3)

                                    delete_manager_dict = {
                                        'userID': id, 
                                        'greenHouseID': greenHouseID
                                    }
                                    delete_to_manager_and_adaptor("irrigation", delete_manager_dict)

                                    output = str(type(user))+"<br>"+str(user)
                                    return output
                                else:
                                    try:
                                        greenhouse['strategies']['irrigation']['strat'][strategyID]
                                    except:
                                        raise cherrypy.HTTPError(400, 'Strategy not found')
                                    else:
                                        for i in range(len(greenhouse['strategies']['irrigation']['strat'])):
                                            if i>strategyID:
                                                index = int(greenhouse['strategies']['irrigation']['strat'][i]["id"]) - 1
                                                greenhouse['strategies']['irrigation']['strat'][i]["id"] = index

                                        greenhouse['strategies']['irrigation']['strat'].pop(strategyID)
                                        greenhouse['strategies']['irrigation']["timestamp"] = time.time()
                                        user["timestamp"] = time.time()
                                        db["users"] = users
                                        json.dump(db, open("src/db/catalog.json", "w"), indent=3)

                                        delete_manager_dict = {
                                            'userID': id, 
                                            'greenHouseID': greenHouseID,
                                            'stratID': strategyID
                                        }
                                        delete_to_manager_and_adaptor("irrigation", delete_manager_dict)

                                        output = str(type(user))+"<br>"+str(user)
                                        return output
                            else:
                                try:
                                    greenhouse['strategies'][strategyType] = strat_dict
                                except:
                                    raise cherrypy.HTTPError(400, 'Wrong strategy type')
                                else:
                                    user["timestamp"] = time.time()
                                    db["users"] = users
                                    json.dump(db, open("src/db/catalog.json", "w"), indent=3)

                                    delete_manager_dict = {
                                        'userID': id, 
                                        'greenHouseID': greenHouseID
                                    }
                                    delete_to_manager_and_adaptor(strategyType, delete_manager_dict)

                                    output = str(type(user))+"<br>"+str(user)
                                    return output
        except:
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
                    
        raise cherrypy.HTTPError(400, 'No user, greenhouse or strategy found')
    

class DeviceConnectors(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get the endpoints of the device connectors of a greenhouse.
        """
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request') 
         
        try:  
            for user in users:
                if user['id'] == int(id):
                    for greenhouse in user['greenHouses']:
                        if greenhouse['greenHouseID'] == int(greenHouseID):
                            return json.dumps(greenhouse["deviceConnectors"], indent=3)
        except:
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
                                      
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
    
    def POST(self, *path, **queries):
        """
        This function updates and adds to the greenhouses the device connectors
        """
        db = json.load(open("src/db/catalog.json", "r"))
        input = json.loads(cherrypy.request.body.read())

        try:
            userID = input["userID"]
            greenHouseID = input["greenHouseID"]
            ip = input["ip"]
            port = input["port"]
            sensors = input["devices"]["sensors"]
            actuators = input["devices"]["actuators"]
            functions = input["functions"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong input')

        dev_conn_dict = {
            "ip": ip,
            "port": port,
            "devices": {
                "sensors": sensors,
                "actuators": actuators
            },
            "functions": functions,
            "timestamp": time.time()
        }
        try:
            for user in db["users"]:
                if user["id"] == userID:
                    for greenhouse in user["greenHouses"]:
                        if greenhouse["greenHouseID"] == greenHouseID:
                            if len(greenhouse["deviceConnectors"]) == 0:
                                greenhouse["deviceConnectors"].append(dev_conn_dict)
                            else:
                                update = False
                                for dev_conn in greenhouse["deviceConnectors"]:
                                    if dev_conn["ip"] == ip and dev_conn["port"] == port:
                                        dev_conn["device"]["sensors"] = sensors
                                        dev_conn["device"]["actuators"] = actuators
                                        dev_conn["functions"] = functions
                                        dev_conn["timestamp"] = time.time()
                                        update = True
                                
                                if update == False:
                                    greenhouse["deviceConnectors"].append(dev_conn_dict)
                            
                            json.dump(db, open("src/db/catalog.json", "w"), indent=3)
                            output=str(type(input))+"<br>"+str(input)
                            return output
        except:
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
        
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')


class Broker(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get the broker endpoints and timestamp
        """
        db = json.load(open("src/db/catalog.json", "r"))
        broker = db["broker"]
        
        return json.dumps(broker, indent=3)
    
    def POST(self, *path, **queries):
        """
        This function updates the broker endpoints and timestamp
        (for future developments)
        """
        pass

def brokerLoader():
    db = json.load(open("src/db/catalog.json", "r"))
    broker = json.load(open("src/db/broker.json", "r"))

    db["broker"]["ip"] = broker["ip"]
    db["broker"]["port"] = broker["port"]
    db["broker"]["timestamp"] = time.time()

    json.dump(db, open("src/db/catalog.json", "w"), indent=3)


# In the POST process the function must create the dictionary structure that will be added to the list in the database (like the managers)
class ThingSpeakAdaptor(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get the ThingSpeak adaptors endpoints, functions and timestamp
        """
        db = json.load(open("src/db/catalog.json", "r"))
        thingspeak_adaptors = db["thingspeak_adaptors"]
        
        return json.dumps(thingspeak_adaptors, indent=3)
    
    def POST(self, *path, **queries):
        """
        This function updates the ThingSpeak adaptors endpoints and timestamp
        """
        db = json.load(open("src/db/catalog.json", "r"))
        input = json.loads(cherrypy.request.body.read())

        try:
            ip = input["ip"]
            port = input["port"]
            functions = input["functions"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        thingspeak_adaptor_dict = {
            "ip": ip,
            "port": port,
            "functions": functions,
            "timestamp": time.time()
        }
        if len(db["thingspeak_adaptors"]) == 0:
            db["thingspeak_adaptors"].append(thingspeak_adaptor_dict)
        else:
            update = False
            for t_adaptor in db["thingspeak_adaptors"]:
                if t_adaptor["ip"] == ip and t_adaptor["port"] == port:
                    t_adaptor["functions"] = functions
                    t_adaptor["timestamp"] = time.time()
                    update = True
            
            if update == False:
                db["thingspeak_adaptors"].append(thingspeak_adaptor_dict)

        json.dump(db, open("src/db/catalog.json", "w"), indent=3)


class ThingSpeak(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get the ThingSpeak endpoints and timestamp
        """
        db = json.load(open("src/db/catalog.json", "r"))
        thingspeak = db["thingspeak"]
        
        return json.dumps(thingspeak, indent=3)
    
def thingSpeakLoader():
    db = json.load(open("src/db/catalog.json", "r"))
    thingspeak = json.load(open("src/db/thingspeak.json", "r"))

    db["thingspeak"]["ip"] = thingspeak["ip"]
    db["thingspeak"]["port"] = thingspeak["port"]
    db["thingspeak"]["timestamp"] = time.time()

    json.dump(db, open("src/db/catalog.json", "w"), indent=3)


# In the POST process the function must create the dictionary structure that will be added to the list in the database (like the managers)
class WebPage(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get the webpages endpoints and timestamp
        """
        db = json.load(open("src/db/catalog.json", "r"))
        webpages = db["webpages"]
        
        return json.dumps(webpages, indent=3)
    
    def POST(self, *path, **queries):
        """
        This function updates the webpages endpoints and timestamp
        """
        pass


class WeatherAPI(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get the weather API endpoints and timestamp
        """
        db = json.load(open("src/db/catalog.json", "r"))
        weather_API = db["weather_API"]
        
        return json.dumps(weather_API, indent=3)
    
def weatherAPILoader():
    db = json.load(open("src/db/catalog.json", "r"))
    weather_API = json.load(open("src/db/weatherAPI.json", "r"))

    db["weather_API"]["ip"] = weather_API["ip"]
    db["weather_API"]["port"] = weather_API["port"]
    db["weather_API"]["timestamp"] = time.time()

    json.dump(db, open("src/db/catalog.json", "w"), indent=3)


class IrrigationManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get the irrigation managers endpoints and timestamp
        """
        db = json.load(open("src/db/catalog.json", "r"))
        irr_manager = db["managers"]["irrigation"]
        
        return json.dumps(irr_manager, indent=3)
    
    def POST(self, *path, **queries):
        """
        This function updates and adds the irrigation managers (endpoints, functions and timestamp)
        """
        db = json.load(open("src/db/catalog.json", "r"))
        input = json.loads(cherrypy.request.body.read())

        try:
            ip = input["ip"]
            port = input["port"]
            functions = input["functions"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        manager_dict = {
            "ip": ip,
            "port": port,
            "functions": functions,
            "timestamp": time.time()
        }
        if len(db["managers"]["irrigation"]) == 0:
            db["managers"]["irrigation"].append(manager_dict)
        else:
            update = False
            for irr_manager in db["managers"]["irrigation"]:
                if irr_manager["ip"] == ip and irr_manager["port"] == port:
                    irr_manager["functions"] = functions
                    irr_manager["timestamp"] = time.time()
                    update = True
            
            if update == False:
                db["managers"]["irrigation"].append(manager_dict)

        json.dump(db, open("src/db/catalog.json", "w"), indent=3)
            

class EnvironmentManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get the environment managers endpoints and timestamp
        """
        db = json.load(open("src/db/catalog.json", "r"))
        env_manager = db["managers"]["environment"]
        
        return json.dumps(env_manager, indent=3)
    
    def POST(self, *path, **queries):
        """
        This function updates and adds the enviroment managers (endpoints, functions and timestamp)
        """
        db = json.load(open("src/db/catalog.json", "r"))
        input = json.loads(cherrypy.request.body.read())

        try:
            ip = input["ip"]
            port = input["port"]
            functions = input["functions"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        manager_dict = {
            "ip": ip,
            "port": port,
            "functions": functions,
            "timestamp": time.time()
        }
        if len(db["managers"]["environment"]) == 0:
            db["managers"]["environment"].append(manager_dict)
        else:
            update = False
            for env_manager in db["managers"]["environment"]:
                if env_manager["ip"] == ip and env_manager["port"] == port:
                    env_manager["functions"] = functions
                    env_manager["timestamp"] = time.time()
                    update = True
            
            if update == False:
                db["managers"]["environment"].append(manager_dict)
        
        json.dump(db, open("src/db/catalog.json", "w"), indent=3)


class WeatherManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get the weather managers endpoints and timestamp
        """
        db = json.load(open("src/db/catalog.json", "r"))
        wea_manager = db["managers"]["weather"]
        
        return json.dumps(wea_manager, indent=3)
    
    def POST(self, *path, **queries):
        """
        This function updates and adds the weather managers (endpoints, functions and timestamp)
        """
        db = json.load(open("src/db/catalog.json", "r"))
        input = json.loads(cherrypy.request.body.read())

        try:
            ip = input["ip"]
            port = input["port"]
            functions = input["functions"]
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameters')

        manager_dict = {
            "ip": ip,
            "port": port,
            "functions": functions,
            "timestamp": time.time()
        }
        if len(db["managers"]["weather"]) == 0:
            db["managers"]["weather"].append(manager_dict)
        else:
            update = False
            for wea_manager in db["managers"]["weather"]:
                if wea_manager["ip"] == ip and wea_manager["port"] == port:
                    wea_manager["functions"] = functions
                    wea_manager["timestamp"] = time.time()
                    update = True
            
            if update == False:
                db["managers"]["weather"].append(manager_dict)

        json.dump(db, open("src/db/catalog.json", "w"), indent=3)


def remove_from_db(category = "", idx = -1):
    db = json.load(open("src/db/catalog.json", "r"))
    category = category.split("/")
    
    # DELETE a device connector of a greenhouse
    if len(category) == 4:
        for user in db["users"]:
            if user["id"] == category[0]:
                for greenhouse in user["greenHouses"]:
                    if greenhouse["greenHouseID"] == category[1]:
                        for index, dev_conn in enumerate(greenhouse["deviceConnectors"]):
                            if dev_conn["ip"] == category[2] and dev_conn["port"] == category[3]:
                                greenhouse["deviceConnectors"].pop(index)
                                break
    # DELETE a manager of the system
    elif len(category) == 2:
        db[category[0]][category[1]].pop(idx)
    # DELETE a ThingSpeak adaptor or a webpage
    else:
        db[category[0]].pop(idx)

    json.dump(db, open("src/db/catalog.json", "w"), indent=3)


def post_to_manager_and_adaptor(strategyType = "", strat_info = {}):
    db = json.load(open("src/db/catalog.json", "r"))

    # We suppose that there is just one manager per type (and we take just the first of the list)
    try:
        manager_info = db["managers"][strategyType][0]
    except:
        raise Exception("No manager present for that strategy") 
    
    if strategyType == "irrigation":
        payload = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"],
            'active': strat_info["active"], 
            'stratID': strat_info["stratID"],
            'time': strat_info["time"], 
            'water_quantity': strat_info["water_quantity"],
            'activeStrat': strat_info["activeStrat"]
        }
        payload_adaptor = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"],
            'strategyType': strategyType,
            'stratID': strat_info["stratID"]
        }
    elif strategyType == "weather":
        for user in db["users"]:
            if user["id"] == strat_info["userID"]:
                payload = {
                    'userID': strat_info["userID"], 
                    'greenHouseID': strat_info["greenHouseID"],
                    'active': strat_info["active"],
                    'temperature': strat_info["temperature"],
                    "humidity": strat_info["humidity"],
                    "city": user["city"]
                }
                break
        payload_adaptor = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"],
            'strategyType': strategyType
        }
    else:
        payload = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"],
            'active': strat_info["active"],
            'temperature': strat_info["temperature"],
            "humidity": strat_info["humidity"]
        }
        payload_adaptor = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"],
            'strategyType': strategyType
        }

    # We suppose that the managers can have just one function (regStrategy)
    url_manager = manager_info["ip"]+":"+str(manager_info["port"])+"/"+manager_info["functions"][0]
    requests.post(url_manager, payload)

    # There could be more then one adaptor but we consider just in this phase
    url_adaptor = db["thingspeak_adaptors"][0]["ip"]+":"+str(db["thingspeak_adaptors"][0]["port"])+"/"+db["thingspeak_adaptors"][0]["functions"][0]
    requests.post(url_adaptor, payload_adaptor)


# We can only change the activity of the strategies, nothing else
def put_to_manager(strategyType = "", strat_info = {}):
    db = json.load(open("src/db/catalog.json", "r"))

    # We suppose that there is just one manager per type (and we take just the first of the list)
    try:
        manager_info = db["managers"][strategyType][0]
    except:
        raise Exception("No manager present for that strategy")
    
    if strategyType == "irrigation":
        try:
            stratID = strat_info["stratID"]
            activeStrat = strat_info["activeStrat"]
        except:
            payload = {
                'userID': strat_info["userID"], 
                'greenHouseID': strat_info["greenHouseID"],
                'active': strat_info["active"]
            }
        else:
            payload = {
                'userID': strat_info["userID"], 
                'greenHouseID': strat_info["greenHouseID"],
                'active': strat_info["active"], 
                'stratID': stratID,
                'activeStrat': activeStrat
            }
    else:
        payload = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"],
            'active': strat_info["active"]
        }
    # We suppose that the managers can have just one function (regStrategy)
    url = manager_info["ip"]+":"+str(manager_info["port"])+"/"+manager_info["functions"][0]
    requests.put(url, payload)


def delete_to_manager_and_adaptor(strategyType = "", strat_info = {}):
    db = json.load(open("src/db/catalog.json", "r"))

    # We suppose that there is just one manager per type (and we take just the first of the list)
    try:
        manager_info = db["managers"][strategyType][0]
    except:
        raise Exception("No manager present for that strategy")
    
    if strategyType == "irrigation":
        try:
            params = {
                'userID': strat_info["userID"], 
                'greenHouseID': strat_info["greenHouseID"],
                'stratID': strat_info["stratID"]
            }
            payload_adaptor = {
                'userID': strat_info["userID"], 
                'greenHouseID': strat_info["greenHouseID"],
                'strategyType': strategyType,
                'stratID': strat_info["stratID"]
            }
        except:
            params = {
                'userID': strat_info["userID"], 
                'greenHouseID': strat_info["greenHouseID"]
            }
            payload_adaptor = {
                'userID': strat_info["userID"], 
                'greenHouseID': strat_info["greenHouseID"],
                'strategyType': strategyType
            }
    else:
        params = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"]
        }
        payload_adaptor = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"],
            'strategyType': strategyType
        }
        
    # We suppose that the managers can have just one function (regStrategy)
    url = manager_info["ip"]+":"+str(manager_info["port"])+"/"+manager_info["functions"][0]
    requests.delete(url, params=params)

    url_adaptor = db["thingspeak_adaptors"][0]["ip"]+":"+str(db["thingspeak_adaptors"][0]["port"])+"/"+db["thingspeak_adaptors"][0]["functions"][0]
    requests.post(url_adaptor, payload_adaptor)


if __name__=="__main__":

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }
    cherrypy.tree.mount(User(), '/user', conf)
    cherrypy.tree.mount(GreenHouse(), '/greenhouse', conf)
    cherrypy.tree.mount(Strategy(), '/strategy', conf)
    cherrypy.tree.mount(Broker(), '/broker', conf)
    cherrypy.tree.mount(ThingSpeakAdaptor(), '/thingspeak_adaptor', conf)
    cherrypy.tree.mount(ThingSpeak(), '/thingspeak', conf)
    cherrypy.tree.mount(WebPage(), '/webpage', conf)
    cherrypy.tree.mount(WeatherAPI(), '/weatherAPI', conf)
    cherrypy.tree.mount(IrrigationManager(), '/irrigation_manager', conf)
    cherrypy.tree.mount(EnvironmentManager(), '/environment_manager', conf)
    cherrypy.tree.mount(WeatherManager(), '/weather_manager', conf)

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()

    db = json.load(open("src/db/catalog.json", "r"))

    # BOOT: retrieve the BROKER ENDPOINTS from a json file
    brokerLoader()

    # BOOT: retrieve the THINGSPEAK ENDPOINTS from a json file
    thingSpeakLoader()

    # BOOT: retrieve the WEATHER API ENDPOINTS from a json file
    weatherAPILoader()
    
    # BOOT: retrieve the THINGSPEAK ADAPTORS info from the database (catalog.json)
    thingspeak_adaptors = db["thingspeak_adaptors"]
    timeout_adaptor = 300 

    # BOOT: retrieve the WEBPAGE info from the database (catalog.json)
    webpages = db["webpages"]
    timeout_webpage = 1200

    # BOOT: retrieve the IRRIGATION MANAGERS info from the database (catalog.json)
    irrigation_managers = db["managers"]["irrigation"]
    timeout_irr_manager = 120

    # BOOT: retrieve the ENVIRONMENT MANAGERS info from the database (catalog.json)
    environment_managers = db["managers"]["environment"]
    timeout_env_manager = 120

    # BOOT: retrieve the WEATHER MANAGERS info from the database (catalog.json)
    weather_managers = db["managers"]["weather"]
    timeout_wea_manager = 120

    # BOOT: retrieve all the DEVICE CONNECTORS info from the database (catalog.json)
    device_connectors_list = []
    device_connectors_dict = {
        "userID": -1,
        "greenHouseID": -1,
        "dev_conn": {}
    }
    if len(db["users"]) > 0:
        for user in db["users"]:
            for greenhouse in user["greenHouses"]:
                for dev_conn in greenhouse["deviceConnectors"]:
                    device_connectors_dict["userID"] = user["id"]
                    device_connectors_dict["greenHouseID"] = greenhouse["greenHouseID"]
                    device_connectors_dict["dev_conn"] = dev_conn
                    device_connectors_list.append(device_connectors_dict)
    timeout_dev_connector = 120

    
    while True:
        timestamp = time.time()
        
        if len(thingspeak_adaptors) > 0:
            for idx, adaptor in enumerate(thingspeak_adaptors):
                if timestamp - float(adaptor["timestamp"]) >= timeout_adaptor:
                    remove_from_db("thingspeak_adaptor/", idx)
        if len(webpages) > 0:
            for idx, webpage in enumerate(webpages):
                if timestamp - float(webpage["timestamp"]) >= timeout_webpage:
                    remove_from_db("webpage/", idx)
        if len(irrigation_managers) > 0:
            for idx, manager in enumerate(irrigation_managers):
                if timestamp - float(manager["timestamp"]) >= timeout_irr_manager:
                    remove_from_db("managers/irrigation", idx)
        if len(environment_managers) > 0:
            for idx, manager in enumerate(environment_managers):
                if timestamp - float(manager["timestamp"]) >= timeout_env_manager:
                    remove_from_db("managers/environment", idx)
        if len(weather_managers) > 0:
            for idx, manager in enumerate(weather_managers):
                if timestamp - float(manager["timestamp"]) >= timeout_wea_manager:
                    remove_from_db("managers/weather", idx)
        if len(device_connectors_list) > 0:
            for dev_conn in device_connectors_list:
                if timestamp - float(dev_conn["dev_conn"]["timestamp"]) >= timeout_dev_connector:
                    remove_from_db(str(dev_conn["userID"])+"/"+dev_conn["greenHouseID"]+"/"+dev_conn["dev_conn"]["ip"]+"/"+str(dev_conn["dev_conn"]["port"]))
            

        # time.sleep(60)
        db = json.load(open("src/db/catalog.json", "r"))
        thingspeak_adaptors = db["thingspeak_adaptors"]
        webpages = db["webpages"]
        irrigation_managers = db["managers"]["irrigation"]
        environment_managers = db["managers"]["environment"]
        weather_managers = db["managers"]["weather"]
        
        device_connectors_list = []
        if len(db["users"]) > 0:
            for user in db["users"]:
                for greenhouse in user["greenHouses"]:
                    for dev_conn in greenhouse["deviceConnectors"]:
                        device_connectors_dict["userID"] = user["id"]
                        device_connectors_dict["greenHouseID"] = greenhouse["greenHouseID"]
                        device_connectors_dict["dev_conn"] = dev_conn
                        device_connectors_list.append(device_connectors_dict)
