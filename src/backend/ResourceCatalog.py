import json
import cherrypy
import time

class UserManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get an especific user or all the users, each user will be call by his id
        """
        users = json.load(open("src/db/catalog.json", "r"))
        
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
        users = json.load(open("src/db/catalog.json", "r"))
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
            json.dump(users, open("src/db/catalog.json", "w"), indent=3)
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
        
        users = json.load(open("src/db/catalog.json", "r"))
        
        keys_to_change = input.keys()
            
        key_not_allowed = ["id","super_User","greenHouses","timestamp"]
        
        keys = list(set(keys_to_change)-set(key_not_allowed))
        
        if not keys:
            raise cherrypy.HTTPError(400, 'Not value to change found')
        
        for user in users:
            if user['id'] == int(id):
                for key in keys:
                    try:
                        user[key] = type(user[key])(input[key])
                    except:
                        raise cherrypy.HTTPError(400, 'No valid key')
                    user["timestamp"] = time.time()
                    json.dump(users, open("src/db/catalog.json", "w"), indent=3)
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
        
        users = json.load(open("src/db/catalog.json", "r"))
        
        for idx, user in enumerate(users):
            if user['id'] == int(id):
                output = str(type(user))+"<br>"+str(user)
                users.pop(idx)
                json.dump(users, open("src/db/catalog.json", "w"), indent=3)
                return output
            
        raise cherrypy.HTTPError(400, 'No user found')
    
class GreenHouseManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get an especific greenhouse or all the greenhouses from an user.
        """
        users = json.load(open("src/db/catalog.json", "r"))
        
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
        This function create a new greenhouse
        """
        users = json.load(open("src/db/catalog.json", "r"))
        try:
            id = queries['id']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        for user in users:
            if user['id'] == int(id):
                if len(user['greenHouses']) == 0:
                    greenHouseID = 0
                else:
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
            json.dump(users, open("src/db/catalog.json", "w"), indent=3)
            output=str(type(input))+"<br>"+str(input)
            return output
            
    @cherrypy.tools.json_in()
    def PUT(self, *path, **queries): 
        """
        This function modify the information of the greenhouse
        """
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        input = cherrypy.request.json
        
        users = json.load(open("src/db/catalog.json", "r"))
        
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
                            try:
                                greenHouse[key] = type(greenHouse[key])(input[key])
                            except:
                                raise cherrypy.HTTPError(400, 'No valid key')
                            user["timestamp"] = time.time()
                            json.dump(users, open("src/db/catalog.json", "w"), indent=3)
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
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        users = json.load(open("src/db/catalog.json", "r"))
        
        for user in users:
            if user['id'] == int(id):
                for idx, greenHouse in enumerate(user['greenHouses']):
                    if greenHouse['greenHouseID'] == int(greenHouseID):
                        output = str(type(greenHouse))+"<br>"+str(greenHouse)
                        user['greenHouses'].pop(idx)
                        json.dump(users, open("src/db/catalog.json", "w"), indent=3)
                        return output
                    
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')

class DeviceManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get an especific device or all the devices from a greenhouse.
        """
        users = json.load(open("src/db/catalog.json", "r"))
        
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            deviceID = queries['deviceID']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        else:
            if queries['deviceID']== "all":
                for user in users:
                    if user['id'] == int(id):
                        for greenhouse in user['greenHouses']:
                            if greenhouse['greenHouseID'] == int(greenHouseID):
                                 return json.dumps(greenhouse['devicesList'], indent=3)
                        
            for user in users:
                if user['id'] == int(id):
                    for greenhouse in user['greenHouses']:
                        if greenhouse['greenHouseID'] == int(greenHouseID):
                            for device in greenhouse['devicesList']:
                                if device['deviceID'] == int(deviceID):
                                    return json.dumps(device, indent=3)
                            
                
        raise cherrypy.HTTPError(400, 'No user, greenhouse or device found')
                        
    
    @cherrypy.tools.json_in()
    def POST(self, *path, **queries):
        """
        This function create a new device
        """
        users = json.load(open("src/db/catalog.json", "r"))
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        for user in users:
            if user['id'] == int(id):
                for greenhouse in user['greenHouses']:
                    if greenhouse['greenHouseID'] == int(greenHouseID):
                        if len(greenhouse['devicesList']) == 0:
                            deviceID = 0
                        else:                           
                            deviceID = greenhouse['devicesList'][len(greenhouse['devicesList'])-1]['deviceID'] + 1
                        device_path = '/' + str(user['id']) + '/' + str(greenhouse['greenHouseID']) + '/' + str(deviceID)
                        break
                    
        
        
        new_device = {
            "deviceName": "deviceName",
            "deviceID": deviceID,
            "measureTypes": [],
            "availableServices": [],
            "servicesDetails" : [],
            "strategies": [],
            "lastUpdate" : time.time()
            }
        
        servicesDetails = [{"serviceType": "MQTT",
                                    "serviceIP": "mqtt.eclipse.org",
                                    "port" : "1883",
                                    "topic": "Smart_GreenHouses_P4IOT" + device_path},
                                 
                                 {"serviceType": "REST",
                                    "serviceIP": "127.0.0.1",
                                    "port" : "8080",
                                    "path": device_path}]
        
        input = cherrypy.request.json
        try:
            new_device["deviceName"] = input['deviceName']
            new_device["measureTypes"] = input['measureTypes']
            new_device["availableServices"] = input['availableServices']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect parameter')
        else:
            for availableService in new_device["availableServices"]:
                for service in servicesDetails:
                    if service['serviceType'] == availableService:
                        new_device["servicesDetails"].append(service)

            greenhouse['devicesList'].append(new_device)
            user["timestamp"] = time.time()
            json.dump(users, open("src/db/catalog.json", "w"), indent=3)
            output=str(type(input))+"<br>"+str(input)
            return output
            
    @cherrypy.tools.json_in()
    def PUT(self, *path, **queries): 
        """
        This function modify the information of the device
        """
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            deviceID = queries['deviceID']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        input = cherrypy.request.json
        
        users = json.load(open("src/db/catalog.json", "r"))
        
        keys_to_change = input.keys()
        
        if path[0] == 'servicesDetails':
            key_not_allowed = ["serviceType","topic","path"]
            keys = list(set(keys_to_change)-set(key_not_allowed))
        else:
            key_not_allowed = ["deviceID", "servicesDetails","lastUpdate","strategies"]
            keys = list(set(keys_to_change)-set(key_not_allowed))
        
        if not keys:
            raise cherrypy.HTTPError(400, 'Not value to change found')
        
        for user in users:
            if user['id'] == int(id):
                for greenHouse in user['greenHouses']:
                    if greenHouse['greenHouseID'] == int(greenHouseID):
                        for device in greenHouse['devicesList']:
                            if device["deviceID"] == int(deviceID):
                                if path[0] == 'servicesDetails':
                                    for servicesDetail in device['servicesDetails']:
                                        if servicesDetail['serviceType'] == path[1]:
                                            for key in keys:
                                                try:
                                                    servicesDetail[key] = type(servicesDetail[key])(input[key])
                                                except:
                                                    raise cherrypy.HTTPError(400, 'No valid key')
                                else:
                                    for key in keys:
                                        try:
                                            device[key] = type(device[key])(input[key])
                                        except:
                                            raise cherrypy.HTTPError(400, 'No valid key')
                                            
                                        user["timestamp"] = time.time()
                                        json.dump(users, open("src/db/catalog.json", "w"), indent=3)
                                        output = str(type(user))+"<br>"+str(user)
                                        return output
            
        raise cherrypy.HTTPError(400, 'No user or greenhouse found')
    
    def DELETE(self, *path, **queries):
        """
        This function delete a device
        """
        
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            deviceID = queries['deviceID']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        users = json.load(open("src/db/catalog.json", "r"))
        
        for user in users:
            if user['id'] == int(id):
                for greenHouse in user['greenHouses']:
                    if greenHouse['greenHouseID'] == int(greenHouseID):
                        for idx, device in enumerate(greenHouse['devicesList']):
                            if device['deviceID'] == int(deviceID):
                                output = str(type(device))+"<br>"+str(device)
                                greenHouse['devicesList'].pop(idx)
                                json.dump(users, open("src/db/catalog.json", "w"), indent=3)
                                return output
                    
        raise cherrypy.HTTPError(400, 'No user, greenhouse or device found')

