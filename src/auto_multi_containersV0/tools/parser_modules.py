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
    module_inputs_path = f"./modules/{name}/inputs"
    os.makedirs(module_logs_path, exist_ok=True)
    os.makedirs(module_inputs_path, exist_ok=True)

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
        f.write("FROM demo_base_image\n\n")
        f.write("# Expose the port that will be used for networking\n")
        f.write("EXPOSE 5000\n\n")
        f.write("# Command executed when a container is deployed\n")
        f.write('CMD ["/bin/bash", "start.sh"]\n\n')

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
        f.write(f"python {name}.py\n")

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
def generate_module_file(module, index):
    name = module['Name']
    role = module.get("Role", "default_role")
    device = module.get("Device", "cpu")
    tags = [role, device]
    target_roles = module.get("Send_to", [])
    # send_to_list = module['Send_to']
    # incoming, outgoing = get_module_connections(name)
    module_file_path = f"./modules/{name}/{name}.py"
    
    with open(module_file_path, 'w') as f:
        # ➡️ En-tête du fichier
        f.write(f"#####################################\n")
        f.write(f"# Module {index + 1} - {name}.py\n")
        f.write(f"# Handles incoming and outgoing connections\n")
        f.write(f"#####################################\n")
        f.write("import time\n")
        f.write("import logging\n")
        f.write("import numpy as np\n")
        f.write("from node import Node\n")
        # f.write("from otter_net_utils import OtterUtils\n")
        # f.write("tcp_tools = OtterUtils()\n")
        f.write("print(\"Node class imported successfully!\")\n")
        f.write("CONSUL_URL = \"http://consul:8500\"")
        f.write("\n#####################################\n")
        f.write("# Placeholder for future AI class\n")
        f.write("#####################################\n\n")

        f.write("if __name__ == \"__main__\":\n")

        # ✅ Si le module agit en tant que client → sleep pour éviter les conflits initiaux
        # if index % 2 == 1:
        #     f.write(f"    time.sleep(2+{index})  # Wait during initialization for client connections\n")

        # ✅ Initialiser le fichier log
        f.write("    # Log Initialization\n")
        f.write("    log_file_path = \"/app/logs/container.log\"\n")
        # f.write("    tcp_tools.build_log_file(log_file_path)\n\n")

        # ✅ Initialiser toutes les connexions après le log !
        f.write("send_data = {'var1' : np.random.rand(3,3), 'var2': 'Hello world'}\n")#{\n")
        f.write(f"node = Node(5000, send_data=send_data, log_file_path=log_file_path, container_name=\"{name}\", tags={tags}, consul_url=CONSUL_URL, target_roles={target_roles} )\n")
        f.write("node.send_data_to_peers()\n")

        f.write("while True:\n")
        f.write("\ttime.sleep(30)\n")
        f.write("\tbreak\n")

        
        
        



        # if incoming or outgoing:
        #     f.write("    ##################################### SOCKET INITIALIZATION #####################################\n")

        # # 🌟 Initialiser les connexions entrantes (indexées)
        # if incoming:
        #     for i, (src_module, conn_type) in enumerate(incoming, start=1):
        #         # ✅ Si le module est d'indice impair → `HOST = '{module}_container'`
        #         if index % 2 == 0:
        #             host = "'0.0.0.0'"
        #             if conn_type == "TCP":
        #                 f.write(f"    # TCP Connection to receive from {src_module}\n")
        #                 f.write(f"    HOST_{i} = {host}\n")  
        #                 f.write(f"    PORT_{i} = 5000\n")
        #                 f.write(f"    s_{i} = tcp_tools.init_server_TCP_connection(HOST_{i}, PORT_{i})\n\n")
        #             elif conn_type == "UDP":
        #                 f.write(f"    # UDP Connection to receive from {src_module}\n")
        #                 f.write(f"    HOST_UDP_{i} = {host}\n")  
        #                 f.write(f"    PORT_UDP_{i} = 5000\n")
        #                 f.write(f"    buffer_size = 1024\n")
        #                 f.write(f"    udp_sock_{i}, udp_addr_{i} = tcp_tools.init_server_UDP_connection(HOST_UDP_{i}, PORT_UDP_{i}, buffer_size)\n\n")

        #         else:
        #             host = f"'{src_module}_container'"
        #             if conn_type == "TCP":
        #                 f.write(f"    # TCP Connection to receive from {src_module}\n")
        #                 f.write(f"    HOST_{i} = {host}\n")  
        #                 f.write(f"    PORT_{i} = 5001\n")
        #                 f.write(f"    s_{i} = tcp_tools.init_client_TCP_connection(HOST_{i}, PORT_{i})\n\n")
        #             elif conn_type == "UDP":
        #                 f.write(f"    # UDP Connection to receive from {src_module}\n")
        #                 f.write(f"    HOST_UDP_{i} = {host}\n")  
        #                 f.write(f"    PORT_UDP_{i} = 5001\n")
        #                 f.write(f"    buffer_size = 1024\n")
        #                 f.write(f"    udp_sock_{i}, udp_addr_{i}  = tcp_tools.init_client_connection_UDP(HOST_UDP_{i}, PORT_UDP_{i}, buffer_size)\n\n")

        # # 🌟 Initialiser les connexions sortantes (indexées)
        # if outgoing:
        #     for i, (dst_module, conn_type) in enumerate(outgoing, start=1):
        #         # ✅ Si le module est d'indice impair → `HOST = '{module}_container'`
        #         if index % 2 == 0:
        #             host = "'0.0.0.0'"
        #             if conn_type == "TCP":
        #                 f.write(f"    # TCP Connection to send to {dst_module}\n")
        #                 f.write(f"    HOST_OUT_{i} = {host}\n")
        #                 f.write(f"    PORT_OUT_{i} = 5001\n")
        #                 f.write(f"    s_out_{i} = tcp_tools.init_server_TCP_connection(HOST_OUT_{i}, PORT_OUT_{i})\n\n")
                    
        #             elif conn_type == "UDP":
        #                 f.write(f"    # UDP Connection to send to {dst_module}\n")
        #                 f.write(f"    HOST_UDP_OUT_{i} = {host}\n")
        #                 f.write(f"    PORT_UDP_OUT_{i} = 5001\n")
        #                 f.write(f"    buffer_size = 1024\n")
        #                 f.write(f"    udp_sock_out_{i}, udp_out_addr_{i} = tcp_tools.init_server_UDP_connection(HOST_UDP_OUT_{i}, PORT_UDP_OUT_{i},buffer_size )\n\n")

        #         else:
        #             host = f"'{dst_module}_container'"
        #             if conn_type == "TCP":
        #                 f.write(f"    # TCP Connection to send to {dst_module}\n")
        #                 f.write(f"    HOST_OUT_{i} = {host}\n")
        #                 f.write(f"    PORT_OUT_{i} = 5000\n")
        #                 f.write(f"    s_out_{i} = tcp_tools.init_client_TCP_connection(HOST_OUT_{i}, PORT_OUT_{i})\n\n")
        #             elif conn_type == "UDP":
        #                 f.write(f"    # UDP Connection to send to {dst_module}\n")
        #                 f.write(f"    HOST_UDP_OUT_{i} = {host}\n")
        #                 f.write(f"    PORT_UDP_OUT_{i} = 5000\n")
        #                 f.write(f"    buffer_size = 1024\n")
        #                 f.write(f"    udp_sock_out_{i}, udp_out_addr_{i} = tcp_tools.init_client_connection_UDP(HOST_UDP_OUT_{i}, PORT_UDP_OUT_{i}, buffer_size)\n\n")



        # # ✅ Réception des données (réutilisation des sockets)
        # if incoming:
        #     f.write("    ##################################### INCOMING DATA #####################################\n")
        #     for i, (_, conn_type) in enumerate(incoming, start=1):
        #         if conn_type == "TCP":
        #             f.write(f"    buffer_size = 1024\n")
        #             f.write(f"    data_decode = tcp_tools.wait_for_container_variable_TCP(s_{i}, buffer_size)\n\n")
        #         elif conn_type == "UDP":
        #             f.write(f"    buffer_size = 1024\n")
        #             f.write(f"    data_decode, udp_addr_{i} = tcp_tools.wait_for_container_variable_UDP(udp_sock_{i}, buffer_size)\n\n")

        # # ✅ Simulation du traitement AI
        # f.write("    ##########################################\n")
        # f.write("    # Placeholder for future AI prediction \n")
        # f.write("    prediction = 'prediction'\n")
        # f.write("    ##########################################\n\n")


        # # ✅ Envoi des résultats
        # if outgoing:
        #     f.write("    ##################################### OUTGOING DATA #####################################\n")
        #     for i, (_, conn_type) in enumerate(outgoing, start=1):
        #         if conn_type == "TCP":
        #             f.write(f"    tcp_tools.send_variable_to_container_TCP(s_out_{i}, prediction)\n\n")
        #         elif conn_type == "UDP":
        #             f.write(f"    tcp_tools.send_variable_to_container_UDP(udp_sock_out_{i}, prediction, udp_out_addr_{i})\n\n")

        # f.write("\n")


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
        generate_module_file(module, i)
        generate_utils_folders(module)
        generate_docker_file(module)
        generate_start_file(module)
        
    print("✅ Python module files and associate folders generated with dynamic TCP/UDP connections!")
