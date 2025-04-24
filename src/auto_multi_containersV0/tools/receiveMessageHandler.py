import socket
import pickle
import struct
import json
import io


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
                "variable-name-length"
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
                    variable_name_len = self.jsonheader["variable-name-length"]
                    content_len = self.jsonheader["content-length"]
                    total_expected = variable_name_len + content_len
                    if len(self._recv_buffer) < total_expected:
                        # Not enough data yet for a complete message.
                        break

                    # Process the variable name.
                    if variable_name_len > 0:
                        var_name_bytes = self._recv_buffer[:variable_name_len]
                        variable_name = var_name_bytes.decode("utf-8")
                    else:
                        variable_name = f"variable_{i}"


                    # Remove variable name bytes.
                    self._recv_buffer = self._recv_buffer[variable_name_len:]
                    # Process the message content.
                    content_bytes = self._recv_buffer[:content_len]
                    self._recv_buffer = self._recv_buffer[content_len:]
                    msg = self._pickle_decode(content_bytes)
                    messages.append((variable_name, msg))

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