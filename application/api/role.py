from flask_rest_api import Blueprint, abort

from ..models.auth import Role
from ..schemas.auth import RoleSchema
from ..schemas.paging import PageInSchema, PageOutSchema, paginate
from .methodviews import ProtectedMethodView

blueprint = Blueprint('role', 'role')


@blueprint.route('', endpoint='roles')
class RoleListAPI(ProtectedMethodView):
    @blueprint.arguments(PageInSchema(), location='headers')
    @blueprint.response(PageOutSchema(RoleSchema))
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


@blueprint.route('/<role_id>', endpoint='role')
class RoleAPI(ProtectedMethodView):
    @blueprint.response(RoleSchema)
    def get(self, role_id):
        """Get role details"""
        try:
            role = Role.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, 'Role not found')
        return role

    @blueprint.arguments(RoleSchema(partial=True))
    @blueprint.response(RoleSchema)
    def patch(self, args, role_id):
        """Edit role"""
        try:
            role = Role.get(id=role_id)
        except Role.DoesNotExist:
            abort(404, 'Role not found')
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
            abort(404, 'Role not found')
        role.delete_instance()
        return role
