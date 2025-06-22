from pyexpat.errors import messages

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from flask_jwt_extended import  JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stackover.db'
app.config['JWT_SECRET_KEY'] = '7f8d2a9b4c6e1f3d8a2b5c7e9d1f4a6b8c3e2d5f7a9b1c4e6d8f2a3b5c7e9d1'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
db = SQLAlchemy(app)
api = Api(app)
jwt = JWTManager(app)

class UserModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f"User(name = {self.name}, email = {self.email}"
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

user_args = reqparse.RequestParser()
user_args.add_argument('name', type=str, required=True, help='User name is required')
user_args.add_argument('email', type=str, required=True, help='User email is required')
user_args.add_argument('password', type=str, required=True, help='User password is required')
userFields = {
    'id': fields.Integer,
    'name':fields.String,
    'email':fields.String
}

login_args = reqparse.RequestParser()
login_args.add_argument('email', type=str, required=True, help='User email is required')
login_args.add_argument('password', type=str, required=True, help='User password is required')

class Register(Resource):
    @marshal_with(userFields)
    def post(self):
        args = user_args.parse_args()
        if UserModel.query.filter_by(email=args['email']).first():
            abort(409, message="Email already registered")
        user = UserModel(name=args['name'], email=args['email'])
        user.set_password(args['password'])
        db.session.add(user)
        db.session.commit()
        return user, 201
class Login(Resource):
    def post(self):
        args = login_args.parse_args()
        user = UserModel.query.filter_by(email=args['email']).first()
        if not user or not user.check_password(args['password']):
            abort(409, messages='Invalid email or password')
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
        args = user_args.parse_args()
        if UserModel.query.filter_by(email=args['email']).first():
            abort(409, message="Email already registered")
        user = UserModel(name=args['name'], email=args['email'])
        user.set_password(args['password'])
        db.session.add(user)
        db.session.commit()
        users = UserModel.query.all()
        return users, 201

class User(Resource):
    @marshal_with(userFields)
    @jwt_required()
    def patch(self, id):
        args = user_args.parse_args()
        user = UserModel.query.filter_by(id=id).first()
        if not user:
            abort(404, message = "User not found")
        if user.id != get_jwt_identity():
            abort(403, message = "unauthorized to modify user")
        user.name = args['name']
        user.email = args['email']
        user.set_password(args['password'])
        db.session.commit()
        return user

    @marshal_with(userFields)
    @jwt_required()
    def delete(self, id):
        user = UserModel.query.filter_by(id=id).first()
        if not user:
            abort(404, message = "User not found")
        if user.id != get_jwt_identity():
            abort(403, message = "unauthorized to delete user")
        db.session.delete(user)
        db.session.commit()
        return user, 204

api.add_resource(Register, '/api/register/')
api.add_resource(Login, '/api/login/')
api.add_resource(Users, '/api/users/')
api.add_resource(User, '/api/users/<int:id>')





@app.route('/')
def home():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
