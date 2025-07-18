from flask import Flask,render_template,redirect,url_for
from datetime import timedelta
import os

from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Api

from stack.forms import UserForm, LoginForm, QuestionForm, AnswerForm
from stack.models import QuestionModel, UserModel, AnswerModel
from stack.dependencies import db,api,jwt



def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stackover.db'
    app.config['JWT_SECRET_KEY'] = '7f8d2a9b4c6e1f3d8a2b5c7e9d1f4a6b8c3e2d5f7a9b1c4e6d8f2a3b5c7e9d1'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=60)
    app.config['SECRET_KEY'] = os.urandom(24)  # Required for Flask-WTF CSRF protection

    db.init_app(app)
    api.init_app(app)
    jwt.init_app(app)

    from .routes import Register, Login, Users, User
    api.add_resource(Register, '/api/register/')
    api.add_resource(Login, '/api/login/')
    api.add_resource(Users, '/api/users/')
    api.add_resource(User, '/api/users/<int:id>')

    @app.route('/')
    def home():
        questions = QuestionModel.query.order_by(QuestionModel.date_posted.desc()).all()
        return render_template("index.html", title="HomePage", questions=questions)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            # This assumes you handle form submission via the API
            return redirect(url_for('question'))
        return render_template("login.html", title="Login", form=form)

    """@app.route("/about")
    def about():
        return render_template("about.html")"""

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = UserForm()
        if form.validate_on_submit():
            # This assumes you handle form submission via the API
            return redirect(url_for('question'))
        return render_template("register.html", title="Register", form=form)

    @app.route('/question', methods=['GET', 'POST'])
    def question():
        form = QuestionForm()
        if form.validate_on_submit():
            print("Question form validated successfully:", form.data)  # Debug
            # Save question to database
            question = QuestionModel(
                title=form.title.data,
                content=form.content.data,
                author="Anonymous"  # Placeholder; replace with authenticated user if needed
            )
            db.session.add(question)
            db.session.commit()
            return redirect(url_for('about'))
        print("Question form submission failed:", form.data, form.errors)  # Debug

        return render_template("question.html", title="Ask a Question", form=form, errors=form.errors)

    @app.route('/answer/<int:question_id>', methods=['GET', 'POST'])
    def answer(question_id):
        form = AnswerForm()
        question = QuestionModel.query.filter_by(id=question_id).first_or_404()
        if form.validate_on_submit():
            answer = AnswerModel(
                content=form.content.data,
                author="Anonymous",  # Replace with authenticated user if needed
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
    
    with app.app_context():

        db.create_all()  # Create database tables

    return app
