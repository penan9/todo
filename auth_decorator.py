from flask import session, redirect
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('profile', None)
        # You would add a check here and use the user id or something to fetch
        # the other data for that user/check if they exist
        if user:
            return f(*args, **kwargs)
        # return 'You aint logged in, no page for u!'
        # return redirect('/login')
        return "Todo List, need to login <a href='/login'><button>Login</button></a>"
    return decorated_function