from flask_smorest import Blueprint, abort

from ..models.role import Role, UserRoles
from ..models.user import User
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
        return paginate(Role.select(), pagination)

    @blueprint.arguments(RoleSchema)
    @blueprint.response(RoleSchema)
    def post(self, args):
        """Create role"""
        role = Role(**args)
        role.save()
        return role


@blueprint.route('/<role_id>', endpoint='detail')
class RoleAPI(ProtectedMethodView):
    @blueprint.response(RoleSchema)
    def get(self, role_id):
        """Get role details"""
        try:
            role = Role.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, message='Role not found')
        role.users = [user.user for user in role.users]
        return role

    @blueprint.arguments(RoleSchema(partial=True))
    @blueprint.response(RoleSchema)
    def patch(self, args, role_id):
        """Edit role"""
        try:
            role = Role.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, message='Role not found')
        for field in args:
            setattr(role, field, args[field])
        role.save()
        return role

    @blueprint.response(RoleSchema)
    def delete(self, role_id):
        """Remove role"""
        try:
            role = Role.get(id=role_id)
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
        try:
            role = Role.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, message='No such role')
        try:
            user = User.get(id=args['id'])
        except User.DoesNotExist:
            abort(404, message='No such user')
        for user in role.users:
            if user.user.id == args['id']:
                abort(409, message='User already assigned to role')
        user_role = UserRoles(user=user, role=role)
        user_role.save()
        return user


@blueprint.route('/<role_id>/user/<user_id>', endpoint='user_deassign')
class RoleUserDeassignAPI(ProtectedMethodView):
    @blueprint.response(RoleSchema)
    def delete(self, role_id, user_id):
        """Remove user from role"""
        try:
            role = Role.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, message='No such role')
        try:
            user = User.get(user_id)
        except User.DoesNotExist:
            abort(404, message='No such user')
        for user in role.users:
            if user.user.id == int(user_id):
                user.delete_instance()
                return user
        abort(409, message='User not assigned to role')
