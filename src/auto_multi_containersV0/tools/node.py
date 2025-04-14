import socket
import threading
import requests
import re
import time
import numpy as np
import ast
from receiveMessageHandler import ReceiveMessageHandler
from sendMessageHandler import SendMessageHandler
import logging
import os
import subprocess

class Node:
    def __init__(self,
                 port : int,
                 send_data : dict = None,
                 log_file_path : str = None,
                 container_name : str = None,
                 tags : list = None,
                 consul_url : str = None,
                 target_roles : list = None,
                 ):
        
        if log_file_path :
            self.build_log_file(log_file_path)

        self.target_roles = target_roles
        self.consul_url = consul_url
        self.container_name = container_name
        self.tags = tags
        self.host = '0.0.0.0' # listen on all interfaces
        self.port = port
        self.send_buffer = send_data # the send buffer is a dict{'args' : value, ...} tha contains all 
        #the messages to send to the peer_list. The messages will be passe to a message class to be sent. 
        #The message class will have one instance per message to be sent
        self.sent_peers = set()           # Track IDs of peers that have already received data

        # for addr in self.send_buffer.keys():
        #     patern = r"\('((\d{1,3}\.){3}\d{1,3})',\s*(\d{1,5})\)"
        #     assert bool(re.match(patern, addr)), "The keys of the dict send_buffer must be a string and in format '('xxx.xxx.xxx.xxx',XXXX)'"

        # string_addr_list = list(self.send_buffer.keys())
        # self.peer_list = list(map(ast.literal_eval,string_addr_list)) # list of peers to which the node has to connect (to send). [(host, port), (host, port)...]


        # for peer_addr in self.peer_list:
        #     # patern = r'^(\d{1,3}\.){3}\d{1,3}$'
        #     # assert isinstance(peer_addr, tuple), f"The peer_list is not in the good format, should be [(host, port), ...], with host : str and port : int  \nGiven : {self.peer_list} "
        #     assert isinstance(peer_addr[0], str), f"The peer_list is not in the good format, should be [(host, port), ...], with host : str and port : int  \nGiven : {self.peer_list} "
        #     # assert bool(re.match(patern, peer_addr[0])), "The ip address is not in the good format."
        #     assert isinstance(peer_addr[1], int)

        # self.established_connection_peer = [] # list with the established connections
        self.received_data = {} # received data { 'sender' : {'args' : value ...} }
        self.peer_connected_socks = []

        # We strat the server on a different thread for it to always be able to listen without blocking the app
        self.register_to_consul()
        # logging.info(f"[DEBUG] This should be viwed only once per container !!!!")
        threading.Thread(target=self.start_server, daemon=True).start()
        time.sleep(4)

    def build_log_file(self, log_file_path):
        """
        Initializes the log file and sets up the logging configuration.
        Args:
            log_file_path (str): The path to the log file where logs will be written.
        """
        try:
            with open(log_file_path, 'w') as file:
                pass  
            logging.basicConfig(
                filename=log_file_path,
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",  
            )
            logging.info(f"Logging initialized. Log file is: {log_file_path}")
        except Exception as e:
            logging.error(f"Error initializing log file: {e}")
            raise
    
    def get_container_ip(self):
        try:
            ip = subprocess.check_output(
                "ip addr show eth0 | awk '/inet / {print $2}'", 
                shell=True
            ).decode().strip().split("/")[0]
            return ip
        except Exception as e:
            logging.error("Could not get container IP: %s", e)
            return "127.0.0.1"
    
    def get_container_id(self):
        return socket.gethostname()


    def register_to_consul(self):
        # Build the registration payload
        self.container_ip = self.get_container_ip()
        self.container_id = self.get_container_id()
        # logging.info(f'[DEBUG] container id on registration{self.container_id}')
        registration = {
            "Name": self.container_name,
            "ID": str(self.container_id),
            "Port": self.port,
            "Tags": self.tags,
            # Using HOST_IP if provided; otherwise, default to 127.0.0.1
            # "Address": os.environ.get("HOST_IP", "127.0.0.1")
            "Address": self.container_ip,
            "Check" : {
                "TTL" : "10s",
                "DeregisterCriticalServiceAfter" : "30s"
            }
        }
        # logging.info(f"[DEBUG] Registering container with ID: {self.container_id}")
        # logging.info(f"[DEBUG] Registration payload: {registration}")
        try:
            logging.info("Registering to Consul: %s", registration)
            response = requests.put(f"{self.consul_url}/v1/agent/service/register", json=registration)
            if response.status_code == 200:
                logging.info("Registration successful")
            else:
                logging.error("Registration failed: %s", response.text)
        except Exception as e:
            logging.error("Exception during registration: %s", e)

    def start_server(self):
        # self.register_to_consul()
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.host, self.port))
        server_sock.listen(5)
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        logging.info(f"[SERVER] Listening on {self.host}:{self.port}")
        while True:
            conn, addr = server_sock.accept()
            # each established connection is lunched on a different thread
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
    

    def handle_client(self, conn: socket.socket, addr: str):
        print(f"[SERVER] Connection from {addr}")
        logging.info(f"[SERVER] Connection from {addr}")
        handler = ReceiveMessageHandler(conn, addr)
        try:
            while True:
                # try:
                messages = handler.recv_all_messages()
                if messages:
                    for variable_name, msg in messages:
                        self.add_data(addr, variable_name, msg)
                        print(f"[SERVER] Received message {msg!r} with variable name {variable_name!r} from {addr}")
                        logging.info(f"[SERVER] Received message {msg!r} with variable name {variable_name!r} from {addr}")
                time.sleep(0.1)
                # except BlockingIOError:
                #     # No data ready yet.
                #     time.sleep(0.1)
        except RuntimeError as e:
            print(f"[SERVER] {e} from {addr}")
            logging.error(f"[SERVER] {e} from {addr}")
        finally:
            conn.close()
            print(f"[SERVER] Connection closed {addr}")
            logging.info(f"[SERVER] Connection closed {addr}")

    def add_data(self, addr, variable_name, msg):
        if addr in list(self.received_data.keys()) :
            self.received_data[addr][str(variable_name)] = msg
        else:
            self.received_data[addr] = {str(variable_name) : msg}


    # def connect_to_one_peer(self, peer_host, peer_port):
    #     """
    #     Try once to connect to the peer. If the connection fails, return None.
    #     """
    #     client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     try:
    #         client_sock.connect((peer_host, peer_port))
    #         print(f"[CLIENT] Connected to peer at {peer_host}:{peer_port}")
    #         logging.info(f"[CLIENT] Connected to peer at {peer_host}:{peer_port}")
    #         return client_sock
    #     except Exception as e:
    #         print(f"[CLIENT] Could not connect to {peer_host}:{peer_port}: {e}")
    #         logging.error(f"[CLIENT] Could not connect to {peer_host}:{peer_port}: {e}")
    #         return None


    # def _connect_and_send(self, peer):
    #     """
    #     For a given peer (a tuple (host, port)), repeatedly try to connect.
    #     As soon as the connection is established, send the data from send_buffer for that peer.
    #     """
    #     # peer_addr = (peer[0], peer[1])
    #     # key = str(peer_addr)
    #     # Loop until we get a connection.
    #     while True:
    #         try:
    #             # Retrieve registered services from Consul.
    #             response = requests.get(f"{self.consul_url}/v1/agent/services")
    #             services = response.json()
    #             # logging.info(f'[DEBUG] {self.container_name} container id is {self.container_id}')
    #             # logging.info(services.items())
    #             for service_id, service in services.items():
    #                 # logging.info(f'[DEBUG] the consul container id : {service["ID"]}')
    #                 if service["ID"] == self.container_id:
    #                     continue
    #                 # Check if the service has one of our target roles in its tags.
    #                 if any(target_role.strip() in service.get("Tags", []) for target_role in self.target_roles)\
    #                 or any(target_role.strip() == service.get("Name") for target_role in self.target_roles):
    #                     target_address = service["Address"]
    #                     target_port = service["Port"]
    #                     # print(f"{self.container_name} sendto : ", target_address, target_port)
    #                     logging.info("Attempting to connect to target %s at %s:%s", service["ID"], target_address, target_port)
    #                     sock = self.connect_to_one_peer(target_address, target_port)
    #                     if sock:
    #                         # Once connected, send the data.
    #                         handler = SendMessageHandler(sock, (target_address, target_port), self.send_buffer)#[key])
    #                         handler.send_all_messages()
    #                         # Optionally, if you want to keep the connection open for further communication,
    #                         # you can store the socket in self.peer_connected_socks.
    #                         self.peer_connected_socks.append(((target_address, target_port), sock))
    #                         break  # Exit the loop for this peer.
    #                     else:
    #                         # Wait a few seconds before retrying.
    #                         print(f"[CLIENT] Retrying connection to {(target_address, target_port)} in 3 seconds...")
    #                         logging.info(f"[CLIENT] Retrying connection to {(target_address, target_port)} in 3 seconds...")
    #                         time.sleep(3)
    #         except Exception as e :
    #             logging.error("Error fetching services from Consul: %s", e)

    #         # sock = self.connect_to_one_peer(peer[0], peer[1])


    # def send_data_to_peers(self):
    #     """
    #     For each peer in the peer_list, start a thread that will try to connect and send data.
    #     This allows other peers to get their data sent immediately.
    #     """
    #     for peer in self.peer_list:
    #         # Start a separate thread for each peer.
    #         t = threading.Thread(target=self._connect_and_send, args=(peer,), daemon=True)
    #         t.start()

    def connect_to_one_peer(self, peer_host, peer_port):
        """
        Try once to connect to the peer. If the connection fails, return None.
        """
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_sock.connect((peer_host, peer_port))
            logging.info(f"[CLIENT] Connected to peer at {peer_host}:{peer_port}")
            return client_sock
        except Exception as e:
            logging.error(f"[CLIENT] Could not connect to {peer_host}:{peer_port}: {e}")
            return None

    def _send_to_peer(self, service):
        """
        Handles connecting and sending data to a specific peer identified by a given service.
        Retry on an independent schedule until success, then mark the peer as done.
        """
        target_address = service["Address"]
        target_port = service["Port"]
        service_id = service["ID"]

        while True:
            sock = self.connect_to_one_peer(target_address, target_port)
            if sock:
                # Once connected, create the send handler to send the unified send_buffer.
                handler = SendMessageHandler(sock, (target_address, target_port), self.send_buffer)
                handler.send_all_messages()
                # Optionally, keep the connection open:
                self.peer_connected_socks.append(((target_address, target_port), sock))
                # Mark this peer as finished so we don't resend in future polls.
                self.sent_peers.add(service_id)
                logging.info(f"[CLIENT] Data sent to peer {service_id} at {target_address}:{target_port}")
                break  # Exit the retry loop for this peer.
            else:
                logging.info(f"[CLIENT] Retry connection to {target_address}:{target_port} in 3 seconds...")
                time.sleep(3)  # Independent delay for this peer before retrying.

    def _poll_consul_and_dispatch(self):
        """
        Poll Consul on a fixed schedule. For every registered service that matches our target roles
        (and that we haven't already sent data to), spawn a new thread for sending.
        """
        while True:
            try:
                response = requests.get(f"{self.consul_url}/v1/agent/services")
                services = response.json()
                logging.info(f"[SERVER] polling registery from consul")

                for service_id, service in services.items():
                    # Skip self-registration.
                    if service["ID"] == self.container_id:
                        continue

                    # Skip peers that already received data.
                    if service_id in self.sent_peers:
                        continue

                    # Check if the service matches our target roles or by exact container name.
                    if any(target_role.strip() in service.get("Tags", []) for target_role in self.target_roles) or \
                       any(target_role.strip() == service.get("Service") for target_role in self.target_roles):
                        logging.info(f"[DEBUG] Peer candidate found: {service_id} ({service.get('Service')})")
                        # Spawn a dedicated thread to handle sending to this peer.
                        t = threading.Thread(target=self._send_to_peer, args=(service,), daemon=True)
                        t.start()

            except Exception as e:
                logging.error("Error fetching services from Consul: %s", e)

            # After processing all services, sleep a bit before polling again.
            time.sleep(3)

    def send_data_to_peers(self):
        """
        Start the polling thread that checks Consul for new peers to send data.
        """
        poll_thread = threading.Thread(target=self._poll_consul_and_dispatch, daemon=True)
        poll_thread.start()

if __name__ == "__main__":
    # peer_dict = {'host': '127.0.0.1', 'port': 6347}

    send_data = {'var1':'Hello from node 1', 'var2':np.eye(3)}

    node1 = Node(6346, send_data=send_data)
    node1.send_data_to_peers()
    print(node1.received_data)

    while True:
        time.sleep(10)