from copy import deepcopy


def all_fields_optional(parser):
    new_parser = deepcopy(parser)
    for arg in new_parser.args:
        arg.required = False
    return new_parser



