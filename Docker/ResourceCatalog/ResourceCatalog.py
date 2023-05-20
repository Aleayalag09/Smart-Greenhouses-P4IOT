import json
import cherrypy
import time
import requests


class User(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns a specific user or all the users.
        """
        
        with open("db/catalog.json", "r") as file:
            db = json.load(file)

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
        Creates a new user.

        The ID must be "registered" and provided by the system owners
        before this function is called. 
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

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
            "greenHouses": [],
            "timestamp": time.time()
        }
        input = json.loads(cherrypy.request.body.read())
        try:
            new_user["userName"] = input['userName']
            new_user["password"] = input['password']
            new_user["id"] = int(input["id"])
            new_user["name"] = input['name']
            new_user["surname"] = input['surname']
            new_user["email_addresses"] = input['email_addresses']
            new_user["country"] = input['country']
        except:
            raise cherrypy.HTTPError(400, 'Wrong parameter')
        else:
            users.append(new_user)
            db["users"] = users
            
            with open("db/catalog.json", "w") as file:
                json.dump(db, file, indent=3)
            
            return new_user
            
    def PUT(self, *path, **queries): 
        """
        Modify the personal data of a specific user.

        Modifications allowed:
        - userName
        - password
        - name
        - surname
        - email_address
        """

        try: 
            id = queries['id']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        input = json.loads(cherrypy.request.body.read())
        
        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        users = db["users"]
        
        keys_to_change = input.keys()
        key_not_allowed = ["id","super_User","greenHouses","timestamp","country"]
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
                    
                    with open("db/catalog.json", "w") as file:
                        json.dump(db, file, indent=3)
                    
                    return "Updated keys: "+str(keys)
        except:
            raise cherrypy.HTTPError(400, 'No user found')
        
        raise cherrypy.HTTPError(400, 'No user found')
    
    def DELETE(self, *path, **queries):
        """
        Deletes a specific user and all of 
        its information in the DB.

        Sends also DELETE messages to the managers
        to delete the strategies related to the user.
        """
        
        try: 
            id = queries['id']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        users = db["users"]
        
        for idx, user in enumerate(users):
            if user['id'] == int(id):

                for i in range(len(user["greenHouses"])):
                    delete_manager_dict = {
                        'userID': id, 
                        'greenHouseID': i
                    }

                    for dev_conn in user["greenHouses"][i]["deviceConnectors"]:
                        # I assume that there is just one Adaptor
                        url_adaptor = db["thingspeak_adaptors"][0]["ip"]+":"+str(db["thingspeak_adaptors"][0]["port"])+"/"+db["thingspeak_adaptors"][0]["functions"][0]
                        payload = {
                            "userID": id,
                            "greenHouseID": i
                        }
                        requests.delete(url_adaptor, params=payload)

                    # We can communicate that the strategy manager is not present if we want 
                    try:
                        delete_to_manager("irrigation", delete_manager_dict)
                        delete_to_dev_conn("irrigation", delete_manager_dict)
                    except:
                        pass
                    try:
                        delete_to_manager("environment", delete_manager_dict)
                        delete_to_dev_conn("environment", delete_manager_dict)
                    except:
                        pass
                    try:
                        delete_to_manager("weather", delete_manager_dict)
                        delete_to_dev_conn("weather", delete_manager_dict)
                    except:
                        pass

                users.pop(idx)
                db["users"] = users

                with open("db/catalog.json", "w") as file:
                    json.dump(db, file, indent=3)

                return "Deleted user "+str(id)
            
        raise cherrypy.HTTPError(400, 'No user found')
    

class GreenHouse(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns a specific greenhouse or all 
        the greenhouses of an user.
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        users = db["users"]
        
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        else:
            try:
                if queries['greenHouseID'] == "all":
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
        Creates a new greenhouse for a specific user.

        The greenHouse ID must be "registered" and provided by the system owners
        before this function is called. 
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        users = db["users"]
        try:
            userID = int(queries['id'])
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')

        for user in users:
            if user['id'] == int(userID):

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
                    new_greenhouse["greenHouseID"] = int(input["greenHouseID"])
                except:
                    raise cherrypy.HTTPError(400, 'Wrong parameter')
                else:
                    user['greenHouses'].append(new_greenhouse)
                    user["timestamp"] = time.time()
                    db["users"] = users
                    
                    with open("db/catalog.json", "w") as file:
                        json.dump(db, file, indent=3)
                    
                    return "New greenhouse for user "+str(userID)+": "+str(new_greenhouse)
        
        raise cherrypy.HTTPError(400, 'No user found')
            
    def PUT(self, *path, **queries): 
        """
        Modify the information of a specific greenhouse of an user.
        
        Modifications allowed:
        - greenHouseName
        """

        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        input = json.loads(cherrypy.request.body.read())
        
        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        users = db["users"]
        
        keys_to_change = input.keys()
        key_not_allowed = ["greenHouseID","deviceConnectors", "strategies","city"]  
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
                            
                            with open("db/catalog.json", "w") as file:
                                json.dump(db, file, indent=3)

                            return "Updated keys: "+str(keys)
        except:  
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
        
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
    
    def DELETE(self, *path, **queries):
        """
        Deletes a specific greenhouse of an user
        and all of its information in the DB.

        Sends also DELETE messages to the managers
        to delete the strategies related to the greenhouse.
        """
        
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        users = db["users"]
        try: 
            for user in users:
                if user['id'] == int(id):
                    for idx, greenHouse in enumerate(user['greenHouses']):
                        if greenHouse['greenHouseID'] == int(greenHouseID):

                            delete_manager_dict = {
                                'userID': id, 
                                'greenHouseID': greenHouseID
                            }

                            for dev_conn in greenHouse["deviceConnectors"]:
                                # I assume that there is just one Adaptor
                                url_adaptor = db["thingspeak_adaptors"][0]["ip"]+":"+str(db["thingspeak_adaptors"][0]["port"])+"/"+db["thingspeak_adaptors"][0]["functions"][0]
                                payload = {
                                    "userID": id,
                                    "greenHouseID": greenHouseID
                                }
                                requests.delete(url_adaptor, params=payload)

                            # We can communicate that the strategy manager is not present if we want 
                            try:
                                delete_to_manager("irrigation", delete_manager_dict)
                                delete_to_dev_conn("irrigation", delete_manager_dict)
                            except:
                                pass
                            try:
                                delete_to_manager("environment", delete_manager_dict)
                                delete_to_dev_conn("environment", delete_manager_dict)
                            except:
                                pass
                            try:
                                delete_to_manager("weather", delete_manager_dict)
                                delete_to_dev_conn("weather", delete_manager_dict)
                            except:
                                pass

                            user['greenHouses'].pop(idx)
                            user["timestamp"] = time.time()
                            db["users"] = users
                            
                            with open("db/catalog.json", "w") as file:
                                json.dump(db, file, indent=3)

                            return "Deleted greenhouse "+str(greenHouseID)+" of user "+str(id)
        except:     
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
        
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')


# If path[0] is equal to manager it means that it is the boot request of a manager, therefore it needs all the strategies present
class Strategy(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns a specific strategy (Irrigation, Environment, Weather)
        or all the strategies of a specific user and greenhouse.

        Manager mode: dedicated to the strategy managers for boot operations.
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

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
                                    strategy_list.append({
                                                            "userID": user["id"],
                                                            "greenHouseID": greenhouse["greenHouseID"],
                                                            "strat": strat,
                                                            "active": greenhouse["strategies"]["irrigation"]["active"]
                                                        })
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
                                strategy_dict["city"] = greenhouse["city"]
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
        Creates a new strategy for a specific user and greenhouse.

        If you want to update one strategy you must 
        first delete it and then create a new one.
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

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
                                    
                                    with open("db/catalog.json", "w") as file:
                                        json.dump(db, file, indent=3)

                                    post_manager_dict = {
                                        'userID': id, 
                                        'greenHouseID': greenHouseID,
                                        'active': activeIrr, 
                                        'stratID': strategyID,
                                        'time': stime, 
                                        'water_quantity': water_quantity,
                                        'activeStrat': activeStrat
                                    }

                                    try:
                                        post_to_manager("irrigation", post_manager_dict)
                                        post_to_dev_conn("irrigation", post_manager_dict)
                                    except:
                                        pass

                                    return post_manager_dict
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
                                    active = input["active"]
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
                                
                                with open("db/catalog.json", "w") as file:
                                    json.dump(db, file, indent=3)

                                try:
                                    post_to_manager(strategyType, post_manager_dict)
                                    post_to_dev_conn(strategyType, post_manager_dict)
                                except:
                                    pass

                                return post_manager_dict
            except: 
                raise cherrypy.HTTPError(400, 'No user or greenhouse found')            
        else:
            raise cherrypy.HTTPError(400, 'Wrong strategy type')
        
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')

    def PUT(self, *path, **queries): 
        """
        Modify the state of activity of a strategy
        of a specific user and greenhouse.

        If the strategy is "irrigation" it can be specified 
        the state of activity of a single strategy
        instead that for all of them.
        """

        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            strategyType = queries['strategyType']
            if queries['active'] == "False":
                active = False
            elif queries['active'] == "True":
                active = True
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        users = db["users"]

        try:
            for user in users:
                if user['id'] == int(id):
                    for greenhouse in user['greenHouses']:
                        if greenhouse['greenHouseID'] == int(greenHouseID):
                            flagIrr = False
                            if strategyType == "irrigation":
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
                                
                                with open("db/catalog.json", "w") as file:
                                    json.dump(db, file, indent=3)

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

                                try:
                                    put_to_manager(strategyType, put_manager_dict)
                                except:
                                    pass

                                return put_manager_dict
        except:
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
                
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
    
    # For the irrigation strategies you can specify the strategy ID
    def DELETE(self, *path, **queries):
        """
        Deletes a strategy of a specific user and greenhouse.

        If you want to modify one you must 
        delete it before and then create a new one.

        If the strategy is "irrigation" it can be deleted 
        just one strategy specifying its ID.
        """
        
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            strategyType = queries['strategyType']
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        with open("db/catalog.json", "r") as file:
            db = json.load(file)

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
                                    strategyID = int(queries["strategyID"])
                                except:
                                    greenhouse['strategies']['irrigation'] = strat_dict
                                    user["timestamp"] = time.time()
                                    db["users"] = users
                                    
                                    with open("db/catalog.json", "w") as file:
                                        json.dump(db, file, indent=3)

                                    delete_manager_dict = {
                                        'userID': id, 
                                        'greenHouseID': greenHouseID
                                    }
                                
                                    delete_to_manager("irrigation", delete_manager_dict)
                                    delete_to_dev_conn("irrigation", delete_manager_dict)

                                    return "Deleted all irrigation strategies for greenhouse "+str(greenHouseID)+" of user "+str(id)
                                else:
                                    try:
                                        greenhouse['strategies']['irrigation']['strat'][strategyID]
                                    except:
                                        raise cherrypy.HTTPError(400, 'Strategy not found')
                                    else:
                                        devconn_strat_ID = len(greenhouse['strategies']['irrigation']['strat'])-1
                                        delete_manager_dict = {
                                            'userID': id, 
                                            'greenHouseID': greenHouseID,
                                            'stratID': devconn_strat_ID
                                        }
                                        delete_to_dev_conn("irrigation", delete_manager_dict)
                                        delete_manager_dict = {
                                            'userID': id, 
                                            'greenHouseID': greenHouseID,
                                            'stratID': strategyID
                                        }
                                        delete_to_manager("irrigation", delete_manager_dict)

                                        for i in range(len(greenhouse['strategies']['irrigation']['strat'])):
                                            if i>strategyID:
                                                index = int(greenhouse['strategies']['irrigation']['strat'][i]["id"]) - 1
                                                greenhouse['strategies']['irrigation']['strat'][i]["id"] = index

                                        greenhouse['strategies']['irrigation']['strat'].pop(strategyID)
                                        greenhouse['strategies']['irrigation']["timestamp"] = time.time()
                                        user["timestamp"] = time.time()
                                        db["users"] = users
                                        
                                        with open("db/catalog.json", "w") as file:
                                            json.dump(db, file, indent=3)

                                        return "Deleted irrigation strategy "+str(strategyID)+" for greenhouse "+str(greenHouseID)+" of user "+str(id)
                            else:
                                try:
                                    greenhouse['strategies'][strategyType] = strat_dict
                                except:
                                    raise cherrypy.HTTPError(400, 'Wrong strategy type')
                                else:
                                    user["timestamp"] = time.time()
                                    db["users"] = users
                                    
                                    with open("db/catalog.json", "w") as file:
                                        json.dump(db, file, indent=3)

                                    delete_manager_dict = {
                                        'userID': id, 
                                        'greenHouseID': greenHouseID
                                    }

                                    delete_to_manager(strategyType, delete_manager_dict)
                                    delete_to_dev_conn(strategyType, delete_manager_dict)

                                    
                                    return "Deleted all "+strategyType+" strategies for greenhouse "+str(greenHouseID)+" of user "+str(id)
        except:
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
                    
        raise cherrypy.HTTPError(400, 'No user, greenhouse or strategy found')
    

class DeviceConnectors(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns the information of the device connectors
        of a user greenhouse.
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        users = db["users"]
        
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            try:
                if path[0] != "adaptor":
                    raise Exception
            except:
                pass
            else:
                dev_conn_list = []
                dev_conn = {
                    "userID": -1,
                    "greenHouseID": -1,
                    "sensors": []
                }
                for user in users:
                    for greenhouse in user["greenHouses"]:
                        for conn in greenhouse["deviceConnectors"]:
                            dev_conn["userID"] = user["id"]
                            dev_conn["greenHouseID"] = greenhouse["greenHouseID"]
                            dev_conn["sensors"] = conn["devices"]["sensors"]

                            dev_conn_list.append(dev_conn)

                return json.dumps(dev_conn_list, indent=3)

            raise cherrypy.HTTPError(400, 'Bad request') 
        else:
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
        Updates and adds to a specific user 
        greenhouse the device connectors.
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        input = json.loads(cherrypy.request.body.read())

        try:
            userID = input["userID"]
            greenHouseID = input["greenHouseID"]
            ip = input["ip"]
            port = input["port"]
            sensors = input["sensors"]
            actuators = input["actuators"]
            functions = input["functions"]
            window_factor = input["window_factor"]
            humidifier_factor = input["humidifier_factor"]
            ac_factor = input["ac_factor"]
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
            "window_factor": window_factor,
            "humidifier_factor": humidifier_factor,
            "ac_factor": ac_factor,
            "timestamp": time.time()
        }
        try:
            for user in db["users"]:
                if user["id"] == int(userID):
                    for greenhouse in user["greenHouses"]:
                        if greenhouse["greenHouseID"] == int(greenHouseID):
                            update = False
                            if len(greenhouse["deviceConnectors"]) == 0:
                                greenhouse["deviceConnectors"].append(dev_conn_dict)
                            else:
                                for dev_conn in greenhouse["deviceConnectors"]:
                                    if dev_conn["ip"] == ip and dev_conn["port"] == port:
                                        dev_conn["devices"]["sensors"] = sensors
                                        dev_conn["devices"]["actuators"] = actuators
                                        dev_conn["functions"] = functions
                                        dev_conn["window_factor"] = window_factor
                                        dev_conn["humidifier_factor"] = humidifier_factor 
                                        dev_conn["ac_factor"] = ac_factor
                                        dev_conn["timestamp"] = time.time()
                                        update = True
                                
                                if update == False:
                                    greenhouse["deviceConnectors"].append(dev_conn_dict)

                            if update == False:
                                # I assume that there is just one Adaptor
                                url_adaptor = db["thingspeak_adaptors"][0]["ip"]+":"+str(db["thingspeak_adaptors"][0]["port"])+"/"+db["thingspeak_adaptors"][0]["functions"][0]
                                payload = {
                                    "userID": userID,
                                    "greenHouseID": greenHouseID,
                                    "sensors": sensors
                                }
                                requests.post(url_adaptor, json.dumps(payload))
                            
                            with open("db/catalog.json", "w") as file:
                                json.dump(db, file, indent=3)

                            return
        except:
            raise cherrypy.HTTPError(400, 'No user or greenhouse found')
        
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')


class Broker(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns the broker endpoints and timestamp.
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        broker = db["broker"]
        
        return json.dumps(broker, indent=3)
    
    def POST(self, *path, **queries):
        """
        This function updates the broker endpoints and timestamp
        (for future developments)
        """

        pass

def brokerLoader():
    """
    Loads the static endpoints of the broker.
    """

    with open("db/catalog.json", "r") as file:
        db = json.load(file)
    
    with open("db/broker.json", "r") as file:
        broker = json.load(file)

    db["broker"]["ip"] = broker["ip"]
    db["broker"]["port"] = broker["port"]
    db["broker"]["timestamp"] = time.time()

    with open("db/catalog.json", "w") as file:
        json.dump(db, file, indent=3)


class ThingSpeakAdaptor(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns the ThingSpeak adaptors information
        (endpoints, functions and timestamp).
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        thingspeak_adaptors = db["thingspeak_adaptors"]
        
        return json.dumps(thingspeak_adaptors, indent=3)
    
    def POST(self, *path, **queries):
        """
        Updates and adds the ThingSepak adaptor information
        (endpoints, functions and timestamp).
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

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

        with open("db/catalog.json", "w") as file:
            json.dump(db, file, indent=3)


class ThingSpeak(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns the ThingSpeak endpoints and timestamp.
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        thingspeak = db["thingspeak"]
        
        return json.dumps(thingspeak, indent=3)
    
def thingSpeakLoader():
    """
    Loads the static endpoints of ThingSpeak.
    """

    with open("db/catalog.json", "r") as file:
        db = json.load(file)

    with open("db/thingspeak.json", "r") as file:
        thingspeak = json.load(file)

    db["thingspeak"]["ip"] = thingspeak["ip"]
    db["thingspeak"]["port"] = thingspeak["port"]
    db["thingspeak"]["timestamp"] = time.time()

    with open("db/catalog.json", "w") as file:
        json.dump(db, file, indent=3)


# In the POST process the function must create the dictionary structure that will be added to the list in the database (like the managers)
class WebPage(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns the webpages endpoints and timestamp.
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)
        
        webpages = db["webpages"]
        
        return json.dumps(webpages, indent=3)
    
    def POST(self, *path, **queries):
        """
        Updates the webpages information
        (endpoints and timestamp).
        """
        pass


class WeatherAPI(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns the weather API endpoints and timestamp.
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        weather_API = db["weather_API"]
        
        return json.dumps(weather_API, indent=3)
    
def weatherAPILoader():
    """
    Loads the static endpoints of the weather API.
    """
    
    with open("db/catalog.json", "r") as file:
        db = json.load(file)
        
    with open("db/weatherAPI.json", "r") as file:
        weather_API = json.load(file)

    db["weather_API"]["ip"] = weather_API["ip"]
    db["weather_API"]["port"] = weather_API["port"]
    db["weather_API"]["timestamp"] = time.time()

    with open("db/catalog.json", "w") as file:
        json.dump(db, file, indent=3)


class IrrigationManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns the irrigation managers information
        (endpoints, functions and timestamp).
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        irr_manager = db["managers"]["irrigation"]
        
        return json.dumps(irr_manager, indent=3)
    
    def POST(self, *path, **queries):
        """
        Updates and adds the irrigation managers information
        (endpoints, functions and timestamp).
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

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

        with open("db/catalog.json", "w") as file:
            json.dump(db, file, indent=3)
            

class EnvironmentManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns the environment managers information
        (endpoints, functions and timestamp).
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        env_manager = db["managers"]["environment"]
        
        return json.dumps(env_manager, indent=3)
    
    def POST(self, *path, **queries):
        """
        Updates and adds the environment managers information
        (endpoints, functions and timestamp).
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)
        
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
        
        with open("db/catalog.json", "w") as file:
            json.dump(db, file, indent=3)


class WeatherManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Returns the weather managers information
        (endpoints, functions and timestamp).
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

        wea_manager = db["managers"]["weather"]
        
        return json.dumps(wea_manager, indent=3)
    
    def POST(self, *path, **queries):
        """
        Updates and adds the weather managers information
        (endpoints, functions and timestamp).
        """

        with open("db/catalog.json", "r") as file:
            db = json.load(file)

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

        with open("db/catalog.json", "w") as file:
            json.dump(db, file, indent=3)


def remove_from_db(category = "", idx = -1):
    """
    Remove old information from the DB:
    - device connector
    - strategy manager
    - ThingSpeak adaptor
    - Webpage
    """

    with open("db/catalog.json", "r") as file:
        db = json.load(file)

    category = category.split("/")

    if category[1] == "":
        category = [category[0]]
    
    # DELETE a device connector of a greenhouse
    if len(category) == 4:
        for user in db["users"]:
            if user["id"] == int(category[0]):
                for greenhouse in user["greenHouses"]:
                    if greenhouse["greenHouseID"] == int(category[1]):
                        for index, dev_conn in enumerate(greenhouse["deviceConnectors"]):
                            if dev_conn["ip"] == category[2] and dev_conn["port"] == int(category[3]):
                                greenhouse["deviceConnectors"].pop(index)

                                # I assume that there is just one Adaptor
                                url_adaptor = db["thingspeak_adaptors"][0]["ip"]+":"+str(db["thingspeak_adaptors"][0]["port"])+"/"+db["thingspeak_adaptors"][0]["functions"][0]
                                payload = {
                                    "userID": category[0],
                                    "greenHouseID": category[1]
                                }
                                requests.delete(url_adaptor, params=payload)
                                break
    # DELETE a manager of the system
    elif len(category) == 2:
        db[category[0]][category[1]].pop(idx)
    # DELETE a ThingSpeak adaptor or a webpage
    else:
        db[category[0]].pop(idx)

    with open("db/catalog.json", "w") as file:
        json.dump(db, file, indent=3)


def post_to_manager(strategyType = "", strat_info = {}):
    """
    Send a POST message to a specific strategy manager
    in order to create a new strategy.
    """

    with open("db/catalog.json", "r") as file:
        db = json.load(file)

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
    elif strategyType == "weather":
        for user in db["users"]:
            if user["id"] == int(strat_info["userID"]):
                for greenhouse in user["greenHouses"]:
                    if greenhouse["greenHouseID"] == int(strat_info["greenHouseID"]):
                        payload = {
                            'userID': strat_info["userID"], 
                            'greenHouseID': strat_info["greenHouseID"],
                            'active': strat_info["active"],
                            'temperature': strat_info["temperature"],
                            "humidity": strat_info["humidity"],
                            "city": greenhouse["city"]
                        }
                        break
    else:
        payload = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"],
            'active': strat_info["active"],
            'temperature': strat_info["temperature"],
            "humidity": strat_info["humidity"]
        }

    # We suppose that the managers can have just one function (regStrategy)
    url_manager = manager_info["ip"]+":"+str(manager_info["port"])+"/"+manager_info["functions"][0]
    requests.post(url_manager, json.dumps(payload))


def put_to_manager(strategyType = "", strat_info = {}):
    """
    Send a PUT message to a specific strategy manager
    in order to update the activity state of a strategy.
    """

    with open("db/catalog.json", "r") as file:
        db = json.load(file)

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
    requests.put(url, json.dumps(payload))


def delete_to_manager(strategyType = "", strat_info = {}):
    """
    Send a DELETE message to a specific strategy manager
    in order to delete a strategy.
    """
    
    with open("db/catalog.json", "r") as file:
        db = json.load(file)

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
        except:
            params = {
                'userID': strat_info["userID"], 
                'greenHouseID': strat_info["greenHouseID"]
            }
    else:
        params = {
            'userID': strat_info["userID"], 
            'greenHouseID': strat_info["greenHouseID"]
        }
        
    # We suppose that the managers can have just one function (regStrategy)
    url = manager_info["ip"]+":"+str(manager_info["port"])+"/"+manager_info["functions"][0]
    requests.delete(url, params=params)


def post_to_dev_conn(strategyType = "", strat_info = {}):
    """
    Send a POST message to a specific device connector
    in order to create a strategy.
    """
    
    with open("db/catalog.json", "r") as file:
        db = json.load(file)

    # We suppose that there is just one device connector per greenhouse (and we take just the first of the list)
    try:
        for user in db["users"]:
            if user["id"] == int(strat_info["userID"]):
                for greenhouse in user["greenHouses"]:
                    if greenhouse["greenHouseID"] == int(strat_info["greenHouseID"]):

                        dev_conn_info = greenhouse["deviceConnectors"][0]
    except:
        raise Exception("No device connector present for that user and greenhouse")
    else:
        if strategyType == "irrigation":
            payload = {
                'strategyType': "irrigation", 
                'stratID': strat_info["stratID"]
            }
        else:
            payload = {
                'strategyType': strategyType, 
            }
            
        # We suppose that the device connectors have as the first function the function to manage the strategies (regStrategy)
        url = dev_conn_info["ip"]+":"+str(dev_conn_info["port"])+"/"+dev_conn_info["functions"][0]
        requests.post(url, json.dumps(payload))


def delete_to_dev_conn(strategyType = "", strat_info = {}):
    """
    Send a DELETE message to a specific device connector
    in order to delete a strategy.
    """
    
    with open("db/catalog.json", "r") as file:
        db = json.load(file)

    # We suppose that there is just one device connector per greenhouse (and we take just the first of the list)
    try:
        for user in db["users"]:
            if user["id"] == int(strat_info["userID"]):
                for greenhouse in user["greenHouses"]:
                    if greenhouse["greenHouseID"] == int(strat_info["greenHouseID"]):

                        dev_conn_info = greenhouse["deviceConnectors"][0]
    except:
        raise Exception("No device connector present for that user and greenhouse")
    else:
        if strategyType == "irrigation":
            try:
                params = {
                    'strategyType': "irrigation", 
                    'stratID': strat_info["stratID"]
                }
            except:
                params = {
                    'strategyType': "irrigation"
                }
        else:
            params = {
                'strategyType': strategyType, 
            }
            
        # We suppose that the device connectors have as the first function the function to manage the strategies (regStrategy)
        url = dev_conn_info["ip"]+":"+str(dev_conn_info["port"])+"/"+dev_conn_info["functions"][0]
        requests.delete(url, params=params)



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
    cherrypy.tree.mount(DeviceConnectors(), '/device_connectors', conf)
    cherrypy.tree.mount(ThingSpeakAdaptor(), '/thingspeak_adaptor', conf)
    cherrypy.tree.mount(ThingSpeak(), '/thingspeak', conf)
    cherrypy.tree.mount(WebPage(), '/webpage', conf)
    cherrypy.tree.mount(WeatherAPI(), '/weatherAPI', conf)
    cherrypy.tree.mount(IrrigationManager(), '/irrigation_manager', conf)
    cherrypy.tree.mount(EnvironmentManager(), '/environment_manager', conf)
    cherrypy.tree.mount(WeatherManager(), '/weather_manager', conf)

    cherrypy.config.update({'server.socket_host': '0.0.0.0'})

    cherrypy.engine.start()
    # cherrypy.engine.block()

    with open("db/catalog.json", "r") as file:
        db = json.load(file)

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
    if len(db["users"]) > 0:
        for user in db["users"]:
            for greenhouse in user["greenHouses"]:
                for dev_conn in greenhouse["deviceConnectors"]:
                    device_connectors_list.append({
                                                    "userID": user["id"],
                                                    "greenHouseID": greenhouse["greenHouseID"],
                                                    "dev_conn": dev_conn
                                                })
    timeout_dev_connector = 120
    update = False
    
    while True:
        timestamp = time.time()
        
        if len(thingspeak_adaptors) > 0:
            for idx, adaptor in enumerate(thingspeak_adaptors):
                if timestamp - float(adaptor["timestamp"]) >= timeout_adaptor:
                    remove_from_db("thingspeak_adaptor/", idx)
                    update = True
        if len(webpages) > 0:
            for idx, webpage in enumerate(webpages):
                if timestamp - float(webpage["timestamp"]) >= timeout_webpage:
                    remove_from_db("webpage/", idx)
                    update = True
        if len(irrigation_managers) > 0:
            for idx, manager in enumerate(irrigation_managers):
                if timestamp - float(manager["timestamp"]) >= timeout_irr_manager:
                    remove_from_db("managers/irrigation", idx)
                    update = True
        if len(environment_managers) > 0:
            for idx, manager in enumerate(environment_managers):
                if timestamp - float(manager["timestamp"]) >= timeout_env_manager:
                    remove_from_db("managers/environment", idx)
                    update = True
        if len(weather_managers) > 0:
            for idx, manager in enumerate(weather_managers):
                if timestamp - float(manager["timestamp"]) >= timeout_wea_manager:
                    remove_from_db("managers/weather", idx)
                    update = True
        if len(device_connectors_list) > 0:
            for dev_conn in device_connectors_list:
                if timestamp - float(dev_conn["dev_conn"]["timestamp"]) >= timeout_dev_connector:
                    remove_from_db(str(dev_conn["userID"])+"/"+str(dev_conn["greenHouseID"])+"/"+dev_conn["dev_conn"]["ip"]+"/"+str(dev_conn["dev_conn"]["port"]))
                    update = True
            
        if update:
            time.sleep(0.5)
            with open("db/catalog.json", "r") as file:
                db = json.load(file)

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
                            device_connectors_list.append({
                                                            "userID": user["id"],
                                                            "greenHouseID": greenhouse["greenHouseID"],
                                                            "dev_conn": dev_conn
                                                        })
