import functools

from flask import current_app
from flask_jwt_extended import get_jwt_identity
from flask_smorest import abort


def get_user():
    User = current_app.user_datastore.user_model
    user_id = get_jwt_identity()
    if user_id is None:
        abort(401, message='No token provided')
    try:
        if current_app.dbtype == 'sql':
            user = User.get(id=user_id)
        else:
            user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        abort(404, message='No such user')
    return user


def every(roles):
    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            user = get_user()
            if not user.admin:
                if current_app.dbtype == 'sql':
                    user_roles = [role.role.name for role in user.roles]
                else:
                    user_roles = [role.name for role in user.roles]
                for role in roles:
                    if role not in user_roles:
                        abort(403, message='Access denied')
            return func(*args, **kwargs)

        return inner

    return outer


def one(roles):
    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            user = get_user()
            if user.admin:
                return func(*args, **kwargs)
            if current_app.dbtype == 'sql':
                user_roles = [role.role.name for role in user.roles]
            else:
                user_roles = [role.name for role in user.roles]
            for role in roles:
                if role in user_roles:
                    return func(*args, **kwargs)
            abort(403, message='Access denied')

        return inner

    return outer
