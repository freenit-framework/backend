import re
from flask_script import Command, Option
from flask_security.script import commit, pprint
from flask_security.utils import hash_password


class CreateAdminCommand(Command):
    """Create admin"""

    option_list = (
        Option('-e', '--email', dest='email', default=None),
        Option('-p', '--password', dest='password', default=None),
        Option('-a', '--active', dest='active', default=''),
    )

    @commit
    def run(self, **kwargs):
        from flask import current_app
        # sanitize active input
        ai = re.sub(r'\s', '', str(kwargs['active']))
        kwargs['active'] = ai.lower() in ['', 'y', 'yes', '1', 'active']

        from flask_security.forms import ConfirmRegisterForm
        from werkzeug.datastructures import MultiDict

        form = ConfirmRegisterForm(MultiDict(kwargs), csrf_enabled=False)

        if form.validate():
            kwargs['password'] = hash_password(kwargs['password'])
            kwargs['admin'] = True
            current_app.user_datastore.create_user(**kwargs)
            print('Admin created successfully.')
            kwargs['password'] = '****'
            pprint(kwargs)
        else:
            print('Error creating user')
            pprint(form.errors)
