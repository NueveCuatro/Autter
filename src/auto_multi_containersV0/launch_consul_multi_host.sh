#!/bin/bash
#
# swarm_init.sh – Initialize or join a Docker Swarm and deploy Consul.
#
# Usage:
#   As manager: ./swarm_init.sh manager
#   As worker : ./swarm_init.sh worker MANAGER_IP
#
# Requirements:
#   - Docker must be installed.
#   - For workers, the environment variable WORKER_JOIN_TOKEN must be set
#     (this token is obtained on the manager via: docker swarm join-token worker).
#
# The script does the following:
#   1. If running as manager:
#         - Initializes Swarm mode.
#         - Creates an overlay network (if it doesn't already exist).
#         - Deploys a Consul stack (using docker stack deploy) with a compose file 
#           (compose-consul-multi-host.yml).
#   2. If running as worker:
#         - Joins the swarm using the provided MANAGER_IP and WORKER_JOIN_TOKEN.
#         - Checks for the overlay network.
#
# Notes on Consul Deployment:
#   For multi-host setups, it’s best practice to deploy a Consul cluster.
#   In the provided compose-consul-multi-host.yml file (not shown here), you should
#   define a service for Consul with multiple replicas (for example, a replica per host).
#   This creates a Consul cluster so that each node participates in service discovery.
#
#   Alternatively, you can deploy a single Consul container on the manager and run a
#   Consul agent (client) on each worker that registers with that server—but this is less
#   fault-tolerant. The example below assumes you want to run a multi-node Consul cluster.
#

# Check if proper argument(s) are provided.
if [ -z "$1" ]; then
    echo "[SCRIPT] Usage: $0 manager|worker [MANAGER_IP]"
    exit 1
fi

ROLE=$1

if [ "$ROLE" == "manager" ]; then
    echo "[SCRIPT] Initializing Docker Swarm on manager node..."
    docker swarm init --advertise-addr 157.159.160.197 #2001:660:3203:1600:79f9:db51:2ef1:faa2
    # Get the manager's advertise address (it’s used for joining workers)
    MANAGER_ADDR=$(docker info -f '{{.Swarm.NodeAddr}}')
    echo "[SCRIPT] Swarm manager initialized at: $MANAGER_ADDR"

    echo "[SCRIPT] Creating overlay network 'my_overlay' if it doesn't exist..."
    # Check for the network and create it if necessary.
    if ! docker network ls | grep -q my_overlay ; then
        docker network create --driver overlay --attachable my_overlay
        echo "[SCRIPT] Overlay network 'my_overlay' created."
    else
        echo "[SCRIPT] Overlay network 'my_overlay' already exists."
    fi

    echo "[SCRIPT] Deploying Consul stack..."
    # This assumes you have a file named compose-consul-multi-host.yml in the current directory.
    # The Compose file should set up Consul in server mode (with for instance replica constraints).
    docker stack deploy -c docker-compose-consul-multi-host.yml consul_stack
    echo "[SCRIPT] Consul stack deployed. Workers can join the swarm and they will see the Consul cluster."
    echo "[SCRIPT] Reach consol UI at https://157.159.160.197:8500/ui

elif [ "$ROLE" == "worker" ]; then
    # Check that the manager IP is provided
    if [ -z "$2" ]; then
        echo "[SCRIPT] Usage for worker: $0 worker MANAGER_IP"
        exit 1
    fi
    MANAGER_IP=$2
    echo "[SCRIPT] Joining Docker Swarm as worker. Manager IP: $MANAGER_IP"
    
    # Check that the join token has been provided in the environment.
    if [ -z "$WORKER_JOIN_TOKEN" ]; then
        echo "[SCRIPT] Error: Environment variable WORKER_JOIN_TOKEN is not set."
        echo "[SCRIPT] Obtain it on the manager node with: docker swarm join-token worker"
        exit 1
    fi

    docker swarm join --token $WORKER_JOIN_TOKEN $MANAGER_IP:2377
    echo "[SCRIPT] Successfully joined the swarm as a worker."

    # On worker nodes, the overlay network 'my_overlay' is created by the manager.
    # Verify that this network exists on this node.
    if docker network ls | grep -q my_overlay ; then
        echo "[SCRIPT] Overlay network 'my_overlay' is available."
    else
        echo "[SCRIPT] Warning: Overlay network 'my_overlay' not found. Ensure the manager created it."
    fi

    echo "[SCRIPT] Note: The Consul stack is managed by the swarm manager. Workers will participate in it via the overlay network."

else
    echo "[SCRIPT] Usage: $0 manager|worker [MANAGER_IP]"
    exit 1
fi

