########################################
# PARSER for creation of Docker compose
# From a JSON CONFIG FILE
########################################
import json
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--json_file', '-j', required=True, type=str, help='Pass the config.json path')
parser.add_argument('--network', '-n', required=True, type=str, help='this argument is passed to know the network name')
args = parser.parse_args()

# Load the JSON
with open(args.json_file, 'r') as f:
    data = json.load(f)

# Dynamic ports
port_start = 5001

# Create the docker-compose.yml file (clear it if it already exists)
os.makedirs('./modules', exist_ok=True)
open('./modules/docker-compose.yml', 'w').close()

# Open the file for writing
with open('./modules/docker-compose.yml', 'w') as f:
    # File header
    f.write("###################\n")
    f.write("# Docker Compose File #\n")
    f.write("###################\n\n")
    f.write("services:\n\n")
    # f.write("  consul:\n")
    # f.write("    image: hashicorp/consul:latest\n")
    # f.write("    command: agent -dev -client=0.0.0.0\n")
    # # f.write("    command: agent -server -bootstrap-expect=1 -client=0.0.0.0 -ui -bind=0.0.0.0\n")
    # f.write("    ports:\n")
    # f.write("      - '8500:8500'\n")
    # f.write("      - '8600:8600/udp'\n")
    # f.write("    networks:\n")
    # f.write("      - test_network\n")

    for i, module in enumerate(data['Modules']):
        name = module['Name']
        service_name = f"{name}_service"
        container_name = f"{name}"
        device = module['Device']

        f.write("###############################\n")
        f.write(f"  {service_name}:\n")
        f.write(f"    build:\n")
        f.write(f"      context: ./{name}\n")
        f.write(f"      dockerfile: Dockerfile.{name}\n")
        f.write(f"    container_name: {container_name}\n")
        f.write(f"    command: [\"/bin/bash\", \"start.sh\"]\n")
        f.write(f"    volumes:\n")
        f.write(f"      - ./{name}:/app\n")
        f.write(f"      - ./node.py:/app/node.py\n")
        f.write(f"      - ./receiveMessageHandler.py:/app/receiveMessageHandler.py\n")
        f.write(f"      - ./sendMessageHandler.py:/app/sendMessageHandler.py\n")
        f.write(f"    ports:\n")
        f.write(f"      - \"{port_start}:5000\"  # Maps port 5000 inside the container to port {port_start} on the host for incoming connections \n") 
        # f.write(f"      - \"{port_start+1}:5001\"  # Maps port 5000 inside the container to port {port_start} on the host for outgoing connections \n")
        f.write(f"    networks:\n")
        f.write(f"      - consul-net\n")

        # ➡️ If the module uses a GPU, add the deployment configuration
        if device == "GPU":
            f.write(f"    deploy:\n")
            f.write(f"      resources:\n")
            f.write(f"        reservations:\n")
            f.write(f"          devices:\n")
            f.write(f"            - capabilities: [\"gpu\"]\n")

        # ➡️ If the module is **even (client)**, add `depends_on`
        # if i % 2 == 1:
        #     f.write(f"    depends_on: # Start Client after Server\n")
        #     f.write(f"      - {data['Modules'][i - 1]['Name']}_service\n")

        #     # ➡️ If it's **not the last module**, it also depends on the next one
        #     if i + 1 < len(data['Modules']):
        #         f.write(f"      - {data['Modules'][i + 1]['Name']}_service\n")

        f.write("\n")
        port_start += 1

    f.write("###############################\n")

    # ➡️ Network configuration
    f.write("networks:\n")
    f.write(f"   {args.network}:\n")
    f.write("     external: true\n")
    # f.write("     driver: bridge\n")

# Confirmation
print("✅ docker-compose.yml file generated successfully!")
