from werkzeug.security import generate_password_hash, check_password_hash
from stack.dependencies import db
from datetime import datetime


class UserModel(db.Model):
    __tablename__ = 'user_model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(80), nullable=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"User(name='{self.name}', email='{self.email}')"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class QuestionModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(40), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    answers = db.relationship('AnswerModel', backref='question', lazy=True)

    def __repr__(self):
        return f"Question(title = {self.title}, author = {self.author}, date_posted = {self.date_posted})"

class AnswerModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(40), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    question_id = db.Column(db.Integer, db.ForeignKey('question_model.id'), nullable=False)

    def __repr__(self):
        return f"Answer(content = {self.content[:50]}, author = {self.author}, date_posted = {self.date_posted})"