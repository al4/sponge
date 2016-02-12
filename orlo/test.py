from flask import Flask
from flask.ext.httpauth import HTTPBasicAuth
from functools import update_wrapper, wraps
from flask.ext.testing import TestCase


app = Flask(__name__)
app.config['TESTING'] = True
app.config['DEBUG'] = False
app.config['TRAP_HTTP_EXCEPTIONS'] = True

security_enabled = True
auth = HTTPBasicAuth()


class conditional_auth(object):
    """
    Decorator which wraps a decorator, to only apply it if auth is enabled
    """
    def __init__(self, decorator):
        print("ini with {}".format(decorator.__name__))
        self.decorator = decorator
        update_wrapper(self, decorator)

    def __call__(self, func):
        """
        Call method
        """
        print("CALL func {}".format(func.__name__))

        @wraps(func)
        def wrapped(*args, **kwargs):
            """
            Wrapped method
            """
            print("WRAPPED CALL {}".format(func.__name__))
            print("Decorator: {}".format(self.decorator.__name__))
            if security_enabled:
                print('sec enabled')
                rv = self.decorator(func(*args, **kwargs))
                return rv
            else:
                print('sec disabled')
                rv = func(*args, **kwargs)
                return rv
        return wrapped


@app.route('/')
@conditional_auth(auth.login_required)
def get_token():
    """
    Get a token
    """
    return "OK"


class TestSecurity(TestCase):
    def create_app(self):
        return app

    def test_auth(self):
        """
        Same test as above with auth disabled
        """
        response = self.client.get('/')
        self.assert200(response)

