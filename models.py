from tortoise import fields
from tortoise.models import Model


class Comment(Model):
    id = fields.TextField(pk=True)
    title = fields.TextField()
    build_number = fields.IntField()
    timestamp = fields.DatetimeField()
    url = fields.TextField()
    description = fields.TextField()
    images = fields.JSONField()
    user = fields.JSONField()
    sended = fields.BooleanField()


class UpdateChannel(Model):
    id = fields.BigIntField(pk=True)
