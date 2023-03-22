Before running any container must be created a CUSTOM NETWORK:

docker network create --subnet=172.18.0.0/16 my_network

subnet indicates the range of IPs that are allowe inside this network (te IP addess must be a free private one)


To build an image:

docker build -t <image_name> /path/to/Dockerfile


Once the image is built run the container with the IP chosen for the REST services and bind the port to which the script inside the container is listening with a port of the host:

docker run --ip 172.18.0.1 -p <host-port>:<container-port> <image_name>

