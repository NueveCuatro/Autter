####################################################################################################
# PARSER for generate modules folder from a JSON config file
####################################################################################################
import json
import os
import argparse
####################################################################################################

# Functions to generate the following template folders and files :
# - Inputs Folders (1)
# - Logs_folders   (2)
# - Dockerfile     (3)
# - start.sh       (4)


# - (1) and (2)
def generate_utils_folders(module):
    '''
    Creation of two folders foor each module folder :
    - inputs folder to copy and past the input for AI inference
    - logs folder to save the log file
    '''
    ''
    name = module['Name']
    module_logs_path = f"./modules/{name}/logs"
    os.makedirs(module_logs_path, exist_ok=True)

# - (3) 
def generate_docker_file(module):
    '''
    Creation of the associate basic template DockerFile. This file use the base image and expose container port
    For complexe tasks, this file could require modifications.
    '''
    name = module['Name']
    dockerfile_path = f"./modules/{name}/Dockerfile.{name}"
    
    with open(dockerfile_path, 'w') as f:
        
        f.write("##### DOCKERFILE ######\n")
        f.write("# Specific Image #\n")
        f.write("###################\n\n")
        
        f.write("# Inherit from the base image\n")
        f.write("FROM 157.159.160.197:5000/demo_base_image:latest\n\n")
        f.write(f"COPY .  /app/\n\n")
        # f.write(f"COPY ../node.py   /app/node.py\n")
        # f.write(f"COPY ../receiveMessageHandler.py   /app/receiveMessageHandler.py\n")
        # f.write(f"COPY ../sendMessageHandler.py   /app/sendMessageHandler.py\n\n")
        f.write("# Expose the port that will be used for networking\n")
        f.write("EXPOSE 5000\n\n")
        f.write("# Command executed when a container is deployed\n")
        f.write('CMD ["/bin/bash", "start.sh"]\n\n')
        # f.write('ENTRYPOINT ["./start.sh"]\n\n')

# - (4) 
def generate_start_file(module):
    '''
    Creation of the associated basic template start.sh. 
    For complex tasks, this file may require modifications.
    '''
    name = module['Name']
    start_path = f"./modules/{name}/start.sh"
    
    with open(start_path, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Display the IPv4 address, subnet mask, broadcast address, and MAC address\n")
        f.write("ip addr show eth0 | awk '\n")
        f.write("  /inet / {print \"IPv4 Address:\", $2; print \"Broadcast Address:\", $4}\n")
        f.write("  /link\\/ether/ {print \"MAC Address:\", $2}\n")
        f.write("'\n\n")
        f.write("# Run the Python script\n")
        f.write("echo before\n")
        f.write(f"python app_{name}.py\n")
        f.write("echo after\n")

####################################################################################################
# Functions to generate module_n.py file depending the topology of the network load through JSON config file

# Get module connection : For each module save in list incomming and outgoing connection
def get_module_connections(module_name):
    incoming = []
    outgoing = []
    for connection in data['Topology']:
        if connection['from']['AIMName'] == module_name:
            outgoing.append((connection['to']['AIMName'], connection['type']['TYPE']))
        if connection['to']['AIMName'] == module_name:
            incoming.append((connection['from']['AIMName'], connection['type']['TYPE']))
    return incoming, outgoing


# Fonction pour générer le fichier d'un module
# def generate_module_file(module, index):
#     name = module['Name']
#     role = module.get("Role", "default_role")
#     device = module.get("Device", "cpu")
#     target_roles = module.get("Send_to", [])
#     # send_to_list = module['Send_to']
#     # incoming, outgoing = get_module_connections(name)
#     module_file_path = f"./modules/{name}/{name}.py"
    
#     with open(module_file_path, 'w') as f:
#         # ➡️ En-tête du fichier
#         f.write(f"#####################################\n")
#         f.write(f"# Module {index + 1} - {name}.py\n")
#         f.write(f"# Handles incoming and outgoing connections\n")
#         f.write(f"#####################################\n")
#         f.write("import time\n")
#         f.write("import logging\n")
#         f.write("import numpy as np\n")
#         f.write("from node import Node\n")
#         # f.write("from otter_net_utils import OtterUtils\n")
#         # f.write("tcp_tools = OtterUtils()\n")
#         f.write("print(\"Node class imported successfully!\")\n")
#         f.write("CONSUL_URL = \"http://157.159.160.197:8500\"")
#         # f.write(f"CONSUL_URL = \"http://consul:8500\"")
#         f.write("\n#####################################\n")
#         f.write("# Placeholder for future AI class\n")
#         f.write("#####################################\n\n")

#         f.write("if __name__ == \"__main__\":\n")

#         # ✅ Si le module agit en tant que client → sleep pour éviter les conflits initiaux
#         # if index % 2 == 1:
#         #     f.write(f"    time.sleep(2+{index})  # Wait during initialization for client connections\n")

#         # ✅ Initialiser le fichier log
#         f.write("    # Log Initialization\n")
#         f.write("    log_file_path = \"/app/logs/container.log\"\n")
#         # f.write("    tcp_tools.build_log_file(log_file_path)\n\n")

#         # ✅ Initialiser toutes les connexions après le log !
#         f.write(f"name = '{name}'\n")
#         # f.write("send_data = {'var1' : name}\n")#{\n")
#         f.write("send_data = {'var1' : np.random.rand(1024).astype(np.float64)}\n")#{\n")
#         # f.write("send_data = {'var1' : 'Hello world from ' + name, 'var2' : np.random.rand(2,2)}\n")#{\n")
#         # f.write("for i in range(3,100):\n")
#         # f.write("\tsend_data[str(i)] = f'data {i}'\n")
#         f.write(f"node = Node(5000, log_file_path=log_file_path, container_name=\"{name}\", role=\"{role}\", device=\"{device}\", consul_url=CONSUL_URL, target_roles={target_roles} )\n")
#         # f.write("node.send_data_to_peers(send_data=send_data)\n")
#         f.write("for i in range(1000):\n")
#         f.write("\tnode.send_data_to_peers(send_data=send_data)\n")
#         f.write(f"\tnode.sent_peers = set()\n")
#         f.write("\ttime.sleep(0.01)\n")

#         f.write("while True:\n")
#         f.write("\ttime.sleep(30)\n")
#         # f.write("\tlogging.info(node.received_data)\n")
#         f.write("\tbreak\n")


####################################################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_file', '-j', required=True, type=str, help='Pass the config.json path')
    args = parser.parse_args()

    # Charger le fichier JSON
    with open(args.json_file, 'r') as f:
        data = json.load(f)

    # Créer des répertoires pour chaque module
    for module in data['Modules']:
        path_module = './modules/'
        os.makedirs(path_module + module['Name'], exist_ok=True)

    # ✅ Générer le fichier Python pour chaque module
    for i, module in enumerate(data['Modules']):
        os.makedirs('./modules', exist_ok=True)
        # generate_module_file(module, i)
        generate_utils_folders(module)
        generate_docker_file(module)
        generate_start_file(module)
        
    print("✅ Python module files and associate folders generated with dynamic TCP/UDP connections!")
