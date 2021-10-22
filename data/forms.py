from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired


class NewPort(FlaskForm):
    port = IntegerField("Port", validators=[DataRequired()])
    submit = SubmitField("Try on")


class Follow(FlaskForm):
    submit = SubmitField("Follow")


class NewPostForm(FlaskForm):
    text = StringField("Enter the text", validators=[DataRequired()])
    submit = SubmitField("Post")


class RegistrationForm(FlaskForm):
    name = StringField("Your name", validators=[DataRequired()])
    description = TextAreaField("Description")
    private_key = TextAreaField("Your Private Key")
    public_key = TextAreaField("Your Public Key")
    submit = SubmitField("Sign Up")


class AddPeerForm(FlaskForm):
    address = StringField("Peer's Address", validators=[DataRequired()])
    port = IntegerField("Port", validators=[DataRequired()])
    submit = SubmitField("Send")
