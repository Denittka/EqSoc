from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Email


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
