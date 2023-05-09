TO BUILD AN IMAGE:
- docker build -t <image_name> /path/to/Dockerfile

ONCE THE IMAGE IS BUILT RUN THE CONTAINER AND BIND THE PORT TO WHICH THE SCRIPT INSIDE THE CONTAINER IS LISTENING WITH A PORT OF THE HOST:
- docker run -p <host-port>:<container-port> --name <container_name> <image_name> 

THE REST SERVICES WILL BE AVAILABLE ON LOCALHOST, BUT AT THE <host-port> SPECIFIED BEFORE

IN THE SCRIPTS THE ENDPOINTS EXPOSED FOR THE REST API REAMINS: IP "127.0.0.1", PORT "8080"

BINDING PORT-SCRIPT

- ResourceCatalog : 4000
- IrrigationManager : 4001
- EnvironmentManager : 4002
- WeatherManager : 4003
- DeviceConnector : 4004
- ThingSpeakAdaptor : 4005

