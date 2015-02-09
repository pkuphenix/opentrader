from tixis import app
from flask import request, render_template, url_for, redirect
from common.db import db_tixis
from bson.objectid import ObjectId

class ValidationError(Exception):
    pass

class TixisModel(object):
    _collection_name = ''
    _fields = []
    @classmethod
    def db(cls):
        return getattr(db_tixis, cls._collection_name)

    @classmethod
    def new(cls, **kwargs):
        for field in cls._fields:
            if field.name in kwargs:
                field.validate(field.standarlize(kwargs[field.name]))
            else:
                if field.optional:
                    kwargs[field.name] = field.default
                else:
                    raise ValidationError('Field %s is not optional.' % field.name)
        # create the instance in db
        oid = cls.db().insert(kwargs)

        return cls(str(oid))

    @classmethod
    def remove(cls, *args, **kwargs):
        return cls.db().remove(*args, **kwargs)

    @classmethod
    def list(cls):
        return cls.find()

    @classmethod
    def find(cls, *args, **kwargs):
        instances = cls.db().find(*args, **kwargs)
        result = []
        for inst in instances:
            result.append(cls(str(inst.get('_id')), verify=False))
        return result

    @classmethod
    def find_one(cls, *args, **kwargs):
        instance = cls.db().find_one(*args, **kwargs)
        if not instance:
            return None
        else:
            return cls(str(instance.get('_id')), verify=False)

    def __init__(self, oid='', verify=True):
        self.oid = str(oid)
        if oid and verify:
            inst = self.__class__.db().find_one({'_id':ObjectId(oid)})
            if not inst:
                raise KeyError('No instance with this ID found: %s.' % oid)
        
    def get(self):
        inst = self.__class__.db().find_one({'_id':ObjectId(self.oid)})
        if not inst:
            raise KeyError('No instance with this ID found: %s.' % oid)
        return inst

    @property
    def url(self):
        return url_for('program_detail', oid=self.oid)
        
    def __getattr__(self, attr):
        return self.get().get(attr)


class TixisField(object):
    def __init__(self, name="", optional=True, default=None, *args, **kwargs):
        self.name = name
        self.optional = optional
        self.default = default

    def validate(self, val):
        return True

    def standarlize(self, val):
        return val

class CharField(TixisField):
    pass

class UIntField(TixisField):
    def validate(self, val):
        if val < 0:
            raise ValidationError('Please input an unsigned integer.')

    def standarlize(self, val):
        try:
            return int(val)
        except ValueError:
            raise ValidationError('Please input an integer.')

class EnumField(TixisField):
    pass


