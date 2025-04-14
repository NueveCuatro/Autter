########## PYTHON CLASS FOR TCP/UDP INTERACTION ##########
####################
# Libraries
import logging
import socket  
import numpy as np
####################

class OtterUtils :

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

# ------------------------------ UDP -----------------------------------------#
# In this section, we propose an implementation of functions to initiate and use a UDP connection to 
# exchange strings only (max length = buffer size) only.
# We use the UDP protocol for faster and smaller variable exchanges.
    
   
    def init_server_UDP_connection(self, HOST, PORT, buffer_size):
        """
        Initializes a UDP connection for the server, waits for the client address (for runtime optimization), sends server address
        and returns the socket and client address.

        Args:
            HOST (str): The IP address or hostname of the server.
            PORT (int): The port to use for the connection.
            buffer_size (int): The size of the buffer to use for receiving data.

        Returns:
            tuple: A tuple containing the UDP socket object and the client address.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((HOST, PORT))
            logging.info(f"Network started on {HOST}:{PORT} and waiting for client messages")

            _, client_addr = self.wait_for_container_variable_UDP(s, buffer_size)
            logging.info(f"Connection with {client_addr} available")

            s.sendto(b"Connection established", client_addr)
            logging.info(f"Sent confirmation to {client_addr}")

            return s, client_addr

        except socket.error as e:
            logging.error(f"Error initializing server: {e}")
            raise


    def init_client_connection_UDP(self, HOST, PORT, buffer_size):
        """
        Initializes a UDP connection for the client and sends a connection request to the server.
        Receive a UDP packet from the server to obtain the server address. 

        Args:
            HOST (str): The IP address or hostname of the server.
            PORT (int): The port to use for the connection.
            buffer_size (int): The size of the buffer to use for receiving data.

        Returns:
            tuple: The UDP socket object and the server address.
        """
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            s.sendto(b"Request for connection", (HOST, PORT))
            logging.info(f"Connection request sent to {HOST}:{PORT}")
            
            _, server_addr = self.wait_for_container_variable_UDP(s, buffer_size)
            logging.info(f"Connected to server at {server_addr}")
            
            return s, server_addr
        
        except socket.error as e:
            logging.error(f"Error initializing UDP connection: {e}")
            raise

    def wait_for_container_variable_UDP(self, s, buffer_size):
            """
            Waits for a container request (e.g., an AI prediction request) from the client.

            Args:
                s (socket): The UDP socket object used for communication.
                buffer_size (int): The size of the buffer to use for receiving data.

            Returns:
                tuple: A tuple containing the decoded message and the address of the sender.
            """
            try:

                data, addr = s.recvfrom(buffer_size)
                data_decode = data.decode()
                logging.info(f"Received message from {addr}: {data_decode}")
                return data_decode, addr
            
            except socket.error as e:
                logging.error(f"Error receiving data: {e}")
                raise


    def send_variable_to_container_UDP(self, s, prediction, addr):
        """
        Sends a prediction (string or NumPy array) to a container.

        Args:
            s (socket): The UDP socket object used for communication.
            prediction (str)
            addr (tuple): The address of the recipient.
        """
        try:
            if isinstance(prediction, str):
                prediction_encode = prediction.encode()
            else:
                raise TypeError("Prediction must be either a string")
            
            s.sendto(prediction_encode, addr)
            logging.info(f"Sent: {prediction_encode} to {addr}")
            
        except socket.error as e:
            logging.error(f"Error sending data: {e}")
            raise


# ------------------------------ TCP -----------------------------------------#
# In this section, we propose an implementation of functions to initiate and use a TCP connection to exchange strings or NumPy arrays.
# We use the TCP protocol for larger data and a more robust connection.
    
    def init_server_TCP_connection(self, HOST, PORT):
        """
        Initializes a TCP connection for the server and return the socket connexion

        Args:
            HOST (str/int): The IP address or hostname of the server.
            PORT (int): The port to use for the connection.

        Returns:
            conn (socket object): The socket object representing the client connection.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((HOST, PORT))
            s.listen()  
            logging.info(f"Network started on {HOST}:{PORT} and waiting for client messages")
            conn, addr = s.accept()
            logging.info(f"Connection available from {addr}")
            return conn
        
        except socket.error as e:
            logging.error(f"Error initializing server: {e}")
            raise


    def init_client_TCP_connection(self, HOST, PORT):
        """
        Initializes a TCP connection for the client and return the connected socket 

        Args:
            HOST (str/int): The IP address or hostname of the server.
            PORT (int): The port to connect to.

        Returns:
            s (socket object): The connected socket object.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            logging.info(f"Connection to server {HOST}:{PORT} established.")
            return s
        except socket.error as e:
            logging.error(f"Error connecting to server {HOST}:{PORT}: {e}")
            raise



    def send_variable_to_container_TCP(self, s, prediction):
        """
        Sends a variable (string or NumPy array) to a container via a TCP connection.

        Args:
            s (socket object): The connected socket to send data through.
            prediction (str or np.ndarray): The variable to send, either a string or a NumPy array.

        Raises:
            TypeError: If the prediction is not a string or a NumPy array.
        """
        try:
            if isinstance(prediction, str):
                prediction_encode = prediction.encode()
                metadata = ('str',)  

            elif isinstance(prediction, np.ndarray):
                prediction_encode = prediction.tobytes()
                metadata = ('np.ndarray', prediction.shape, prediction.dtype.str)  
            else:
                raise TypeError("Prediction must be either a string or a NumPy array")

            # Encode metadata and send its length first
            metadata_encode = str(metadata).encode()
            metadata_length = len(metadata_encode).to_bytes(4, byteorder='big') 
            s.sendall(metadata_length) 
            s.sendall(metadata_encode)  

            # Encode and send data length, then the actual data
            data_length = len(prediction_encode).to_bytes(4, byteorder='big')  
            s.sendall(data_length)  
            s.sendall(prediction_encode)  
            logging.info(f"Sent metadata and data with total length: {len(prediction_encode)}")

        except (TypeError) as e:
            logging.error(f"Error while sending data: {e}")
            raise

    def wait_for_container_variable_TCP(self, s, buffer_size):
        """
        Waits for a variable (string or NumPy array) from a container via a TCP connection.

        Args:
            s (socket object): The connected socket to receive data from.
            buffer_size (int): The size of the buffer for receiving data in chunks.

        Returns:
            prediction (str or np.ndarray): The received variable, either a string or a NumPy array.

        Raises:
            TypeError: If an unknown data type is received.
        """
        try:
            # Receive metadata 
            metadata_length = int.from_bytes(s.recv(4), byteorder='big')  
            metadata = s.recv(metadata_length).decode()  
            metadata = eval(metadata)  
            data_type = metadata[0]

            if data_type == 'np.ndarray':
                shape = metadata[1]  
                dtype_str = metadata[2]
                data_length = int.from_bytes(s.recv(4), byteorder='big')  
                received_data = b''
                while len(received_data) < data_length:
                    chunk = s.recv(min(buffer_size, data_length - len(received_data)))
                    received_data += chunk
                    logging.info(f"Received {len(received_data)} of {data_length} bytes")

                # Reconstruct the NumPy array
                dtype = np.dtype(dtype_str)
                prediction = np.frombuffer(received_data, dtype=dtype).reshape(shape)
                logging.info(f"Received NumPy prediction with shape: {prediction.shape}")
                return prediction

            elif data_type == 'str':
                data_length = int.from_bytes(s.recv(4), byteorder='big')  
                prediction = s.recv(data_length).decode()  
                logging.info(f"Received string data: {prediction}")
                return prediction

            else:
                raise TypeError("Unknown data type received")

        except (TypeError) as e:
            logging.error(f"Error while receiving data: {e}")
            raise

