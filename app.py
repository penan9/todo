import os
import pathlib
import requests
import flask
from flask import Flask, request, url_for, session, abort, redirect
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from auth_decorator import login_required
from datetime import timedelta

# dotenv setup
from dotenv import load_dotenv
load_dotenv()

# App config
app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'

# Session config
app.secret_key = '4325bedae2c4e7e790c43a05bc14d1914a979f9e07d92236ac93ec9533899fad'
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

db = SQLAlchemy(app)

# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='881072346550-btb1pupabk29t35tcbkejdgh4or62tk8.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    taskName = db.Column(db.String(80), unique=True, nullable=False)
    markDone = db.Column(db.Boolean, default=False, nullable=False)
    description = db.Column(db.String(300))

    # db.create_all()

    def __repr__(self):
        return f"{self.id}, {self.taskName}, {self.markDone} - {self.description}"


@app.route('/todo')
@login_required
def get_todos():
    todos = Todo.query.all()
    if todos is None:
        return {"error": "No data found"}
    output = []
    for todo in todos:
        if todo is None:
            return {"error": "No data found"}
        todo_data = {'id': todo.id, 'taskName': todo.taskName, 'markDone': todo.markDone, 'description': todo.description}
        output.append(todo_data)
    return {"todos": output}


@app.route('/todo/<id>')
@login_required
def get_todo(id):
    todo = Todo.query.get_or_404(id)
    return {"id": todo.id, "taskName": todo.taskName, "markDone": todo.markDone, "description": todo.description}


@app.route('/todo', methods=['POST'])
def add_todo():
    todo = Todo(taskName=request.json['taskName'], markDone=request.json['markDone'], description=request.json['description'])
    db.session.add(todo)
    db.session.commit()
    return {'id': todo.id}


@app.route('/todo/<id>', methods=['DELETE'])
@login_required
def delete_todo(id):
    todo = Todo.query.get(id)
    if todo is None:
        return {"error": "not found"}
    db.session.delete(todo)
    db.session.commit()
    return {'message': "Done delete todo!"}


@app.route('/todo_complete/<id>', methods=['POST'])
@login_required
def complete_todo(id):
    result = Todo.query.filter_by(id=id).first()
    if not result:
        return {'message': "List doesn't exist, cannot update"}
    result.markDone = True
    db.session.commit()
    return {'message': "Marking done!", 'id': result.id}


@app.route('/')
@login_required
def hello_world():
    email = dict(session)['profile']['email']
    return f"Hello, you are logged in as {email}! \
    <br> <a href='/todo'><button>List Todo List</button></a>"


@app.route('/login')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set ur own data in the session not the profile from google
    session['profile'] = user_info
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    return redirect('/')


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
