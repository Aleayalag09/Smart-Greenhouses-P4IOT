import json
import cherrypy
import time

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
        
            for user in users:
                if user['id'] == int(id):
                    return json.dumps(user, indent=3)
                
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
            "id": users[len(users)-1]['id'] + 1,
            "name": "name",
            "surname": "surname",
            "email_addresses": "email",
            "country": "country",
            "city": "city",
            "MQTTBaseTopic": "baseTopic",
            "greenHouses": [],
            "timestamp": time.time()
        }
        input = json.loads(cherrypy.request.body.read())
        try:
            new_user["userName"] = input['userName']
            new_user["password"] = input['password']
            new_user["name"] = input['name']
            new_user["surname"] = input['surname']
            new_user["email_addresses"] = input['email_addresses']
            new_user["country"] = input['country']
            new_user["city"] = input['city']
            new_user["MQTTBaseTopic"] = input['MQTTBaseTopic']
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
                output = str(type(user))+"<br>"+str(user)
                users.pop(idx)
                db["users"] = users
                json.dump(db, open("src/db/catalog.json", "w"), indent=3)
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
        
        userPres = False
        userNum = 0
        for user in users:
            if user['id'] == id:
                userPres = True
                if len(user['greenHouses']) == 0:
                    greenHouseID = 0
                else:
                    greenHouseID = user['greenHouses'][len(user['greenHouses'])-1]['greenHouseID'] + 1
                break
            userNum += 1

        if userPres:
            strat_dict = {
                "strat": [],
                "active": False,
                "timestamp": -1
            }
            
            new_greenhouse = {
                "greenHouseName": "greenHouseName",
                "greenHouseID": greenHouseID,
                "city": "city",
                "deviceConnector": {},
                "strategies": {"irrigation": strat_dict, "environment": strat_dict, "windows": strat_dict}
                }
            
            input = json.loads(cherrypy.request.body.read())
            try:
                new_greenhouse["greenHouseName"] = input['greenHouseName']
                new_greenhouse["city"] = input['city']
            except:
                raise cherrypy.HTTPError(400, 'Wrong parameter')
            else:
                users[userNum]['greenHouses'].append(new_greenhouse)
                users[userNum]["timestamp"] = time.time()
                db["users"] = users
                json.dump(db, open("src/db/catalog.json", "w"), indent=3)
                output=str(type(input))+"<br>"+str(input)
                return output
        else:
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
            
        key_not_allowed = ["greenHouseID","deviceConnector", "strategies"]
        
        keys = list(set(keys_to_change)-set(key_not_allowed))
        
        if not keys:
            raise cherrypy.HTTPError(400, 'No value to change found')
        
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
        
        for user in users:
            if user['id'] == int(id):
                for idx, greenHouse in enumerate(user['greenHouses']):
                    if greenHouse['greenHouseID'] == int(greenHouseID):
                        output = str(type(greenHouse))+"<br>"+str(greenHouse)
                        user['greenHouses'].pop(idx)
                        user["timestamp"] = time.time()
                        db["users"] = users
                        json.dump(db, open("src/db/catalog.json", "w"), indent=3)
                        return output
                    
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')

class Strategy(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get a specific strategy (Irrigation, Environment, Windows) or all the strategies from a device.
        """
        db = json.load(open("src/db/catalog.json", "r"))
        users = db["users"]
        
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            strategyType = queries['strategyType']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        else:
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
                            
                
        raise cherrypy.HTTPError(400, 'No user, greenhouse or strategy found')
                        
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
            for user in users:
                if user['id'] == int(id):
                    for greenhouse in user['greenHouses']:
                        if greenhouse['greenHouseID'] == int(greenHouseID):
                            if len(greenhouse['strategies']['irrigation']['strat']) == 0:
                                strategyID = 0
                            else:                           
                                strategyID = greenhouse['strategies']['irrigation']['strat'][len(greenhouse['strategies']['irrigation']['strat'])-1]['id'] + 1

                            try: 
                                stime = input["time"]
                                water_quantity = input["water_quantity"]
                                activeStrat = input["activeStrat"]
                                activeIrr = input["activeIrr"]
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
                                greenhouse['strategies']['irrigation']['active'] = activeIrr
                                greenhouse['strategies']['irrigation']['timestamp'] = time.time()

                                user['timestamp'] = time.time()
                                db["users"] = users
                                json.dump(db, open("src/db/catalog.json", "w"), indent=3)
                                output=str(type(input))+"<br>"+str(input)
                                return output

        elif strategyType == "environment" or strategyType == "windows":   
            for user in users:
                if user['id'] == int(id):
                    for greenhouse in user['greenHouses']:
                        if greenhouse['greenHouseID'] == int(greenHouseID):

                            if strategyType == "environment":
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

                                    greenhouse['strategies']['environment']["strat"] = new_strat
                                    greenhouse['strategies']['environment']['active'] = active
                                    greenhouse['strategies']['environment']['timestamp'] = time.time()

                            elif strategyType == "windows":
                                try:
                                    active = input["input"]
                                except:
                                    raise cherrypy.HTTPError(400, 'Wrong parameters')
                                else:
                                    greenhouse['strategies']['windows']['active'] = active
                                    greenhouse['strategies']['windows']['timestamp'] = time.time()
                            
                            user['timestamp'] = time.time()
                            db["users"] = users
                            json.dump(db, open("src/db/catalog.json", "w"), indent=3)
                            output=str(type(input))+"<br>"+str(input)
                            return output
                        
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

        for user in users:
            if user['id'] == int(id):
                for greenhouse in user['greenHouses']:
                    if greenhouse['greenHouseID'] == int(greenHouseID):
                        
                        if strategyType == "irrigation":
                            try:
                                input = json.loads(cherrypy.request.body.read())
                                strategyID = int(input["strategyID"])
                                activeStrat = input["activeStrat"]
                            except:
                                pass
                            else:
                                greenhouse['strategies']['irrigation']["strat"][strategyID]['active'] = activeStrat

                        try:
                            greenhouse['strategies'][strategyType]["active"] = active
                            greenhouse['strategies'][strategyType]["timestamp"] = time.time()
                        except:
                            raise cherrypy.HTTPError(400, 'Wrong strategy type')
                        else:
                            user["timestamp"] = time.time()
                            db["users"] = users
                            json.dump(db, open("src/db/catalog.json", "w"), indent=3)
                            output = str(type(user))+"<br>"+str(user)
                            return output
            
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
    
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
                                json.dump(users, open("src/db/catalog.json", "w"), indent=3)
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
                                            greenhouse['strategies']['irrigation']['strat'][i]["id"] -= 1

                                    greenhouse['strategies']['irrigation']['strat'].pop(strategyID)
                                    greenhouse['strategies']['irrigation']["timestamp"] = time.time()
                                    user["timestamp"] = time.time()
                                    db["users"] = users
                                    json.dump(users, open("src/db/catalog.json", "w"), indent=3)
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
                                json.dump(users, open("src/db/catalog.json", "w"), indent=3)
                                output = str(type(user))+"<br>"+str(user)
                                return output
                    
        raise cherrypy.HTTPError(400, 'No user, greenhouse or strategy found')

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

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()