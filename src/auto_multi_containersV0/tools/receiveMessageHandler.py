import socket
import pickle
import logging
import struct
import json
import io
import time


# class ReceiveMessageHandler:
#     def __init__(self, sock: socket.socket, addr):
#         self.sock = sock
#         self.addr = addr
#         # we'll read in blocking mode here for simplicity
#         self.sock.setblocking(True)
#         self._recv_buffer = b""
#         self._msg_len = None

#     def _read_from_socket(self):
#         """
#         Read as much as available (up to 4096 bytes) into our buffer.
#         Returns False if the peer cleanly closed the connection.
#         """
#         try:
#             data = self.sock.recv(4096)
#         except socket.error as e:
#             raise
#         if not data:
#             # peer closed
#             return False
#         self._recv_buffer += data
#         return True

#     def recv_all_messages(self):
#         """
#         Attempt to read exactly one batch payload, decode it, and return
#         a list of (variable_name, value) pairs.  If not enough data yet,
#         returns an empty list.
#         """
#         messages = []

#         # 1) Read from socket until we have at least 4 bytes for length
#         while self._msg_len is None and len(self._recv_buffer) < 4:
#             if not self._read_from_socket():
#                 return []  # connection closed before header

#         # 2) Extract the 4-byte length prefix if we haven't yet
#         if self._msg_len is None and len(self._recv_buffer) >= 4:
#             self._msg_len = struct.unpack(">I", self._recv_buffer[:4])[0]
#             self._recv_buffer = self._recv_buffer[4:]

#         # 3) Read until we have the full payload
#         while len(self._recv_buffer) < self._msg_len:
#             if not self._read_from_socket():
#                 return []  # connection closed prematurely

#         # 4) We now have at least _msg_len bytes: extract payload
#         payload = self._recv_buffer[: self._msg_len]
#         self._recv_buffer = self._recv_buffer[self._msg_len :]
#         self._msg_len = None  # reset for next batch

#         # 5) Unpickle the dict and emit (key, value) pairs
#         try:
#             data_dict = pickle.loads(payload)
#         except Exception as e:
#             logging.error(f"[SERVER] Failed to unpickle batch from {self.addr}: {e}")
#             return []

#         messages.append(data_dict['container_creds_xxx'])
#         for var_name, value in data_dict.items():
#             if var_name=='container_creds_xxx':
#                 continue
#             messages.append((var_name, value))
#             logging.info(f"[SERVER] Received variable '{var_name}' from {self.addr}")

#         return messages


class ReceiveMessageHandler:
    
    def __init__(self, sock : socket.socket, addr):
        self.sock = sock
        self.sock.setblocking(False)
        self.addr = addr
        self._recv_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.msg = None
    
    
    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")
    

    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)


    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj
    

    def _pickle_decode(self, pkl_bytes):
        return pickle.loads(pkl_bytes)
        
    
    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]
    

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:hdrlen], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
                "sent-ts"
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f"Missing required header '{reqhdr}'.")


    def recv_all_messages(self):
        messages = []
        i = 1
        try:
            while True:
                # Read any available data.
                self._read()
                # if not self._read():
                #     # If _read() returns False, the connection is closed.
                #     print(f"[SERVER] Connection closed by peer {self.addr}")
                #     break
                # If we don't yet have the proto header, try to process it.
                if self._jsonheader_len is None and len(self._recv_buffer) >= 2:
                    self.process_protoheader()

                # Process JSON header if possible.
                if self._jsonheader_len is not None and self.jsonheader is None:
                    if len(self._recv_buffer) >= self._jsonheader_len:
                        self.process_jsonheader()

                # If we have a JSON header, check if the full message is available.
                if self.jsonheader is not None:
                    content_len = self.jsonheader["content-length"]
                    sent_ts = self.jsonheader.get("sent-ts")
                    total_expected = content_len
                    if len(self._recv_buffer) < total_expected:
                        # Not enough data yet for a complete message.
                        break
                    
                    #compute the latency
                    recv_ts = time.time()
                    latency = (recv_ts - sent_ts) if sent_ts is not None else None

                    content_bytes = self._recv_buffer[:content_len]
                    self._recv_buffer = self._recv_buffer[content_len:]
                    data_dict = self._pickle_decode(content_bytes)


                    messages.append((data_dict['container_creds_xxx'], latency))
                    for var_name, value in data_dict.items():
                        if var_name=='container_creds_xxx':
                            continue
                        messages.append((var_name, value))
                    # for variable_name, content in data_dict.items():
                    #     messages.append((variable_name, content))

                    # Reset header info so that we can process the next message.
                    self._jsonheader_len = None
                    self.jsonheader = None
                    i+=1
                else:
                    break
        except RuntimeError as e:
        # When the peer closes the connection, _read() will raise a RuntimeError.
            if str(e) == "Peer closed.":
                # print(f"[SERVER] Connection closed by peer {self.addr}")
                pass
            else:
                raise

        return messages