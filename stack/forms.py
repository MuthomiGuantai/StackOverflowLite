from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_restful import fields

class UserForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired(message='User name is required'), Length(max=40)])
    email = StringField('Email', validators=[DataRequired(message='User email is required'), Email(), Length(max=80)])
    password = PasswordField('Password', validators=[DataRequired(message='User password is required'), Length(min=6)])
    confirm_password = PasswordField('Verify Password', validators=[DataRequired(message='Password confirmation is required'), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message='User email is required'), Email(), Length(max=80)])
    password = PasswordField('Password', validators=[DataRequired(message='User password is required')])
    submit = SubmitField('Login')

userFields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String
}