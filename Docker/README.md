# HOW TO RUN THE NETWORK WITH DOCKER CONTAINERS

Firstly you need to install Docker, then you must create a Docker network: <docker network create smart_greenhouse>
"smart_greenhouse" is the name of the custom network used in "docker-compose.yml".

To run all the elements of the network you can use the file "docker-compose.yml": from the command line in the directory "Docker" write <docker-compose up --build> and it automatically creates images and runs containers.

To run different elements you must write a new docker compose file with less "services".

For each of the scripts the exposed port will be 8080 but it is binded with a port of the local system (see "docker-compose.yml").
To contact the web interface of another script inside a container the IP and PORT will be:
- IP: <container_name> (e.g. resource_catalog)
- PORT: 8080

To open Node-Red you must go to your browser and digit:
- <127.0.0.1> to see the the development page
- <127.0.0.1/ui> to see the web page

If you make changes to the scripts after you already launched <docker-compose up --build> you must first delete containers and images and then launch again the same comand in order to "apply" the changes

Terminal code sequence (after Docker installation and opening):

(once)
- <docker network create smart_greenhouse> 
(each time)
- <docker compose up --build>
- <cntrl+c> to stop the containers (to delete them go to your Docker desktop or delete them from the terminal)

