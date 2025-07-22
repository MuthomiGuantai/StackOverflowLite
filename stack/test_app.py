import unittest
import pytest
from flask import url_for
from flask_jwt_extended import create_access_token
from stack import create_app
from stack.models import UserModel, QuestionModel, AnswerModel
from stack import TokenBlocklist
from stack.dependencies import db
from datetime import datetime, timedelta
import json


class FlaskAppTests(unittest.TestCase):
    def setUp(self):
        """Set up test environment with in-memory SQLite database."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create a test user
            self.test_user = UserModel(name="testuser", email="test@example.com")
            self.test_user.set_password("TestPassword123")
            db.session.add(self.test_user)
            db.session.commit()
            self.user_id = self.test_user.id

    def tearDown(self):
        """Tear down test environment."""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_home_page(self):
        """Test the home page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'HomePage', response.data)

    def test_register_success(self):
        """Test successful user registration."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPassword123',
            'confirm_password': 'NewPassword123'
        }
        response = self.client.post('/register', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)
        with self.app.app_context():
            user = UserModel.query.filter_by(email='newuser@example.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'newuser')

    def test_register_failure_duplicate_email(self):
        """Test registration with duplicate email."""
        data = {
            'username': 'testuser2',
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'confirm_password': 'TestPassword123'
        }
        response = self.client.post('/register', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration failed', response.data)

    def test_login_success(self):
        """Test successful login."""
        data = {
            'email': 'test@example.com',
            'password': 'TestPassword123'
        }
        response = self.client.post('/login', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in successfully', response.data)
        self.assertIn('access_token_cookie', response.headers.get('Set-Cookie', ''))

    def test_login_failure_wrong_password(self):
        """Test login with incorrect password."""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        response = self.client.post('/login', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Incorrect username or password', response.data)

    def test_question_post_authenticated(self):
        """Test posting a question when authenticated."""
        with self.app.app_context():
            access_token = create_access_token(identity=str(self.user_id))
        headers = {'Cookie': f'access_token_cookie={access_token}'}
        data = {
            'title': 'Test Question',
            'content': 'This is a test question content.'
        }
        response = self.client.post('/question', data=data, headers=headers, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Question posted successfully', response.data)
        with self.app.app_context():
            question = QuestionModel.query.filter_by(title='Test Question').first()
            self.assertIsNotNone(question)
            self.assertEqual(question.author, 'testuser')

    def test_question_post_unauthenticated(self):
        """Test posting a question without authentication."""
        data = {
            'title': 'Test Question',
            'content': 'This is a test question content.'
        }
        response = self.client.post('/question', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in to access this page', response.data)

    def test_answer_post_authenticated(self):
        """Test posting an answer when authenticated."""
        with self.app.app_context():
            question = QuestionModel(title='Test Question', content='Test content', author='testuser')
            db.session.add(question)
            db.session.commit()
            question_id = question.id
            access_token = create_access_token(identity=str(self.user_id))
        headers = {'Cookie': f'access_token_cookie={access_token}'}
        data = {'content': 'This is a test answer.'}
        response = self.client.post(f'/answer/{question_id}', data=data, headers=headers, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            answer = AnswerModel.query.filter_by(question_id=question_id).first()
            self.assertIsNotNone(answer)
            self.assertEqual(answer.author, 'testuser')

    def test_profile_update(self):
        """Test updating user profile."""
        with self.app.app_context():
            access_token = create_access_token(identity=str(self.user_id))
        headers = {'Cookie': f'access_token_cookie={access_token}'}
        data = {
            'username': 'updateduser',
            'email': 'updated@example.com'
        }
        response = self.client.post('/profile', data=data, headers=headers, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Profile updated successfully', response.data)
        with self.app.app_context():
            user = UserModel.query.get(self.user_id)
            self.assertEqual(user.name, 'updateduser')
            self.assertEqual(user.email, 'updated@example.com')

    def test_request_otp(self, mocker):
        """Test requesting OTP for password change."""
        mocker.patch('flask_mail.Mail.send')  # Mock email sending
        with self.app.app_context():
            access_token = create_access_token(identity=str(self.user_id))
        headers = {'Cookie': f'access_token_cookie={access_token}'}
        response = self.client.post('/request-otp', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'OTP sent to your email', response.data)
        with self.app.app_context():
            user = UserModel.query.get(self.user_id)
            self.assertIsNotNone(user.otp)
            self.assertTrue(user.otp_expiry > datetime.utcnow())

    def test_change_password_success(self, mocker):
        """Test successful password change with valid OTP."""
        mocker.patch('flask_mail.Mail.send')  # Mock email sending
        with self.app.app_context():
            access_token = create_access_token(identity=str(self.user_id))
            user = UserModel.query.get(self.user_id)
            user.otp = '123456'
            user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
            db.session.commit()
        headers = {'Cookie': f'access_token_cookie={access_token}'}
        data = {
            'otp': '123456',
            'new_password': 'NewPassword456',
            'confirm_password': 'NewPassword456'
        }
        response = self.client.post('/change-password', data=data, headers=headers, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Password changed successfully', response.data)
        with self.app.app_context():
            user = UserModel.query.get(self.user_id)
            self.assertTrue(user.check_password('NewPassword456'))
            self.assertIsNone(user.otp)
            self.assertIsNone(user.otp_expiry)

    def test_change_password_invalid_otp(self):
        """Test password change with invalid OTP."""
        with self.app.app_context():
            access_token = create_access_token(identity=str(self.user_id))
            user = UserModel.query.get(self.user_id)
            user.otp = '123456'
            user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
            db.session.commit()
        headers = {'Cookie': f'access_token_cookie={access_token}'}
        data = {
            'otp': '654321',
            'new_password': 'NewPassword456',
            'confirm_password': 'NewPassword456'
        }
        response = self.client.post('/change-password', data=data, headers=headers, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid OTP', response.data)

    def test_logout(self):
        """Test logout functionality."""
        with self.app.app_context():
            access_token = create_access_token(identity=str(self.user_id))
        headers = {'Cookie': f'access_token_cookie={access_token}'}
        response = self.client.get('/logout', headers=headers, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged out successfully', response.data)
        with self.app.app_context():
            token = TokenBlocklist.query.filter_by(jti=access_token).first()
            self.assertIsNotNone(token)
        # Check if cookie is cleared
        self.assertIn('access_token_cookie=; Expires=Thu, 01-Jan-1970 00:00:00 GMT',
                      response.headers.get('Set-Cookie', ''))


if __name__ == '__main__':
    pytest.main(['-v'])