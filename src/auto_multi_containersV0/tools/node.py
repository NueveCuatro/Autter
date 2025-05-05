import socket
import threading
import requests
import re
import sys
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
                 log_file_path : str = None,
                 container_name : str = None,
                 role : str = "default_role",
                 device : str = "CPU",
                 consul_url : str = None,
                 target_roles : list = None,
                 ):
        
        if log_file_path :
            self._build_log_file(log_file_path)

        self.target_roles = target_roles
        self.consul_url = consul_url
        self.container_name = container_name
        assert isinstance(role, str)
        self.role = role,
        assert isinstance(device, str)
        self.device = device
        self.tags = [role, device]
        logging.info(self.tags)
        self.host = '0.0.0.0' # listen on all interfaces
        self.port = port
        self.sent_peers = set()     # Track IDs of peers that have already received data
        self.in_progress_peers = set()


        # self.established_connection_peer = [] # list with the established connections
        self.received_data = {} # received data { 'sender' : {'args' : value ...} }

        # We strat the server on a different thread for it to always be able to listen without blocking the app
        self._register_to_consul()
        # logging.info(f"[DEBUG] This should be viwed only once per container !!!!")
        threading.Thread(target=self._start_server, daemon=True).start()
        time.sleep(4)

    # def build_log_file(self, log_file_path):
    #     """
    #     Initializes the log file and sets up the logging configuration.
    #     Args:
    #         log_file_path (str): The path to the log file where logs will be written.
    #     """
    #     try:
    #         with open(log_file_path, 'w') as file:
    #             pass  
    #         logging.basicConfig(
    #             filename=log_file_path,
    #             handlers=[logging.FileHandler(log_file_path),
    #                       logging.StreamHandler(sys.stdout)],
    #             # level=logging.INFO,
    #             format="%(asctime)s - %(levelname)s - %(message)s",  
    #         )
    #         logging.info(f"Logging initialized. Log file is: {log_file_path}")
    #     except Exception as e:
    #         logging.error(f"Error initializing log file: {e}")
    #         raise
    def _build_log_file(self, log_file_path):
        """
        Initializes the log file and sets up the logging configuration.
        Args:
            log_file_path (str): The full path to the log file.
        """
        # 1) Ensure the parent log directory exists
        log_dir = os.path.dirname(log_file_path)
        os.makedirs(log_dir, exist_ok=True)

        # 2) Touch the file so it's there (optional)
        with open(log_file_path, 'a'):
            os.utime(log_file_path, None)

        # 3) Configure logging with both a FileHandler and StreamHandler
        file_handler   = logging.FileHandler(log_file_path)
        console_handler = logging.StreamHandler(sys.stdout)

        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler],
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

        logging.info(f"Logging initialized. Log file is: {log_file_path}")
    
    # def get_container_ip(self):
    #     try:
    #         ip = subprocess.check_output(
    #             "ip addr show eth0 | awk '/inet / {print $2}'", 
    #             shell=True
    #         ).decode().strip().split("/")[0]
    #         return ip
    #     except Exception as e:
    #         logging.error("Could not get container IP: %s", e)
    #         return "127.0.0.1"
    
    def _get_container_ip(self):
        """
        Return the Swarm VIP for this container’s service, so that clients
        always connect to the service name (and get routed via the overlay mesh).
        Falls back to eth0 if DNS fails.
        """
        # We assume you set an environment var SERVICE_NAME equal to your full
        # Swarm service name, e.g. "multi_app_stack_c1_service"
        svc = os.environ.get("SERVICE_NAME")  
        if svc:
            try:
                vip = socket.gethostbyname(svc)
                logging.info(f"[DISCOVERY] Resolved service VIP {svc} → {vip}")
                return vip
            except Exception as e:
                logging.warning(f"[DISCOVERY] DNS lookup failed for {svc}: {e}")

        # Fallback: real container IP on eth0
        try:
            out = subprocess.check_output(
                "ip addr show eth0 | awk '/inet / {print $2}'", 
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip().split("/")[0]
            logging.info(f"[DISCOVERY] Using eth0 address fallback → {out}")
            return out
        except Exception as e:
            logging.error(f"Could not get container IP from eth0: {e}")
            return "127.0.0.1"
    
    def _get_container_id(self):
        return socket.gethostname()


    def _register_to_consul(self):
        # Build the registration payload
        self.container_ip = self._get_container_ip()
        self.container_id = self._get_container_id()
        # logging.info(f'[DEBUG] container id on registration{self.container_id}')
        registration = {
            "Name": self.container_name,
            "ID": str(self.container_id),
            "Port": self.port,
            "Tags": self.tags,
            # Using HOST_IP if provided; otherwise, default to 127.0.0.1
            # "Address": os.environ.get("HOST_IP", "127.0.0.1")
            "Address": self.container_ip,
            "Check": {
                 "TCP": f"{self.container_ip}:{self.port}",
                 "Interval": "5s",
                 "Timeout": "1s",
                 "DeregisterCriticalServiceAfter": "10s"
             }
        }
            # "Check" : {
            #     "TTL" : "10s",
            #     "DeregisterCriticalServiceAfter" : "30s"
            # }
        # logging.info(f"[DEBUG] Registering container with ID: {self.container_id}")
        # logging.info(f"[DEBUG] Registration payload: {registration}")
        try:
            logging.info("Registering to Consul: %s", registration)
            response = requests.put(f"{self.consul_url}/v1/agent/service/register", json=registration)
            if response.status_code == 200:
                logging.info(f"[DISCOVERY] Registration successful to {self.consul_url}")
            else:
                logging.error("[DISCOVERY] Registration failed: %s", response.text)
        except Exception as e:
            logging.error("Exception during registration: %s", e)

    def _start_server(self):
        # self.register_to_consul()
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.host, self.port))
        server_sock.listen(5)
        # print(f"[SERVER] Listening on {self.host}:{self.port}")
        logging.info(f"[SERVER] Listening on {self.host}:{self.port}")
        while True:
            conn, addr = server_sock.accept()
            # each established connection is lunched on a different thread
            threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
    

    def _handle_client(self, conn: socket.socket, addr: str):
        # print(f"[SERVER] Connection from {addr}")
        logging.info(f"[SERVER] Connection from {addr}")
        handler = ReceiveMessageHandler(conn, addr)
        try:
            while True:
                # try:
                messages = handler.recv_all_messages()
                if messages:
                    creds, latency = messages.pop(0)
                    for variable_name, msg in messages:
                        if variable_name=='container_creds_xxx':
                            continue
                        self._add_data(creds, variable_name, msg)
                        # print(f"[SERVER] Received message {msg!r} with variable name {variable_name!r} from {addr}")
                        # logging.info(f"[SERVER] Received message {msg!r} with variable name {variable_name!r} from {addr}")
                    logging.info(f"[LATENCY] from {creds} is : {latency} on port {addr[1]}")
                time.sleep(0.1)
                # except BlockingIOError:
                #     # No data ready yet.
                #     time.sleep(0.1)
        except RuntimeError as e:
            print(f"[SERVER] {e} from {addr}")
            logging.error(f"[SERVER] {e} from {addr}")
        finally:
            conn.close()
            logging.info(f"[SERVER] Connection closed {addr}")

    def _add_data(self, creds, variable_name, msg):
        if creds in list(self.received_data.keys()) :
            self.received_data[creds][str(variable_name)] = msg
        else:
            self.received_data[creds] = {str(variable_name) : msg}


    def _connect_to_one_peer(self, peer_host, peer_port):
        """
        Try once to connect to the peer. If the connection fails, return None.
        """
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.settimeout(10)   # fail fast after 5 seconds
        try:
            # client_sock.connect((peer_host, peer_port))
            logging.info(f"[CLIENT] attempting socket.connect() on {peer_host}:{peer_port}")
            client_sock.connect((peer_host, peer_port))
            logging.info(f"[CLIENT] socket.connect() succeeded")

            # logging.info(f"[CLIENT] Connected to peer at {peer_host}:{peer_port}")
            return client_sock
        except Exception as e:
            logging.error(f"[CLIENT] Could not connect to {peer_host}:{peer_port}: {e}")
            return None


    def _send_to_peer(self, service):
        """
        Handles connecting and sending data to a specific peer identified by a given service.
        Retry on an independent schedule until success, then mark the peer as done.
        """
        service_id = service["ID"]
        target_address = service["Address"]
        target_port = service["Port"]

        # logging.info(f"[THREAD {service_id}] → _send_to_peer starting (addr={target_address}:{target_port})")
        try:
            while True:
                # logging.info(f"[THREAD {service_id}] attempting connect to {target_address}:{target_port}")
                sock = self._connect_to_one_peer(target_address, target_port)
                # logging.info(f"[THREAD {service_id}] after")
                if sock:
                    # Once connected, create the send handler to send the unified send_buffer.
                    # logging.info(f"[THREAD {service_id}] connected, now sending buffer")
                    handler = SendMessageHandler(sock, (target_address, target_port), self.send_buffer)
                    handler.send_all_messages()
                    # Mark this peer as finished so we don't resend in future polls.
                    self.sent_peers.add(service_id)
                    self.in_progress_peers.remove(service_id)
                    logging.info(f"[CLIENT] Data sent to peer {service_id} at {target_address}:{target_port}")
                    break  # Exit the retry loop for this peer.
                else:
                    # logging.info(f"[CLIENT] Retry connection to {target_address}:{target_port} in 3 seconds...")
                    logging.info(f"[THREAD {service_id}] connect failed; retrying in 3s")
                    time.sleep(3)  # Independent delay for this peer before retrying.
        except Exception as e :
            logging.exception(f"[THREAD {service_id}] ❌ unexpected error in _send_to_peer")



    def _poll_consul_and_dispatch(self):
        """
        Poll Consul on a fixed schedule. For every registered service that matches our target roles
        (and that we haven't already sent data to), spawn a new thread for sending.
        """
        while True:
            try:
                response = requests.get(f"{self.consul_url}/v1/agent/services")
                # logging.info(response.text)
                services = response.json()
                logging.info(f"[SERVER] polling registery from consul")

                for service_id, service in services.items():
                    # Skip self-registration.
                    if service["ID"] == self.container_id:
                        continue

                    # # Skip peers that already received data.
                    if service_id in self.sent_peers:
                        continue

                    # Check if the service matches our target roles or by exact container name.
                    if any(target_role.strip() in service.get("Tags", []) for target_role in self.target_roles) or \
                       any(target_role.strip() == service.get("Service") for target_role in self.target_roles):
                        if service["ID"] not in self.in_progress_peers:
                            self.in_progress_peers.add(service["ID"])
                            t = threading.Thread(
                                target=self._send_to_peer,
                                args=(service,),
                                daemon=True,
                                name=f"send-{service['ID']}"
                                )
                            t.start()
                        # logging.info(f"[DEBUG] Peer candidate found: {service_id} ({service.get('Service')})")
                        # # Spawn a dedicated thread to handle sending to this peer.
                        # t = threading.Thread(target=self._send_to_peer, args=(service,), daemon=True)
                        # t.start()

            except Exception as e:
                logging.error("Error fetching services from Consul: %s", e)
            # break
            # After processing all services, sleep a bit before polling again.
            time.sleep(5)


    def send_data_to_peers(self, send_data):
        """
        Start the polling thread that checks Consul for new peers to send data.
        """
        self.send_buffer = send_data # the send buffer is a dict{'args' : value, ...} tha contains all 
        #the messages to send to the peer_list. The messages will be passe to a message class to be sent. 
        #The message class will have one instance per message to be sent
        self.send_buffer['container_creds_xxx'] = (self.container_name, self.role)
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