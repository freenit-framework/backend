from marshmallow import ValidationError, fields


class ID(fields.Field):
    def _serialize(self, value, attr, obj, *args, **kwargs):
        if type(value) == int:
            return value
        if value is None:
            return None
        return str(value)

    def _deserialize(self, value, attr, data, *args, **kwargs):
        if type(value) == int:
            return value
        try:
            import bson
            return bson.ObjectId(value)
        except (TypeError, bson.errors.InvalidId):
            raise ValidationError('Invalid ObjectId.')
