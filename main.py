from flask_login import LoginManager, current_user, login_required, login_user
from flask import Flask, redirect, render_template
from data.db_session import create_session, global_init
from data.forms import RegistrationForm, AddPeerForm, NewPort
from data.__all_models import User, Peer
from eqengine import Client, Server, ConfigParser
from functools import wraps

app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = 'piuhPIDFUSHG<-I\'llNeverBeAloneAgain?->KOJDSkfoijds'
login_manager = LoginManager()
login_manager.init_app(app)
server = Server()
port = server.initialize()


def check(function):
    @wraps(function)
    def checking_function():
        if server.initialized:
            return function()
        return redirect("/set_port")
    return checking_function


@app.route("/set_port", methods=["GET", "POST"])
def set_port():
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
    return render_template("set_port.html", port=port, form=form)



@login_manager.user_loader
def load_user(user_id):
    session = create_session()
    return session.query(User).get(user_id)


@login_manager.unauthorized_handler
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    session = create_session()
    if form.validate_on_submit():
        if form.public_key.data.strip() != "" and form.public_key.data.strip() == "" \
                or form.public_key.data.strip() == "" and form.private_key.data.strip() != "":
            return render_template("register.html", errors=["There are not another key in the fields"], form=form)
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
    return render_template("register.html", errors=[], form=form)


@app.route("/add_peer", methods=["GET", "POST"])
@check
@login_required
def add_peer():
    session = create_session()
    form = AddPeerForm()
    if form.validate_on_submit():
        peer = Peer()
        peer.address = form.address.data
        peer.port = form.port.data
        peer.pubkey = server.ask_pubkey(peer.address, peer.port)
        session.add(peer)
        session.commit()
    return render_template("add_peer.html", form=form, error=[])


@app.route("/", methods=['GET', 'POST'])
@check
@login_required
def index():
    return ""


if __name__ == '__main__':
    config = ConfigParser()
    config.read("config.ini")
    global_init("db/database.db")
    session = create_session()
    user = session.query(User).get(0)
    if user is not None:
        login_user(user)
    app.run()
