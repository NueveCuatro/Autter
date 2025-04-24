# ########################################
# # PARSER for creation of Docker compose
# # From a JSON CONFIG FILE
# ########################################
# import json
# import os
# import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument('--json_file', '-j', required=True, type=str, help='Pass the config.json path')
# parser.add_argument('--network', '-n', required=True, type=str, help='this argument is passed to know the network name')
# args = parser.parse_args()

# # Load the JSON
# with open(args.json_file, 'r') as f:
#     data = json.load(f)

# # Dynamic ports
# port_start = 5001

# # Create the docker-compose.yml file (clear it if it already exists)
# # os.makedirs('./modules', exist_ok=True)
# open('./modules/docker-compose.yml', 'w').close()

# # Open the file for writing
# with open('./modules/docker-compose.yml', 'w') as f:
#     # File header
#     f.write("###################\n")
#     f.write("# Docker Compose File #\n")
#     f.write("###################\n\n")
#     f.write("services:\n\n")
#     # f.write("  consul:\n")
#     # f.write("    image: hashicorp/consul:latest\n")
#     # f.write("    command: agent -dev -client=0.0.0.0\n")
#     # # f.write("    command: agent -server -bootstrap-expect=1 -client=0.0.0.0 -ui -bind=0.0.0.0\n")
#     # f.write("    ports:\n")
#     # f.write("      - '8500:8500'\n")
#     # f.write("      - '8600:8600/udp'\n")
#     # f.write("    networks:\n")
#     # f.write("      - test_network\n")

#     for i, module in enumerate(data['Modules']):
#         name = module['Name']
#         service_name = f"{name}_service"
#         container_name = f"{name}"
#         device = module['Device']

#         f.write("###############################\n")
#         f.write(f"  {service_name}:\n")
#         f.write(f"    build:\n")
#         f.write(f"      context: ./{name}\n")
#         f.write(f"      dockerfile: Dockerfile.{name}\n")
#         f.write(f"    container_name: {container_name}\n")
#         f.write(f"    command: [\"/bin/bash\", \"start.sh\"]\n")
#         f.write(f"    volumes:\n")
#         f.write(f"      - ./{name}:/app\n")
#         f.write(f"      - ./node.py:/app/node.py\n")
#         f.write(f"      - ./receiveMessageHandler.py:/app/receiveMessageHandler.py\n")
#         f.write(f"      - ./sendMessageHandler.py:/app/sendMessageHandler.py\n")
#         f.write(f"    ports:\n")
#         f.write(f"      - \"{port_start}:5000\"  # Maps port 5000 inside the container to port {port_start} on the host for incoming connections \n") 
#         # f.write(f"      - \"{port_start+1}:5001\"  # Maps port 5000 inside the container to port {port_start} on the host for outgoing connections \n")
#         f.write(f"    networks:\n")
#         f.write(f"      - {args.network}\n")

#         # ➡️ If the module uses a GPU, add the deployment configuration
#         if device == "GPU":
#             f.write(f"    deploy:\n")
#             f.write(f"      resources:\n")
#             f.write(f"        reservations:\n")
#             f.write(f"          devices:\n")
#             f.write(f"            - capabilities: [\"gpu\"]\n")

#         # ➡️ If the module is **even (client)**, add `depends_on`
#         # if i % 2 == 1:
#         #     f.write(f"    depends_on: # Start Client after Server\n")
#         #     f.write(f"      - {data['Modules'][i - 1]['Name']}_service\n")

#         #     # ➡️ If it's **not the last module**, it also depends on the next one
#         #     if i + 1 < len(data['Modules']):
#         #         f.write(f"      - {data['Modules'][i + 1]['Name']}_service\n")

#         f.write("\n")
#         port_start += 1

#     f.write("###############################\n")

#     # ➡️ Network configuration
#     f.write("networks:\n")
#     f.write(f"    {args.network}:\n")
#     f.write("      external: true\n")
#     # f.write("     driver: bridge\n")

# # Confirmation
# print("✅ docker-compose.yml file generated successfully!")


#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import yaml

