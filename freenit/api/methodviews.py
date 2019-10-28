from flask.views import MethodView
from flask_jwt_extended import jwt_required


class ProtectedMethodView(MethodView):
    """
    Resource protedted by jwt
    """
    decorators = [jwt_required]
