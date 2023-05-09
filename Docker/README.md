TO BUILD AN IMAGE:
- docker build -t <image_name> /path/to/Dockerfile

BEFORE RUNNING THE CONTAINERS MUST BE CREATED A SUBNET TO SPECIFY IPs:
- docker network create --subnet=<ip_portion_for_the_subnet> <subnet_name>

TO RUN A CONTAINER IN A SPECIFIC SUBNET AND WITH A SPECIFIC IP:
- docker run --net <network_name> --ip <ip_number> -p <host-port>:<container-port> --name <container_name> <image_name> 

IP PORTION FOR THE SUBNET:
- 172.18.0.0/16

BINDING HOST_PORT - CONTAINER_PORT (8080)

- ResourceCatalog : 4000 (IP: 172.18.0.1)
- IrrigationManager : 4001 (IP: 172.18.0.2)
- EnvironmentManager : 4002 (IP: 172.18.0.3)
- WeatherManager : 4003 (IP: 172.18.0.4)
- DeviceConnector : 4004 (IP: 172.18.0.5)
- ThingSpeakAdaptor : 4005 (IP: 172.18.0.6)

