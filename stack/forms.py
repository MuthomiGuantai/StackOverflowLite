from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
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

class QuestionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(message='Question title is required'), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired(message='Question content is required'), Length(max=5000)])
    submit = SubmitField('Post Question')

class AnswerForm(FlaskForm):
    content = TextAreaField('Answer', validators=[DataRequired(message='Answer content is required'), Length(max=5000)])
    submit = SubmitField('Post Answer')

class ChangePasswordForm(FlaskForm):
    otp = StringField('OTP', validators=[DataRequired(message='OTP is required'), Length(min=6, max=6, message='OTP must be 6 digits')])
    new_password = PasswordField('New Password', validators=[DataRequired(message='New password is required'), Length(min=6, message='Password must be at least 6 characters')])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(message='Password confirmation is required'), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password')


userFields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String
}