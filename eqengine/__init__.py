import socket
from threading import Thread
from configparser import ConfigParser
from data.db_session import create_session
from data.__all_models import User, Peer, Post
import sqlalchemy
import rsa


def verify(message, signature, pubkey):
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(pubkey)
    try:
        rsa.verify(message.encode(), bytes(signature, encoding="cp855"), pubkey)
        return True
    except rsa.pkcs1.VerificationError:
        return False


def ask_for_pubkey(address, port, my_pubkey):
    # Function of asking the peer for its pubkey.
    try:
        parser = ConfigParser()
        parser.read("config.ini")
        server_address = parser["SERVER"]["address"]
        server_port = parser["SERVER"]["port"]
        # * - Ask for pubkey with the code -> P
        # * <- Get the peer's pubkey - P
        # * - Send user's own pubkey -> P
        # * <- Get a response - P
        # * - Send user's server's address and port -> P
        client = socket.socket()
        client.connect((address, port))
        client.send(bytes("\x01", encoding="utf-8"))
        pubkey = str(client.recv(4096), encoding="utf-8")
        client.send(bytes(my_pubkey, encoding="utf-8"))
        client.recv(1024)
        client.send(bytes(f"{server_address};{server_port}", encoding="utf-8"))
        client.close()
        return pubkey
    except ConnectionAbortedError:
        return -1
    except ConnectionRefusedError:
        return -1


def ask_for_user(address, port, pubkey):
    # Ask for a user's data if a pubkey of its is met for the first time.
    session = create_session()
    client = socket.socket()
    client.connect((address, port))
    # * - Ask for with the code -> P
    # * <- Get a response - P
    # * - Send the pubkey -> P
    # * <- Get the user's data - P
    client.send(bytes("\x03", encoding="utf-8"))
    client.recv(1024)
    client.send(bytes(pubkey, encoding="utf-8"))
    data = client.recv(1024)
    if data == bytes("\x01", encoding="utf-8"):
        return -1
    user = User()
    data = str(data, encoding="utf-8").split(";")
    user.name = data[0]
    user.pubkey = pubkey
    user.description = data[1]
    session.add(user)
    session.commit()
    return 0


def search(text, except_list, self_address, self_port):
    # Search for the requested text.
    session = create_session()
    peers = session.query(Peer).all()
    result = []
    people = []
    except_list += [(self_address, self_port)]
    for peer in peers:
        if (peer.address, peer.port) in except_list:
            continue
        # * - Ask for with the code -> P
        # * <- Get a response - P
        # * - Send the request -> P
        # * <- Get a user's data - P
        # * - Send a response -> P
        # ...
        # * <- Get an ending byte - P
        client = socket.socket()
        client.connect((peer.address, peer.port))
        client.send(bytes("\x02", encoding="utf-8"))
        client.recv(1024)
        client.send(bytes(text, encoding="utf-8"))
        client.recv(1024)
        for passed in except_list:
            client.send(bytes(passed[0], encoding="utf-8"))
            client.recv(1024)
            client.send(bytes(str(passed[1]), encoding="utf-8"))
            client.recv(1024)
        client.send(bytes("\x01", encoding="utf-8"))
        while True:
            data = client.recv(1024)
            if data == bytes("\x01", encoding="utf-8"):
                break
            data = str(data, encoding="utf-8").split(";")
            user = User()
            user.pubkey = data[0]
            user.id = int(data[1])
            people += [user]
            client.send(bytes(1))
        # * - Send a response -> P
        # * <- Get a post's text - P
        # * - Send a response -> P
        # * <- Get the post's author's id - P
        # * - Send a response -> P
        # ...
        # * <- Get an ending byte - P
        client.send(bytes(1))
        while True:
            data = client.recv(1024)
            if data == bytes("\x01", encoding="utf-8"):
                break
            post = Post()
            post.text = str(data, encoding="utf-8")
            client.send(bytes(1))
            post.author = int(str(client.recv(1024), encoding="utf-8"))
            client.send(bytes(1))
            post.sign = str(client.recv(1024), encoding="utf-8")
            result += [post]
            client.send(bytes(1))
        client.close()
        for post in result:
            author = list(filter(lambda x: x.id == post.author, people))[0]
            searched_author = session.query(User).filter(User.pubkey == author.pubkey).first()
            if searched_author is None:
                committed = ask_for_user(peer.address, peer.port, author.pubkey)
                if committed == -1:
                    continue
                if committed == 0:
                    searched_author = session.query(User).filter(User.pubkey == author.pubkey).first()
            post.author = searched_author.id
            current_posts = session.query(Post).filter(Post.text == post.text and Post.author == post.author).all()
            if len(current_posts) == 0 and verify(post.text, post.sign, searched_author.pubkey):
                session.add(post)
        session.commit()
    return_results = []
    for post in result:
        return_results += [{"author": post.author, "text": post.text}]
    return return_results


