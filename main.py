from data.forms import RegistrationForm, AddPeerForm, SearchForm, NewPostForm, FollowForm
from flask_login import LoginManager, current_user, login_required, login_user
from data.db_session import create_session, global_init
from flask import Flask, redirect, render_template
from data.__all_models import User, Peer, Post, Follow
from eqengine import Server, search, ask_for_pubkey, ask_for_users_posts
from functools import wraps
from configparser import ConfigParser
import atexit
import rsa

app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = 'piuhPIDFUSHG<-I\'Youllalwaysbethatstate?->KOJDSkfoijds'
login_manager = LoginManager()
login_manager.init_app(app)
server = Server()
port = server.initialize()


def __search(session, form):
    # Function of searching.
    if form.validate_on_submit():
        results = search(form.search.data, [], server.address, server.port)
        for i in range(len(results)):
            current_author = session.query(User).get(results[i]["author"])
            results[i]["name"] = current_author.name
        return results


def check(curr_function):
    # Function to check whether server is initialized before accessing the app.
    @wraps(curr_function)
    def checking_function():
        if server.initialized:
            return curr_function()
        return redirect("/set_port")
    return checking_function


@app.route("/set_port", methods=["GET", "POST"])
def set_port():
    # A page to inform a user of a server error.
    if server.initialized:
        return redirect("/")
    search_form = SearchForm()
    session = create_session()
    __search(session, search_form)
    return render_template("set_port.html", port=port, search=search_form)


@login_manager.user_loader
def load_user(user_id):
    # Function to login a user.
    session = create_session()
    return session.query(User).get(user_id)


@login_manager.unauthorized_handler
@app.route("/register", methods=['GET', 'POST'])
def register():
    # If there is no user, creates the first one.
    form = RegistrationForm()
    search_form = SearchForm()
    session = create_session()
    check_user = session.query(User).get(1)
    if check_user is not None:
        login_user(check_user)
    if current_user.is_authenticated:   # Does not allow a user to register a new user.
        return redirect("/")
    results = __search(session, search_form)
    if results is not None and len(results) != 0:
        return render_template("search.html", results=results, search=SearchForm())
    if form.validate_on_submit():
        if form.public_key.data.strip() != "" and form.public_key.data.strip() == "" \
                or form.public_key.data.strip() == "" and form.private_key.data.strip() != "":
            return render_template("register.html", errors=["There are not another key in the fields"], form=form,
                                   search=search_form)
        new_user = User()
        new_user.name = form.name.data.strip()  # Besides, if a person creates a new user, it would be just an entity.
        new_user.description = form.description.data.strip()    # No problem.
        new_user.pubkey = form.public_key.data.strip()
        session.add(new_user)
        session.commit()
        file = open("data/private.pem", "w")
        file.write(form.private_key.data)
        file.close()
        login_user(new_user)
        return redirect("/")
    return render_template("register.html", errors=[], form=form, search=search_form)


@app.route("/add_peer", methods=["GET", "POST"])
@check
@login_required
def add_peer():
    # A page to add a new peer.
    search_form = SearchForm()
    session = create_session()
    results = __search(session, search_form)
    if results is not None and len(results) != 0:
        return render_template("search.html", results=results, search=SearchForm())
    form = AddPeerForm()
    errors = []
    if form.validate_on_submit():
        peer = Peer()
        peer.address = form.address.data
        peer.port = form.port.data
        my_pubkey = session.query(User).get(1).pubkey
        peer.pubkey = ask_for_pubkey(peer.address, peer.port, my_pubkey)
        if peer.pubkey == -1:
            errors += ["This Peer does not answer"]
            return render_template("add_peer.html", form=form, errors=errors, search=search_form)
        session.add(peer)
        session.commit()
        return redirect("/add_peer")
    return render_template("add_peer.html", form=form, errors=[], search=search_form)


@app.route("/", methods=['GET', 'POST'])
@check
@login_required
def index():
    # The main page itself.
    server.refresh()
    search_form = SearchForm()
    session = create_session()
    results = __search(session, search_form)
    if results is not None and len(results) != 0:
        return render_template("search.html", results=results, search=SearchForm())
    form = NewPostForm()
    posts = [{
        "author": post.author,
        "name": session.query(User).get(post.author).name,
        "text": post.text,
    } for post in session.query(Post).all()]
    if form.validate_on_submit():
        post = Post()
        post.text = form.text.data
        post.author = current_user.id
        try:
            privkey = rsa.PrivateKey.load_pkcs1(bytes(open("data/private.pem").read(), encoding="utf-8"))
        except ValueError:
            return render_template("index.html", search=search_form, form=form, posts=posts,
                                   error="There is a problem with your private key")
        post.sign = str(rsa.sign(post.text.encode(), privkey, "SHA-1"), encoding="cp855")
        session.add(post)
        session.commit()
        return redirect("/")
    return render_template("index.html", search=search_form, form=form, posts=posts)


@app.route("/user/<int:user_id>", methods=['GET', 'POST'])
@login_required
def user(user_id: int):
    # The page of a user.
    search_form = SearchForm()
    follow = FollowForm()
    session = create_session()
    following = session.query(Follow).filter(Follow.follower == current_user.id and Follow.followed == user_id).first()
    is_followed = False if following is None else True
    results = __search(session, search_form)
    if results is not None and len(results) != 0:
        return render_template("search.html", results=results, search=SearchForm())
    got_user = session.query(User).get(user_id)
    if follow.validate_on_submit():
        if is_followed:
            session.delete(following)
            session.commit()
        else:
            new_follow = Follow()
            new_follow.follower = current_user.id
            new_follow.followed = user_id
            session.add(new_follow)
            session.commit()
        return redirect(f"/user/{str(user_id)}")
    if got_user is None:
        got_user = User()
        got_user.name = "Error"
        got_user.description = "Error"
    else:
        ask_for_users_posts(got_user.id)
    posts = session.query(Post).filter(Post.author == got_user.id).all()
    return render_template("user.html", user=got_user, search=search_form, posts=posts, follow=follow,
                           is_followed=is_followed, current_user=current_user)


def shutdown():
    # Threading needs to have the join function anywhere in the code. So it's here.
    server.accepting.join()
    for conn in server.connections:
        conn[-1].join()


if __name__ == '__main__':
    atexit.register(shutdown)   # Registering the join functions.
    global_init("db/database.db")
    parser = ConfigParser()
    parser.read("config.ini")
    flask_port = int(parser["SERVER"]["flaskPort"])
    app.run(port=flask_port)
