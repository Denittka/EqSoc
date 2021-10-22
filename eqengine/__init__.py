import socket
from configparser import ConfigParser


class Server:
    def __init__(self):
        self.initialized = False
        self.port = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def initialize(self):
        config = ConfigParser()
        config.read("./config.ini")
        port = int(config["SERVER"]["port"])
        try:
            self.sock.bind(("127.0.0.1", port))
            self.port = port
            self.initialized = True
        except OSError:
            return port
        except OverflowError:
            return port


class Client:
    pass
