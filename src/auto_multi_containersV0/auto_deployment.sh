#!/bin/bash

echo "---------- DOCKER AI Pipeline ----------"

if [[ "$1" == "--build" ]]; then
    echo "Deployment with Building Image Steps"
    docker build -f Dockerfile.base -t demo_base_image .
    python ./tools/parser_compose.py -j $2 # add the path to the config.json
    python ./tools/parser_modules.py -j $2
    # cp ./tools/otter_net_utils.py  ./modules/otter_net_utils.py
    cp ./tools/node.py ./modules/node.py
    cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
    cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
    cd modules
    # docker-compose down --remove-orphans
    docker compose -p firstset up --remove-orphans --build                 

else
    echo "Deploying without rebuilding images"
    cd modules
    docker compose up    

fi

