#!/bin/bash
# This script deploys your application containers.
# Use:
#   --build : Rebuild images and deploy on a single host using docker compose.
#   --multi : Deploy for multi-host using docker stack deploy (requires Swarm mode).
#   (No flag): Deploy without rebuilding images (single host).

# if [[ "$1" == "--build" ]]; then
#     echo "Deployment with Building Image Steps (Single Host Mode)"
#     # Build the base image.
#     docker build -f Dockerfile.base -t demo_base_image .
#     # Generate config and module files using the config.json file passed as $2.
#     python ./tools/parser_compose.py -j "$2" -n "consul-net" # parse config.json to generate compose file?
#     python ./tools/parser_modules.py -j "$2"
#     # Copy necessary module files.
#     cp ./tools/node.py ./modules/node.py
#     cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
#     cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
#     cd modules
#     # Launch using docker compose (single host)
#     docker compose -p firstset up --remove-orphans --build  

# elif [[ "$1" == "--multi" ]]; then
#     echo "Deploying in Multi-Host Mode using docker stack deploy"
#     # In multi-host mode, we assume you have already:
#     #  1) Enabled Docker Swarm (e.g., "docker swarm init" on one host and "docker swarm join" on others)
#     #  2) Created an overlay network that all hosts share (e.g., "docker network create --driver overlay --attachable my_overlay")
#     #  3) Configured your docker-compose.yml file to use the external network (see networks section below).
    
#     # Build the base image.
#     docker build -f Dockerfile.base -t demo_base_image .
#     # Generate the application configuration files from the provided config JSON.
#     python ./tools/parser_modules.py -j "$2"
#     python ./tools/parser_compose.py -j "$2" -n "my_overlay"
#     # Copy the necessary module files.
#     cp ./tools/node.py ./modules/node.py
#     cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
#     cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
#     cd modules
#     # Deploy the application as a docker stack.
#     # This requires a Compose file (docker-compose.yml) that defines your services,
#     # and the services must reference the overlay network that spans both physical hosts.
#     docker stack deploy -c docker-compose.yml multi_app_stack
# else
#     echo "Deploying without rebuilding images (Single Host Mode)"
#     cd modules
#     docker compose up    
# fi

#!/bin/bash
# This script deploys your application containers.
# Usage:
#   --build : Rebuild images and deploy on a single host using docker compose.
#   --multi : Deploy for multi-host using docker stack deploy (requires Swarm mode).
#   (No flag): Deploy without rebuilding images (single host).

# if [[ "$1" == "--build" ]]; then
#     echo "Deployment with Building Image Steps (Single Host Mode)"
#     # Build the base image.
#     docker build -f Dockerfile.base -t demo_base_image .
#     # Generate config and module files using the config.json file passed as $2.
#     python ./tools/parser_compose.py -j "$2" -n "consul-net" --mode single
#     python ./tools/parser_modules.py -j "$2"
#     # Copy necessary module files.
#     cp ./tools/node.py ./modules/node.py
#     cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
#     cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
#     cd modules
#     # Launch using docker compose (single host)
#     docker compose -p firstset up --remove-orphans --build  

# elif [[ "$1" == "--multi" ]]; then
#     echo "Deploying in Multi-Host Mode using docker stack deploy"
#     # In multi-host mode, we assume you have already:
#     #  1) Enabled Docker Swarm ("docker swarm init" on one host and "docker swarm join" on others)
#     #  2) Created an overlay network that all hosts share (e.g., "docker network create --driver overlay --attachable my_overlay")
#     #  3) Configured your docker-compose.yml file to use the external network.
    
#     # Build the base image.
#     docker build -f Dockerfile.base -t demo_base_image .
#     # Generate the application configuration files from the provided config JSON.
#     # The parser will now generate a compose file for multi-host deployment and build images dynamically.
#     python ./tools/parser_compose.py -j "$2" -n "my_overlay" --mode multi
#     python ./tools/parser_modules.py -j "$2"
#     # Copy the necessary module files.
#     cp ./tools/node.py ./modules/node.py
#     cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
#     cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
#     cd modules
#     # Deploy the application as a Docker stack.
#     docker stack deploy -c docker-compose.yml multi_app_stack
# else
#     echo "Deploying without rebuilding images (Single Host Mode)"
#     cd modules
#     docker compose up    
# fi

#!/bin/bash
# Assume $2 is the path to config.json.

# CONFIG_JSON="$2"
# NETWORK_NAME="my_overlay"
# MODE="${1}"
# # If mode isn't provided, default to single.
# if [ -z "$MODE" ]; then
#   MODE="single"
# fi

