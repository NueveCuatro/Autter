# #!/bin/bash

# echo "---------- DOCKER AI Pipeline ----------"

# if [[ "$1" == "--build" ]]; then
#     echo "Deployment with Building Image Steps"
#     docker build -f Dockerfile.base -t demo_base_image .
#     python ./tools/parser_compose.py -j $2 # add the path to the config.json
#     python ./tools/parser_modules.py -j $2
#     # cp ./tools/otter_net_utils.py  ./modules/otter_net_utils.py
#     cp ./tools/node.py ./modules/node.py
#     cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
#     cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
#     cd modules
#     # docker-compose down --remove-orphans
#     docker compose -p firstset up --remove-orphans --build                 

# else
#     echo "Deploying without rebuilding images"
#     cd modules
#     docker compose up    

# fi

#!/bin/bash
# This script deploys your application containers.
# Use:
#   --build : Rebuild images and deploy on a single host using docker compose.
#   --multi : Deploy for multi-host using docker stack deploy (requires Swarm mode).
#   (No flag): Deploy without rebuilding images (single host).

if [[ "$1" == "--build" ]]; then
    echo "Deployment with Building Image Steps (Single Host Mode)"
    # Build the base image.
    docker build -f Dockerfile.base -t demo_base_image .
    # Generate config and module files using the config.json file passed as $2.
    python ./tools/parser_compose.py -j "$2" -n "consul-net" # parse config.json to generate compose file?
    python ./tools/parser_modules.py -j "$2"
    # Copy necessary module files.
    cp ./tools/node.py ./modules/node.py
    cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
    cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
    cd modules
    # Launch using docker compose (single host)
    docker compose -p firstset up --remove-orphans --build  

elif [[ "$1" == "--multi" ]]; then
    echo "Deploying in Multi-Host Mode using docker stack deploy"
    # In multi-host mode, we assume you have already:
    #  1) Enabled Docker Swarm (e.g., "docker swarm init" on one host and "docker swarm join" on others)
    #  2) Created an overlay network that all hosts share (e.g., "docker network create --driver overlay --attachable my_overlay")
    #  3) Configured your docker-compose.yml file to use the external network (see networks section below).
    
    # Build the base image.
    docker build -f Dockerfile.base -t demo_base_image .
    # Generate the application configuration files from the provided config JSON.
    python ./tools/parser_compose.py -j "$2" -n "my_overlay"
    python ./tools/parser_modules.py -j "$2"
    # Copy the necessary module files.
    cp ./tools/node.py ./modules/node.py
    cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
    cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
    cd modules
    # Deploy the application as a docker stack.
    # This requires a Compose file (docker-compose.yml) that defines your services,
    # and the services must reference the overlay network that spans both physical hosts.
    docker stack deploy -c docker-compose.yml multi_app_stack
else
    echo "Deploying without rebuilding images (Single Host Mode)"
    cd modules
    docker compose up    
fi

