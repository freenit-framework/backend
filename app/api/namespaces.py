from . import api

ns_auth = api.namespace('auth', description='Auth operations')
ns_me = api.namespace('me', description='Me operations')
ns_user = api.namespace('users', description='User operations')
