# HOW TO RUN THE NETWORK WITH DOCKER CONTAINERS

Firstly you need to install Docker, then you must create a Docker network: <docker network create smart_greenhouse>
"smart_greenhouse" is the name of the custom network used in "docker-compose.yml".

To run all the elements of the network you can use the file "docker-compose.yml": from the command line in the directory "Docker" write <docker-compose up> and it automatically creates images and runs containers.
To run different elements you must write a new docker compose file with less "services".

For each of the scripts the exposed port will be 8080 but it is binded with a port of the local system (see "docker-compose.yml").
To contact the web interface of another script inside a container the IP and PORT will be:
- IP: <container_name> (e.g. resource_catalog)
- PORT: 8080
