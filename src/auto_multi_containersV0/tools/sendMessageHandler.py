import socket
import pickle
import struct
import sys
import json
import logging


class SendMessageHandler:
    def __init__(self, sock: socket.socket, peer_addr, send_data: dict):
        """
        :param sock: Socket connection to the peer.
        :param peer_addr: The address (or identifier) of the peer.
        :param send_data: A dict containing the variables to send to the peer.
                          Format: { "variable_name": message_content, ... }
        """
        self.sock = sock
        self.peer_addr = peer_addr
        self.send_data = send_data
        # Using blocking mode for simplicity
        self.sock.setblocking(True)


    def _create_message(self, variable_name: str, msg_obj) -> bytes:
        """
        Constructs a full message according to our protocol:
          - First 2 bytes: length of JSON header (big-endian)
          - JSON header: contains keys "byteorder", "content-length", "variable-name-length"
          - Optional variable name bytes (UTF-8)
          - Pickled message content
        """
        # Serialize the message content
        msg_bytes = pickle.dumps(msg_obj)
        content_length = len(msg_bytes)

        # Encode the variable name (if provided)
        if variable_name:
            var_name_bytes = variable_name.encode("utf-8")
        else:
            var_name_bytes = b""
        variable_name_length = len(var_name_bytes)

        # Build the JSON header
        json_header = {
            "byteorder": sys.byteorder,
            "content-length": content_length,
            "variable-name-length": variable_name_length
        }
        json_header_bytes = json.dumps(json_header).encode("utf-8")
        json_header_length = len(json_header_bytes)

        # Pack the length of the JSON header as 2 bytes (big-endian)
        proto_header = struct.pack(">H", json_header_length)

        # Concatenate all parts: proto header + JSON header + variable name + content
        full_message = proto_header + json_header_bytes + var_name_bytes + msg_bytes
        return full_message


    def send_all_messages(self):
        """
        Loops through the send_data dictionary and sends each message.
        """
        for variable_name, message_content in self.send_data.items():
            full_message = self._create_message(variable_name, message_content)
            try:
                self.sock.sendall(full_message)
                print(f"[CLIENT] Sent message for variable '{variable_name}' to {self.peer_addr}")
                logging.info(f"[CLIENT] Sent message for variable '{variable_name}' to {self.peer_addr}")
            except Exception as e:
                print(f"[CLIENT] Error sending message for '{variable_name}' to {self.peer_addr}: {e}")