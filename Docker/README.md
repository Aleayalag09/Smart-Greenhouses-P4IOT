- To build an image:
    - docker build -t <image_name> /path/to/Dockerfile


- Once the image is built run the container and bind the port to which the script inside the container is listening with a port of the host:
    - docker run -p <host-port>:<container-port> --name <container_name> <image_name> 

- The rest services will be available on localhost, but at the <host-port> specified before
- In the scripts the endpoints exposed for the rest API remain: IP _localhost_ and PORT _8080_

BINDING PORT-SCRIPT

- ResourceCatalog : 4000
- IrrigationManager : 4001
- EnvironmentManager : 4002
- WeatherManager : 4003
- DeviceConnector : 4004
- ThingSpeakAdaptor : 4005

