from flask import request, jsonify
from flask_restful import Resource, abort, marshal_with
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from .forms import UserForm, LoginForm, userFields
from .models import UserModel, db



class Register(Resource):
    @marshal_with(userFields)
    def post(self):
        form = UserForm()
        if not form.validate_on_submit():
            errors = {field: errors for field, errors in form.errors.items()}
            abort(400, message=errors)
        if UserModel.query.filter_by(email=form.email.data).first():
            abort(409, message="Email already registered")
        user = UserModel(name=form.username.data, email=form.email.data)  # Changed form.name to form.username
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return user, 201


class Login(Resource):
    def post(self):
        form = LoginForm()
        if not form.validate_on_submit():
            errors = {field: errors for field, errors in form.errors.items()}
            abort(400, message=errors)
        user = UserModel.query.filter_by(email=form.email.data).first()
        if not user or not user.check_password(form.password.data):
            abort(401, message="Invalid email or password")
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token)


class Users(Resource):
    @marshal_with(userFields)
    @jwt_required()
    def get(self):
        users = UserModel.query.all()
        return users

    @marshal_with(userFields)
    @jwt_required()
    def post(self):
        form = UserForm()
        if not form.validate_on_submit():
            errors = {field: errors for field, errors in form.errors.items()}
            abort(400, message=errors)
        if UserModel.query.filter_by(email=form.email.data).first():
            abort(409, message="Email already registered")
        user = UserModel(name=form.username.data, email=form.email.data)  # Changed form.name to form.username
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        users = UserModel.query.all()
        return users, 201


class User(Resource):
    @marshal_with(userFields)
    @jwt_required()
    def patch(self, id):
        form = UserForm()
        if not form.validate_on_submit():
            errors = {field: errors for field, errors in form.errors.items()}
            abort(400, message=errors)
        user = UserModel.query.filter_by(id=id).first()
        if not user:
            abort(404, message="User not found")
        if user.id != int(get_jwt_identity()):
            abort(403, message="Unauthorized to modify user")
        user.name = form.username.data  # Changed form.name to form.username
        user.email = form.email.data
        user.set_password(form.password.data)
        db.session.commit()
        return user

    @marshal_with(userFields)
    @jwt_required()
    def delete(self, id):
        user = UserModel.query.filter_by(id=id).first()
        if not user:
            abort(404, message="User not found")
        if user.id != int(get_jwt_identity()):
            abort(403, message="Unauthorized to delete user")
        db.session.delete(user)
        db.session.commit()
        return user, 204


