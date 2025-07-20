StackOverflow-Lite
A lightweight platform where users can ask questions, provide answers, and interact with content through a RESTful API built with Flask.
Table of Contents

Project Overview
Features
Technologies Used
Setup Instructions
API Endpoints
Testing
Continuous Integration
Deployment
Contributing
License

Project Overview
StackOverflow-Lite is a simplified version of StackOverflow, designed to allow users to create accounts, post and delete questions, provide answers, and mark answers as accepted. The API is secured with JWT and uses a database for data persistence. The project follows OOP principles and TDD, with linting and style guides enforced.
Features
Required Features

User registration and login
Post and delete questions
Post answers
View questions and their answers
Mark an answer as accepted

Optional Features

Upvote or downvote answers
Comment on answers
Fetch all questions asked by a user
Search for questions
View questions with the most answers

Technologies Used

Server-Side Framework: Flask (Python)
Database: PostgreSQL
Linting Library: Pylint
Style Guide: PEP8
Testing Framework: PyTest
Authentication: JWT
CI/CD: TravisCI, Coveralls
Hosting: Heroku

Setup Instructions

Clone the repository:
git clone https://github.com/yourusername/stackoverflow-lite.git
cd stackoverflow-lite


Set up a virtual environment:
python3 -m venv venv
source venv/bin/activate


Install dependencies:
pip install -r requirements.txt


Set up environment variables:Create a .env file in the root directory and add:
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=postgresql://username:password@localhost:5432/stackoverflow_lite
SECRET_KEY=your-secret-key


Set up the database:Run the following commands to create and migrate the database:
flask db init
flask db migrate
flask db upgrade


Run the application:
flask run


Run tests:
pytest



API Endpoints
The API is versioned with /api/v1 prefix (e.g., https://yourapp.herokuapp.com/api/v1/).



Endpoint
Functionality
Note



POST /auth/signup
Register a user



POST /auth/login
Login a user
Returns JWT token


GET /questions
Fetch all questions



GET /questions/<questionId>
Fetch a specific question
Includes all answers for the question


POST /questions
Post a question
Requires JWT authentication


DELETE /questions/<questionId>
Delete a question
Available to the question author, requires JWT authentication


POST /questions/<questionId>/answers
Post an answer to a question
Requires JWT authentication


PUT /questions/<questionId>/answers/<answerId>
Mark an answer as accepted or update an answer
Available to answer/question author, requires JWT authentication


Example Request
POST /auth/signup
{
  "username": "testuser",
  "email": "testuser@example.com",
  "password": "password123"
}

Response
{
  "message": "User registered successfully",
  "user": {
    "username": "testuser",
    "email": "testuser@example.com"
  }
}

Testing

Tests are written using PyTest and cover all API endpoints.
To run tests with coverage:pytest --cov=app


Test the API using Postman to verify functionality.

Continuous Integration

TravisCI: Configured for continuous integration. See .travis.yml for details.
Coveralls: Tracks test coverage. See coverage reports at Coveralls.
Badges:






Deployment
The application is hosted on Heroku at https://yourapp.herokuapp.com.
Contributing

Fork the repository.
Create a feature branch (git checkout -b feature/your-feature).
Commit your changes (git commit -m 'Add your feature').
Push to the branch (git push origin feature/your-feature).
Create a pull request on GitHub for review.

License
This project is licensed under the MIT License. See the LICENSE file for details.