class StrategiesManager(object):
    exposed = True

    def GET(self, *path, **queries):
        """
        Function that get an especific strategy or all the strategies from a device.
        """
        users = json.load(open("src/db/catalog.json", "r"))
        
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            deviceID = queries['deviceID']
            strategyID = queries['strategyID']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        else:
            if queries['strategyID']== "all":
                for user in users:
                    if user['id'] == int(id):
                        for greenhouse in user['greenHouses']:
                            if greenhouse['greenHouseID'] == int(greenHouseID):
                                for device in greenhouse['devicesList']:
                                    if device['deviceID'] == int(deviceID):
                                        return json.dumps(device['strategies'], indent=3)
                        
            for user in users:
                if user['id'] == int(id):
                    for greenhouse in user['greenHouses']:
                        if greenhouse['greenHouseID'] == int(greenHouseID):
                            for device in greenhouse['devicesList']:
                                if device['deviceID'] == int(deviceID):
                                    for strategy in device['strategies']:
                                        if strategy["strategyID"] == int(strategyID):
                                            return json.dumps(strategy, indent=3)
                            
                
        raise cherrypy.HTTPError(400, 'No user, greenhouse, device or strategy found')
                        
    
    @cherrypy.tools.json_in()
    def POST(self, *path, **queries):
        """
        This function create a new strategy
        """
        users = json.load(open("src/db/catalog.json", "r"))
        try:
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            deviceID = queries['deviceID']
        
        except:
            raise cherrypy.HTTPError(400, 'Bad request')
        
        for user in users:
            if user['id'] == int(id):
                for greenhouse in user['greenHouses']:
                    if greenhouse['greenHouseID'] == int(greenHouseID):
                        for device in greenhouse['devicesList']:
                            if device['deviceID'] == int(deviceID):
                                if len(device['strategies']) == 0:
                                    strategyID = 0
                                else:                           
                                    strategyID = device['strategies'][len(device['strategies'])-1]['strategyID'] + 1
                                break   
                
        new_strategy = {
            "strategyID": strategyID,
            "time" : "00:00:00",
            "water_quantity": 0,
            "duration" : 0
            }
        
        for measure in device["measureTypes"]:
            new_strategy.update({measure : 0})
     
        keys = list(set(new_strategy.keys())-set(["strategyID"]))
        input = cherrypy.request.json
        try:
            for key in keys:   
                new_strategy[key] = input[key]
        except:
            raise cherrypy.HTTPError(400, 'Incorrect parameter')
        else:
            device['strategies'].append(new_strategy)
            user["timestamp"] = time.time()
            json.dump(users, open("src/db/catalog.json", "w"), indent=3)
            output=str(type(input))+"<br>"+str(input)
            return output
            
    @cherrypy.tools.json_in()
    def PUT(self, *path, **queries): 
        """
        This function modify a strategy
        """
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            deviceID = queries['deviceID']
            strategyID = queries['strategyID']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        input = cherrypy.request.json
        
        users = json.load(open("src/db/catalog.json", "r"))
        
        keys_to_change = input.keys()
            
        key_not_allowed = ["strategyID"]
        
        keys = list(set(keys_to_change)-set(key_not_allowed))
        
        if not keys:
            raise cherrypy.HTTPError(400, 'Not value to change found')
        
        for user in users:
            if user['id'] == int(id):
                for greenHouse in user['greenHouses']:
                    if greenHouse['greenHouseID'] == int(greenHouseID):
                        for device in greenHouse['devicesList']:
                            if device["deviceID"] == int(deviceID):
                                for strategy in device['strategies']:
                                    if strategy['strategyID'] == int(strategyID):
                                        for key in keys:
                                            try:
                                                strategy[key] = type(strategy[key])(input[key])
                                            except:
                                                raise cherrypy.HTTPError(400, 'No valid key')
                                            
                                            user["timestamp"] = time.time()
                                            json.dump(users, open("src/db/catalog.json", "w"), indent=3)
                                            output = str(type(user))+"<br>"+str(user)
                                            return output
            
        raise cherrypy.HTTPError(400, 'No user, greenhouse, device or strategy found')
    
    def DELETE(self, *path, **queries):
        """
        This function delete a strategy
        """
        
        try: 
            id = queries['id']
            greenHouseID = queries['greenHouseID']
            deviceID = queries['deviceID']
            strategyID = queries['strategyID']
        except:
            raise cherrypy.HTTPError(400, 'Incorrect id')
        
        users = json.load(open("src/db/catalog.json", "r"))
        
        for user in users:
            if user['id'] == int(id):
                for greenHouse in user['greenHouses']:
                    if greenHouse['greenHouseID'] == int(greenHouseID):
                        for device in (greenHouse['devicesList']):
                            if device['deviceID'] == int(deviceID):
                                for idx, strategy in enumerate(device['strategies']):
                                    if strategy['strategyID'] == int(strategyID):
                                        output = str(type(strategy))+"<br>"+str(strategy)
                                        device['strategies'].pop(idx)
                                        json.dump(users, open("src/db/catalog.json", "w"), indent=3)
                                        return output
                    
        raise cherrypy.HTTPError(400, 'No user, greenhouse, device or strategy found')

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
    cherrypy.tree.mount(StrategiesManager(), '/strategy_manager', conf)

    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    cherrypy.config.update({'server.socket_port': 8080})

    cherrypy.engine.start()
    cherrypy.engine.block()