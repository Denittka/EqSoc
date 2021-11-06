import socket
from threading import Thread
from configparser import ConfigParser
from data.db_session import create_session
from data.__all_models import User, Peer


class Server:
    def __init__(self):
        self.initialized = False
        self.port = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client = socket.socket()
        self.connections = []
        self.accepting = None

    def ask_for_pubkey(self, address, port, my_pubkey):
        try:
            self.client.connect((address, port))
            self.client.send(bytes("1", encoding="utf-8"))
            pubkey = str(self.client.recv(4096), encoding="utf-8")
            self.client.send(bytes(my_pubkey, encoding="utf-8"))
            return pubkey
        except ConnectionAbortedError:
            return -1
        except ConnectionRefusedError:
            return -1

    def handle_request(self, data):
        result = ""
        session = create_session()
        if data == "0":
            pubkey = session.query(User).get(1).pubkey
            result = pubkey
        return result

    def handle_connection(self, conn, addr):
        while True:
            data = str(conn.recv(1024), encoding="utf-8")
            if data == "0":
                conn.send(bytes(self.handle_request(data), encoding="utf-8"))
                data = str(conn.recv(1024), encoding="utf-8")
                session = create_session()
                peer = Peer()
                peer.address = addr[0]
                peer.port = addr[1]
                peer.pubkey = data
                session.add(peer)
                session.commit()

    def loop(self):
        while True:
            conn, addr = self.sock.accept()
            thread = Thread(target=self.handle_connection, args=(conn, addr))
            thread.start()
            self.connections += [(conn, addr, thread)]

    def initialize(self):
        config = ConfigParser()
        config.read("./config.ini")
        port = int(config["SERVER"]["port"])
        address = config["SERVER"]["address"]
        print(address)
        try:
            self.sock.bind((address, port))
            self.sock.listen(10)
            self.port = port
            self.initialized = True
        except OSError:
            return port
        except OverflowError:
            return port
        self.accepting = Thread(target=self.loop)
        self.accepting.start()


class Client:
    pass
