from orlo import app
from orlo.config import config
from orlo.exceptions import OrloAuthError
from flask.ext.httpauth import HTTPBasicAuth
from flask.ext.tokenauth import TokenAuth, TokenManager
from flask import request, jsonify, g, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from functools import update_wrapper, wraps


# initialization
user_auth = HTTPBasicAuth()
token_auth = TokenAuth(config.get('security', 'secret_key'))
token_manager = TokenManager(secret_key=config.get('security', 'secret_key'))


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
            if config.getboolean('security', 'enabled'):
                print('sec enabled')
                print(self.decorator.__name__)
                print(type(self.decorator))
                print(type(func))
                set_current_user_as(User('nobody'))
                rv = self.decorator(func(*args, **kwargs))
                print('foo')
                return rv
            else:
                print('sec disabled')
                print(self.decorator.__name__)
                print(type(self.decorator))
                print(type(func))
                rv = func(*args, **kwargs)
                print('foo')
                print(rv)
        return wrapped


# def conditional_auth(decorator, function):
#     @wraps(function)
#     def decorated(*args, **kwargs):
#         if config.get('security', 'enabled'):
#             decorator(function(*args, **kwargs))
#         else:
#             function(*args, **kwargs)
#
#     return decorated


class User(object):
    def __init__(self, name):
        self.name = name
        self.password_hash = self.get_pw_ent(name)
        self.confirmed = False

    @staticmethod
    def get_pw_ent(name):
        if config.get('security', 'method') == 'file':
            with open(config.get('security', 'passwd_file')) as f:
                for line in f:
                    line = line.strip()
                    user = line.split(':')[0]
                    if not user == name:
                        continue

                    # found user return password
                    app.logger.debug("Found user {} in file".format(name))
                    pw = ':'.join(line.split(':')[1:])
                    return pw
            # user not in passwd file return a hash that cannot occur
            return '*'

        # TODO implement LDAP
        raise OrloAuthError("Unknown user_auth method, check security config")

    def hash_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        rc = check_password_hash(self.password_hash, password)
        return rc

    def generate_auth_token(self, expiration=3600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.name})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        name = data['id']
        return User(name)


@conditional_auth(user_auth.verify_password)
def verify_password(username=None, password=None):
    app.logger.debug("Verify_password called")

    if not password:
        return False

    user = User(username)
    if not user.verify_password(password):
        return False

    set_current_user_as(user)
    return True


@conditional_auth(token_auth.verify_token)
def verify_token(token=None):
    app.logger.debug("Verify_token called")

    if not token:
        return False

    token_user = token_manager.verify(token)
    if token_user:
        set_current_user_as(User(token_user))
        return True


def set_current_user_as(user):
    if not g.get('current_user'):
        app.logger.debug('Setting current user to: {}'.format(user.name))
        g.current_user = user


@user_auth.error_handler
@token_auth.error_handler
def auth_error():
    """
    Authentication error
    """
    # raise OrloAuthError("Not authorized")
    response = jsonify({'error': 'not authorized'})
    response.status_code = 401
    return response


@app.route('/token')
@conditional_auth(user_auth.login_required)
def get_token():
    """
    Get a token
    """
    ttl = config.getint('security', 'token_ttl')
    token = token_manager.generate(g.current_user.name, ttl)
    print('bar')
    rv = jsonify({
        'token': token.decode('ascii'),
        'duration': config.get('security', 'token_ttl')
    })
    print(rv)
    return rv

