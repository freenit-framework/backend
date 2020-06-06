from flask import current_app
from flask_smorest import Blueprint, abort

from ..schemas.paging import PageInSchema, paginate
from ..schemas.role import RolePageOutSchema, RoleSchema, UserAssignSchema
from .methodviews import ProtectedMethodView

blueprint = Blueprint('roles', 'role')


@blueprint.route('', endpoint='list')
class RoleListAPI(ProtectedMethodView):
    @blueprint.arguments(PageInSchema(), location='headers')
    @blueprint.response(RolePageOutSchema)
    def get(self, pagination):
        """List roles"""
        Role = current_app.user_datastore.role_model
        if current_app.dbtype == 'sql':
            return paginate(Role.select(), pagination)
        else:
            return paginate(Role.objects.all(), pagination)

    @blueprint.arguments(RoleSchema)
    @blueprint.response(RoleSchema)
    def post(self, args):
        """Create role"""
        Role = current_app.user_datastore.role_model
        role = Role(**args)
        role.save()
        return role


@blueprint.route('/<role_id>', endpoint='detail')
class RoleAPI(ProtectedMethodView):
    @blueprint.response(RoleSchema)
    def get(self, role_id):
        """Get role details"""
        Role = current_app.user_datastore.role_model
        try:
            if current_app.dbtype == 'sql':
                role = Role.get(id=role_id)
            else:
                role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, message='Role not found')
        role.users = [user.user for user in role.users]
        return role

    @blueprint.arguments(RoleSchema(partial=True))
    @blueprint.response(RoleSchema)
    def patch(self, args, role_id):
        """Edit role"""
        Role = current_app.user_datastore.role_model
        try:
            if current_app.dbtype == 'sql':
                role = Role.get(id=role_id)
            else:
                role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, message='Role not found')
        for field in args:
            setattr(role, field, args[field])
        role.save()
        return role

    @blueprint.response(RoleSchema)
    def delete(self, role_id):
        """Remove role"""
        Role = current_app.user_datastore.role_model
        try:
            if current_app.dbtype == 'sql':
                role = Role.get(id=role_id)
            else:
                role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, message='Role not found')
        role.delete_instance()
        return role


@blueprint.route('/<role_id>/user', endpoint='user_assign')
class RoleUserAssignAPI(ProtectedMethodView):
    @blueprint.arguments(UserAssignSchema)
    @blueprint.response(RoleSchema)
    def post(self, args, role_id):
        """Assign user to role"""
        Role = current_app.user_datastore.role_model
        User = current_app.user_datastore.user_model
        try:
            if current_app.dbtype == 'sql':
                role = Role.get(id=role_id)
            else:
                role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, message='No such role')
        try:
            user = User.get(id=args['id'])
        except User.DoesNotExist:
            abort(404, message='No such user')
        current_app.user_datastore.add_role_to_user(user, role)
        return role


@blueprint.route('/<role_id>/user/<user_id>', endpoint='user_deassign')
class RoleUserDeassignAPI(ProtectedMethodView):
    @blueprint.response(RoleSchema)
    def delete(self, role_id, user_id):
        """Remove user from role"""
        Role = current_app.user_datastore.role_model
        User = current_app.user_datastore.user_model
        try:
            if current_app.dbtype == 'sql':
                role = Role.get(id=role_id)
            else:
                role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, message='No such role')
        try:
            if current_app.dbtype == 'sql':
                user = User.get(id=user_id)
            else:
                user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            abort(404, message='No such user')
        current_app.user_datastore.remove_role_from_user(user, role)
        return role