def build_image(module_name):
    """
    Build the Docker image for a module using its Dockerfile.
    Assumes:
      - The build context is in "./<module_name>"
      - The Dockerfile is named "Dockerfile.<module_name>"
    Returns the image name (e.g., "demo_c1:latest").
    """
    context = f"./modules/{module_name}"
    dockerfile = f"Dockerfile.{module_name}"
    image_name = f"demo_{module_name}:latest"
    cmd = ["docker", "build", "-t", image_name, "-f", dockerfile, context]
    print(f"Building image for module '{module_name}' with command: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print(f"✅ Successfully built image: {image_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error building image for module '{module_name}': {e}", file=sys.stderr)
        sys.exit(1)
    return image_name

def generate_compose(config, network_name, mode):
    """
    Generate a Docker Compose configuration dictionary from the given JSON config.
    
    :param config: Parsed JSON configuration.
    :param network_name: Name of the external network to use.
    :param mode: "single" for local deployment (docker compose up) or "multi" for swarm (docker stack deploy).
    :return: A dictionary representing the docker-compose.yml content.
    """
    services = {}
    volumes = {}
    modules = config.get("Modules", [])
    for i, module in enumerate(modules):
        module_name = module.get("Name")
        service_name = f"{module_name}_service"
        module_placement = module.get("Deploy_to", "manager")
        service_def = {}
        
        
        # Volumes: Mount the module folder and shared files.
        
        # Ports: Map container port 5000 to a host port derived from index (e.g., 5001, 5002, etc.).
        host_port = 5000 + (i + 1)
        service_def["ports"] = [f"{host_port}:5000"]
        
        # Networks: Attach to the given network.
        service_def["networks"] = [network_name]
        
        # Set environment variables (based on config values).
        env_vars = {
            "MODULE_NAME": module_name,
            "DEVICE": module.get("Device", ""),
            "ROLE": module.get("Role", ""),
            "SEND_TO": ",".join(module.get("Send_to", [])),
            "SERVICE_NAME": f'multi_app_stack_{module_name}_service',
            "CONSUL_URL" : "http://consul:8500"
        }
        service_def["environment"] = env_vars
        
        # For single-host mode, include build and container_name keys.
        if mode == "single":
            # Set the command common to both modes.
            service_def["command"] = ["/bin/bash", "start.sh"]

            service_def["volumes"] = [
                f"./{module_name}:/app",
                "./node.py:/app/node.py",
                "./receiveMessageHandler.py:/app/receiveMessageHandler.py",
                "./sendMessageHandler.py:/app/sendMessageHandler.py"
            ]
            
            service_def["build"] = {
                "context": f"./{module_name}",
                "dockerfile": f"Dockerfile.{module_name}"
            }
            service_def["container_name"] = module_name
            
        # For multi-host (stack) mode, build the image first and add an 'image' reference.
        elif mode == "multi":
            # image_name = build_image(module_name)
            service_def["image"] = f"157.159.160.197:5000/demo_{module_name}:latest"
            # Do not restart completed tasks
            service_def["deploy"] = {
                "restart_policy": {"condition": "none"},
                "placement": {"constraints": [f"node.role=={module_placement}"]},
            }
                # "placement": {"constraints": [f"node.hostname=={module_placement}"]},

        else:
            print("Invalid mode specified", file=sys.stderr)
            sys.exit(1)
        
        services[service_name] = service_def

        volumes[f"{module_name}_logs"] = {}

    compose_dict = {
        "version": "3.8",
        "services": services,
        "networks": {
            network_name: {
                "external": True
            }
        },
    }

    if mode=='multi':
        compose_dict['volumes'] = volumes
    return compose_dict

def main():
    parser = argparse.ArgumentParser(description="Generate Docker Compose file from config JSON.")
    parser.add_argument("-j", "--json", required=True, help="Path to config.json")
    parser.add_argument("-n", "--network", required=True, help="Name of the external network to use")
    parser.add_argument("--mode", choices=["single", "multi"], default="single",
                        help="Deployment mode: 'single' (docker compose) or 'multi' (docker stack)")
    args = parser.parse_args()
    
    # Load the configuration JSON file.
    try:
        with open(args.json, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config JSON: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate the compose configuration dictionary.
    compose_config = generate_compose(config, args.network, args.mode)
    
    # Write the generated YAML to 'docker-compose.yml' in the current (or target) directory.
    output_file = "./modules/docker-compose.yml"
    try:
        # open('./modules/docker-compose.yml', 'w').close()
        with open(output_file, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        print("✅ docker-compose.yml file generated successfully!")
    except Exception as e:
        print(f"Error writing {output_file}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
