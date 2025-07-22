import random
import string
from flask_mail import Mail, Message

from flask import Flask, render_template, redirect, url_for, flash, make_response, request, jsonify
from datetime import timedelta, datetime
import os

from flask_jwt_extended import get_jwt_identity, jwt_required, create_access_token, verify_jwt_in_request, \
    unset_jwt_cookies, get_jwt

from stack.forms import UserForm, LoginForm, QuestionForm, AnswerForm, ChangePasswordForm
from stack.models import QuestionModel, UserModel, AnswerModel
from stack.dependencies import db,api,jwt

class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stackover.db'
    app.config['JWT_SECRET_KEY'] = '7f8d2a9b4c6e1f3d8a2b5c7e9d1f4a6b8c3e2d5f7a9b1c4e6d8f2a3b5c7e9d1'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SECRET_KEY'] = 'my-fixed-secret-key-for-development'
    app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']  # Enable cookies for JWT
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Simplified for development
    app.config['JWT_COOKIE_SECURE'] = False  # Allow non-HTTPS for localhost testing
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'  # Ensure cookie is sent with redirects
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token_cookie'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'bruceydev@gmail.com'
    app.config['MAIL_PASSWORD'] = 'hzxtvcynfoknlwzo'
    app.config['MAIL_DEFAULT_SENDER'] = 'bruceydev@gmail.com'

    db.init_app(app)
    api.init_app(app)
    jwt.init_app(app)
    mail = Mail(app)

    from .routes import Register, Login, Users, User
    api.add_resource(Register, '/api/register/')
    api.add_resource(Login, '/api/login/')
    api.add_resource(Users, '/api/users/')
    api.add_resource(User, '/api/users/<int:id>')

    @app.context_processor
    def inject_user():
            try:
                # Allow JWT verification for all routes, including '/'
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
                user = UserModel.query.filter_by(id=user_id).first() if user_id else None
                print(f"Injecting user: {user.name if user else None}")
                return dict(current_user=user)
            except Exception as e:
                print(f"Error in inject_user: {str(e)}")
                return dict(current_user=None)

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        print(f"Unauthorized access attempted: {str(error)}, Cookies: {request.cookies}")  # Debug
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"msg": "Please provide a valid JWT token in the Authorization header."}), 401
        flash("Please log in to access this page.", "error")
        return redirect(url_for('login'))

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"Invalid token error: {str(error)}, Cookies: {request.cookies}")  # Debug
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"msg": "Invalid or expired token. Please obtain a new token."}), 401
        flash("Invalid or expired token. Please log in again.", "error")
        response = make_response(redirect(url_for('login')))
        response.set_cookie('access_token_cookie', '', expires=0)  # Clear invalid token
        return response

    @app.route('/')
    def home():
        questions = QuestionModel.query.order_by(QuestionModel.date_posted.desc()).all()
        return render_template("index.html", title="HomePage", questions=questions)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = UserModel.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                access_token = create_access_token(identity=str(user.id))
                response = make_response(redirect(url_for('question')))
                response.set_cookie('access_token_cookie', access_token, httponly=True, max_age=60 * 60, samesite='lax')
                flash("Logged in successfully!", "success")
                return response
            else:
                flash("Incorrect username or password.", "error")
        return render_template("login.html", title="Login", form=form)


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = UserForm()
        if form.validate_on_submit():
            user = UserModel(
                name=form.username.data,
                email=form.email.data,
                password_hash=form.password.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            access_token = create_access_token(identity=str(user.id))
            response = make_response(redirect(url_for('question')))
            response.set_cookie('access_token_cookie', access_token, httponly=True, max_age=60 * 60, samesite='lax')
            flash("Registration successful! You are now logged in.", "success")
            return response
        else:
            flash("Registration failed. Please check your input.", "error")
        return render_template("register.html", title="Register", form=form)

    @app.route('/question', methods=['GET', 'POST'])
    @jwt_required()
    def question():
        user_id = get_jwt_identity()
        user = UserModel.query.filter_by(id=user_id).first()
        if not user:
            flash("User not found. Please log inBond: in again.", "error")
            return redirect(url_for('login'))
        form = QuestionForm()
        if form.validate_on_submit():
            question = QuestionModel(
                title=form.title.data,
                content=form.content.data,
                author=user.name
            )
            db.session.add(question)
            db.session.commit()
            flash("Question posted successfully!", "success")
            questions = QuestionModel.query.order_by(QuestionModel.date_posted.desc()).all()
            return render_template("question.html", title="Ask a Question", form=form, errors=form.errors,
                                   questions=questions)

        return render_template("question.html", title="Ask a Question", form=form, errors=form.errors)

    @app.route('/answer/<int:question_id>', methods=['GET', 'POST'])
    @jwt_required()
    def answer(question_id):
        user_id = get_jwt_identity()
        user = UserModel.query.filter_by(id=user_id).first()
        if not user:
            flash("User not found. Please log inBond: in again.", "error")
            return redirect(url_for('login'))
        form = AnswerForm()
        question = QuestionModel.query.filter_by(id=question_id).first_or_404()
        if form.validate_on_submit():
            answer = AnswerModel(
                content=form.content.data,
                author=user.name,
                question_id=question_id
            )
            db.session.add(answer)
            db.session.commit()
            return redirect(url_for('home'))
        return render_template("answer.html", title="Post an Answer", form=form, question=question, errors=form.errors)


    @app.route("/about")
    def about():
        from stack.models import QuestionModel
        questions = QuestionModel.query.order_by(QuestionModel.date_posted.desc()).all()
        return render_template("about.html", questions=questions)

    @app.route('/profile', methods=['GET', 'POST'])
    @jwt_required()
    def profile():
        user_id = get_jwt_identity()
        user = UserModel.query.filter_by(id=user_id).first()
        if not user:
            flash("User not found. Please log in again.", "error")
            return redirect(url_for('login'))
        form = UserForm()
        # Exclude password fields for profile editing
        form.password.validators = []
        form.confirm_password.validators = []
        if form.validate_on_submit():
            if UserModel.query.filter_by(email=form.email.data).first() and form.email.data != user.email:
                flash("Email already registered by another user.", "error")
            else:
                user.name = form.username.data
                user.email = form.email.data
                db.session.commit()
                flash("Profile updated successfully!", "success")
                return redirect(url_for('profile'))
        elif request.method == 'GET':
            form.username.data = user.name
            form.email.data = user.email
        questions = QuestionModel.query.filter_by(author=user.name).order_by(QuestionModel.date_posted.desc()).all()
        answers = AnswerModel.query.filter_by(author=user.name).order_by(AnswerModel.date_posted.desc()).all()
        change_password_form = ChangePasswordForm()
        return render_template("profile.html", user=user, title="Profile", questions=questions, answers=answers,
                               form=form, change_password_form=change_password_form)

    @app.route('/request-otp', methods=['POST'])
    @jwt_required()
    def request_otp():
        user_id = get_jwt_identity()
        user = UserModel.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"message": "User not found."}), 404
        otp = ''.join(random.choices(string.digits, k=6))
        user.otp = otp
        user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        try:
            msg = Message("Your OTP for Password Change", recipients=[user.email])
            msg.body = f"Your OTP is {otp}. It is valid for 10 minutes."
            msg.html = render_template('otp_email.html', otp=otp, user=user)
            mail.send(msg)
            return jsonify({"message": "OTP sent to your email."}), 200
        except Exception as e:
            print(f"Error sending OTP email: {str(e)}")
            return jsonify({"message": "Failed to send OTP. Please try again."}), 500

    @app.route('/change-password', methods=['POST'])
    @jwt_required()
    def change_password():
        user_id = get_jwt_identity()
        user = UserModel.query.filter_by(id=user_id).first()
        if not user:
            flash("User not found. Please log in again.", "error")
            return redirect(url_for('login'))
        form = ChangePasswordForm()
        if form.validate_on_submit():
            if not user.otp or user.otp_expiry < datetime.utcnow():
                flash("OTP is invalid or expired. Please request a new OTP.", "error")
                return redirect(url_for('profile'))
            if user.otp != form.otp.data:
                flash("Invalid OTP. Please try again.", "error")
                return redirect(url_for('profile'))
            user.set_password(form.new_password.data)
            user.otp = None
            user.otp_expiry = None
            db.session.commit()
            flash("Password changed successfully!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Invalid input. Please check the form.", "error")
        return redirect(url_for('profile'))

    @app.route('/logout')
    def logout():
        try:
            jwt_data = get_jwt()
            jti = jwt_data['jti']
            token = TokenBlocklist(jti=jti)
            db.session.add(token)
            db.session.commit()
        except Exception as e:
            print(f"Error adding token to blocklist: {str(e)}")
        response = make_response(redirect(url_for('login')))
        unset_jwt_cookies(response)  # Clears access_token_cookie
        flash("Logged out successfully!", "success")
        return response

    with app.app_context():

        db.create_all()

    return app
