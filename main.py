from flask_login import LoginManager, current_user, login_required
from flask import Flask, redirect, render_template
from data.db_session import create_session, global_init
from data.forms import RegistrationForm
from data.__all_models import User

app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = 'piuhPIDFUSHG<-I\'llNeverBeAloneAgain?->KOJDSkfoijds'
login_manager = LoginManager()
login_manager.init_app(app)


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
    return render_template("register.html", errors=[], form=form)


@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    pass


if __name__ == '__main__':
    global_init("db/database.db")
    session = create_session()
    app.run()
