from flask_login import LoginManager, current_user, login_required, login_user
from flask import Flask, redirect, render_template
from data.db_session import create_session, global_init
from data.forms import RegistrationForm, AddPeerForm, NewPort, SearchForm, NewPostForm
from data.__all_models import User, Peer, Post
from eqengine import Client, Server, ConfigParser
from functools import wraps
import datetime
import atexit

app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = 'piuhPIDFUSHG<-I\'llNeverBeAloneAgain?->KOJDSkfoijds'
login_manager = LoginManager()
login_manager.init_app(app)
server = Server()
port = server.initialize()


def __search(session, form):
    if form.validate_on_submit():
        pass


def check(function):
    @wraps(function)
    def checking_function():
        if server.initialized:
            return function()
        return redirect("/set_port")
    return checking_function


@app.route("/set_port", methods=["GET", "POST"])
def set_port():
    if server.initialized:
        return redirect("/")
    search = SearchForm()
    session = create_session()
    __search(session, search)
    form = NewPort()
    global port
    if form.validate_on_submit():
        config = ConfigParser()
        config.read("config.ini")
        config["SERVER"]["port"] = str(form.port.data)
        with open("config.ini", "w") as configfile:
            config.write(configfile)
        port = server.initialize()
        return redirect("/")
    return render_template("set_port.html", port=port, form=form, search=search)



@login_manager.user_loader
def load_user(user_id):
    session = create_session()
    return session.query(User).get(user_id)


@login_manager.unauthorized_handler
@app.route("/register", methods=['GET', 'POST'])
@check
def register():
    form = RegistrationForm()
    search = SearchForm()
    session = create_session()
    user = session.query(User).get(1)
    if user is not None:
        login_user(user)
    if current_user.is_authenticated:
        return redirect("/")
    __search(session, search)
    if form.validate_on_submit():
        if form.public_key.data.strip() != "" and form.public_key.data.strip() == "" \
                or form.public_key.data.strip() == "" and form.private_key.data.strip() != "":
            return render_template("register.html", errors=["There are not another key in the fields"], form=form,
                                   search=search)
        user = User()
        user.name = form.name.data.strip()
        user.description = form.description.data.strip()
        user.pubkey = form.public_key.data.strip()
        session.add(user)
        session.commit()
        file = open("data/private_key.dat", "w")
        file.write(form.private_key.data)
        login_user(user)
        return redirect("/")
    return render_template("register.html", errors=[], form=form, search=search)


@app.route("/add_peer", methods=["GET", "POST"])
@check
@login_required
def add_peer():
    search = SearchForm()
    session = create_session()
    __search(session, search)
    form = AddPeerForm()
    errors = []
    if form.validate_on_submit():
        peer = Peer()
        peer.address = form.address.data
        peer.port = form.port.data
        my_pubkey = session.query(User).get(1).pubkey
        peer.pubkey = server.ask_for_pubkey(peer.address, peer.port, my_pubkey)
        if peer.pubkey == -1:
            errors += ["This Peer does not answer"]
            return render_template("add_peer.html", form=form, errors=errors, search=search)
        session.add(peer)
        session.commit()
        errors = ["Peer has been successfully added"]
        form = AddPeerForm()
    return render_template("add_peer.html", form=form, errors=[], search=search)


@app.route("/", methods=['GET', 'POST'])
@check
@login_required
def index():
    search = SearchForm()
    session = create_session()
    __search(session, search)
    form = NewPostForm()
    posts = [{
        "author": post.author,
        "name": session.query(User).get(post.author).name,
        "text": post.text,
        "datetime": post.datetime
    } for post in session.query(Post).all()]
    if form.validate_on_submit():
        post = Post()
        post.text = form.text.data
        post.datetime = datetime.datetime.now()
        post.author = current_user.id
        session.add(post)
        session.commit()
        return redirect("/")
    return render_template("index.html", search=search, form=form, posts=posts)


@app.route("/user/<int:user_id>", methods=['GET', 'POST'])
@login_required
def user(user_id: int):
    search = SearchForm()
    session = create_session()
    __search(session, search)
    user = session.query(User).get(user_id)
    if user is None:
        user = User()
        user.name = "Error"
        user.description = "Error"
    posts = session.query(Post).filter(Post.author == user.id).all()
    return render_template("user.html", user=user, search=search, posts=posts)


def shutdown():
    server.accepting.join()
    for conn in server.connections:
        conn[-1].join()


if __name__ == '__main__':
    atexit.register(shutdown)
    config = ConfigParser()
    config.read("config.ini")
    global_init("db/database.db")
    app.run()