# # Build base image (if necessary)
# docker build -f Dockerfile.base -t demo_base_image .

# # Extract module names from config.json (using jq, for example)
# MODULES=$(jq -r '.Modules[].Name' "$CONFIG_JSON")

# if [ "$MODE" == "--multi" ]; then
#   echo "Building images for multi-host deployment..."
#   python ./tools/parser_modules.py -j "$CONFIG_JSON"
#   for module in $MODULES; do
#       # Build each module image; assume Dockerfile is in ./$module and named Dockerfile.$module
#       echo "module name is" $module
#       docker build -t demo_${module}:latest -f Dockerfile.${module} ./modules/$module || exit 1
#   done
#   # Generate the compose file for multi-host mode (without build/context)
#   python ./tools/parser_compose.py -j "$CONFIG_JSON" -n "$NETWORK_NAME" --mode multi
#   # Copy necessary module files
#   cp ./tools/node.py ./modules/node.py
#   cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
#   cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
#   cd modules
#   # Deploy the application as a Docker stack.
#   docker stack deploy -c docker-compose.yml multi_app_stack
# else
#   echo "Deploying in single-host mode..."
#   # For single-host mode, the parser includes build instructions.
#   python ./tools/parser_compose.py -j "$CONFIG_JSON" -n "consul-net" --mode single
#   python ./tools/parser_modules.py -j "$CONFIG_JSON"
#   cp ./tools/node.py ./modules/node.py
#   cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
#   cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
#   cd modules
#   docker compose -p firstset up --remove-orphans --build
# fi


#!/bin/bash
# This script deploys your application containers.
# Usage:
#   --build : Rebuild images and deploy on a single host using docker compose.
#   --multi : Deploy for multi-host using docker stack deploy (requires Swarm mode).
#   (No flag): Deploy without rebuilding images (single host).

CONFIG_JSON="$2"

if [[ "$1" == "--build" ]]; then
    echo "Deployment with Building Image Steps (Single Host Mode)"
    # Build the base image.
    docker build -f Dockerfile.base -t demo_base_image .
    # Generate config and module files using the config.json file.
    python ./tools/parser_compose.py -j "$CONFIG_JSON" -n "consul-net" --mode single
    python ./tools/parser_modules.py -j "$CONFIG_JSON"
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
    #  3) Configured your docker-compose.yml file to use the external network.
    
    # Build the base image.
    docker build -f Dockerfile.base -t demo_base_image .

    docker tag demo_base_image:latest 157.159.160.197:5000/demo_base_image:latest
    docker push 157.159.160.197:5000/demo_base_image:latest
    
    # Change directory into modules so that we can build each module's image
    echo "Building images for multi-host deployment..."
    python ./tools/parser_modules.py -j "$CONFIG_JSON"
    
    cd modules || { echo "Failed to change directory to modules"; exit 1; }
    
    # Extract module names from the config.json. We assume jq is available.
    MODULES=$(jq -r '.Modules[].Name' "../$CONFIG_JSON")
    for module in $MODULES; do
        echo "Building image for module: $module"
        cp ../tools/node.py ${module}/node.py
        cp ../tools/receiveMessageHandler.py ${module}/receiveMessageHandler.py
        cp ../tools/sendMessageHandler.py ${module}/sendMessageHandler.py
        # The Dockerfile is assumed to be at ./<module>/Dockerfile.<module> and the build context is that module's directory.
        if [ -f "./${module}/Dockerfile.${module}" ]; then
            docker build -t demo_${module}:latest -f "./${module}/Dockerfile.${module}" "./${module}" || { echo "Error building image for ${module}"; exit 1; }
            docker tag demo_${module}:latest   157.159.160.197:5000/demo_${module}:latest
            docker push 157.159.160.197:5000/demo_${module}:latest
        else
            echo "Error: Dockerfile for module '${module}' not found at ./${module}/Dockerfile.${module}"
            exit 1
        fi
    done
    
    # Return to the root directory
    cd ..
    
    # Generate the Compose file in multi-host mode (this version omits build and container_name,
    # and uses image keys instead).
    python ./tools/parser_compose.py -j "$CONFIG_JSON" -n "my_overlay" --mode multi
    # Copy necessary module files.
    # cp ./tools/node.py ./modules/node.py
    # cp ./tools/receiveMessageHandler.py ./modules/receiveMessageHandler.py
    # cp ./tools/sendMessageHandler.py ./modules/sendMessageHandler.py
    cd modules
    # Deploy the application as a Docker stack.
    docker stack deploy -c docker-compose.yml multi_app_stack

else
    echo "Deploying without rebuilding images (Single Host Mode)"
    cd modules
    docker compose up    
fi