class Server:
    def __init__(self):
        self.initialized = False
        self.address = None
        self.port = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []
        self.accepting = None

    def refresh(self):
        pass

    def handle_user_request(self, conn, session):
        # * <- Get a response - S
        # * - Send the pubkey -> S
        # * <- Get the user's data - S
        conn.send(bytes(1))
        pubkey = str(conn.recv(4096), encoding="utf-8")
        searched_user = session.query(User).filter(User.pubkey == pubkey).first()
        if searched_user is None:
            conn.send(bytes("\x01", encoding="utf-8"))
        else:
            conn.send(bytes(f"{searched_user.name};{searched_user.description}", encoding="utf-8"))

    def handle_pubkey_request(self, conn, session):
        # * <- Get the peer's pubkey - S
        # * - Send user's own pubkey -> S
        # * <- Get a response - S
        # * - Send user's server's address and port -> S
        pubkey = session.query(User).get(1).pubkey
        conn.send(bytes(pubkey, encoding="utf-8"))
        peers_pubkey = str(conn.recv(1024), encoding="utf-8")
        conn.send(bytes(1))
        address, port = str(conn.recv(1024), encoding="utf-8").split(";")
        peer = Peer()
        peer.address = address
        peer.port = int(port)
        peer.pubkey = peers_pubkey
        session.add(peer)
        session.commit()

    def handle_search_request(self, conn, session):
        # * <- Get a response - S
        # * - Send the request -> S
        # * <- Get a user's data - S
        # * - Send a response -> S
        # ...
        # * <- Get an ending byte - S
        conn.send(bytes(1))
        text = str(conn.recv(1024), encoding="utf-8")
        except_list = []
        conn.send(bytes(1))
        while True:
            address = str(conn.recv(1024), encoding="utf-8")
            if address == "\x01":
                break
            conn.send(bytes(1))
            port = int(str(conn.recv(1024), encoding="utf-8"))
            conn.send(bytes(1))
            except_list += [(address, port)]
        search(text, except_list, self.address, self.port)
        posts = session.query(Post).filter(sqlalchemy.func.lower(Post.text).like("%" + text.lower() + "%")).all()
        people = []
        for post in posts:
            author = session.query(User).get(post.author)
            if author not in people:
                people += [author]
        for author in people:
            conn.send(bytes(f"{author.pubkey};{author.id}", encoding="utf-8"))
            conn.recv(1024)
        conn.send(bytes("\x01", encoding="utf-8"))
        # * - Send a response -> S
        # * <- Get a post's text - S
        # * - Send a response -> S
        # * <- Get the post's author's id - S
        # * - Send a response -> S
        # ...
        # * <- Get an ending byte - S
        conn.recv(1024)
        for post in posts:
            conn.send(bytes(post.text, encoding="utf-8"))
            conn.recv(1024)
            conn.send(bytes(str(post.author), encoding="utf-8"))
            conn.recv(1024)
            conn.send(bytes(post.sign, encoding="utf-8"))
            conn.recv(1024)
        conn.send(bytes("\x01", encoding="utf-8"))

    def handle_connection(self, conn, index):
        # * - Ask for with the code -> S
        session = create_session()
        code = conn.recv(1024)
        if code == bytes("\x01", encoding="utf-8"):
            self.handle_pubkey_request(conn, session)
        if code == bytes("\x02", encoding="utf-8"):
            self.handle_search_request(conn, session)
        if code == bytes("\x03", encoding="utf-8"):
            self.handle_user_request(conn, session)
        conn.close()
        del self.connections[index]

    def loop(self):
        while True:
            conn, addr = self.sock.accept()
            thread = Thread(target=self.handle_connection, args=(conn, len(self.connections)))
            thread.start()
            self.connections += [(conn, addr, thread)]

    def initialize(self):
        config = ConfigParser()
        config.read("./config.ini")
        port = int(config["SERVER"]["port"])
        address = config["SERVER"]["address"]
        try:
            self.sock.bind((address, port))
            self.address = address
            self.port = port
            self.sock.listen(10)
            self.initialized = True
        except OSError:
            return port
        except OverflowError:
            return port
        self.accepting = Thread(target=self.loop)
        self.accepting.start()
