from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, BooleanField, PasswordField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):
    search = StringField("Search", validators=[DataRequired()])
    submit = SubmitField("Search")


class NewPort(FlaskForm):
    port = IntegerField("Port", validators=[DataRequired()])
    submit = SubmitField("Try on")


class FollowForm(FlaskForm):
    submit = SubmitField("Follow")


class NewPostForm(FlaskForm):
    text = TextAreaField("Enter the text", validators=[DataRequired()])
    submit = SubmitField("Post")


class RegistrationForm(FlaskForm):
    name = StringField("Your name", validators=[DataRequired()])
    description = TextAreaField("Description")
    private_key = TextAreaField("Your Private Key")
    public_key = TextAreaField("Your Public Key")
    new_password = PasswordField("Your Password")
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    password = StringField("The Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class AddPeerForm(FlaskForm):
    address = StringField("Peer's Address", validators=[DataRequired()])
    port = IntegerField("Port", validators=[DataRequired()])
    submit = SubmitField("Send")


class ChangePasswordForm(FlaskForm):
    new_password = StringField("New password")
    turn_on = BooleanField("Turn on security password")
    submit = SubmitField("Save")
