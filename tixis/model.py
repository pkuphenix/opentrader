from tixis import app
from flask import request, render_template, url_for, redirect
from common.db import db_tixis
from bson.objectid import ObjectId
from common.utils import gen_time

class ValidationError(Exception):
    pass

class TixisModelBase(type):
    """
    Metaclass for all models. As a meta class, all model classes are its instances. That is, the __new__ function would be triggered to create every model class based on its definition.
    """
    def __new__(cls, name, bases, attrs):
        # find the _fields attribute and call each field's append_to_model function
        _fields = attrs.get('_fields', [])
        _field_dict = {}
        for each_field in _fields:
            _field_dict[each_field.name] = each_field
        attrs['_field_dict'] = _field_dict
        new_class = super(TixisModelBase, cls).__new__(cls, name, bases, attrs)
        for each_field in _fields:
            each_field.append_to_model(new_class)
        return new_class

class TixisModel(object):
    __metaclass__ = TixisModelBase
    _collection_name = ''
    _fields = []
    @classmethod
    def db(cls):
        return getattr(db_tixis, cls._collection_name)

    @classmethod
    def new(cls, **kwargs):
        for field in cls._fields:
            if field.name in kwargs:
                if kwargs[field.name] in ('', None):
                    if field.optional:
                        kwargs[field.name] = field.default
                    else:
                        raise ValidationError('Field %s is not optional.' % field.name)
                else:
                    kwargs[field.name] = field.standarlize(kwargs[field.name])
                    field.validate(kwargs[field.name])
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
        self.init()

    def init(self):
        pass # to be overwritten by sub classes
        
    def get(self):
        inst = self.__class__.db().find_one({'_id':ObjectId(self.oid)})
        if not inst:
            raise KeyError('No instance with this ID found: %s.' % oid)
        return inst

    def update(self, **kwargs):
        for field in self._fields:
            if field.name in kwargs:
                if kwargs[field.name] in ('', None):
                    if field.optional:
                        kwargs[field.name] = field.default
                    else:
                        raise ValidationError('Field %s is not optional.' % field.name)
                else:
                    kwargs[field.name] = field.standarlize(kwargs[field.name])
                    field.validate(kwargs[field.name])

        # update the instance in db
        return self.db().update({"_id":ObjectId(self.oid)}, {"$set":kwargs})

    @property
    def url(self):
        return url_for('program_detail', oid=self.oid)

    def display(self, fieldname):
        for each in self._fields:
            if each.name == fieldname:
                return each.display(self.get().get(fieldname))
        return ''

    @classmethod
    def get_field(cls, fieldname):
        return cls._field_dict.get(fieldname, None)
        
    def __getattr__(self, attr):
        field = self.__class__.get_field(attr)
        return self.get().get(attr, field.default)


class TixisField(object):
    def __init__(self, name="", optional=True, default=None, *args, **kwargs):
        self.name = name
        self.optional = optional
        self.default = default

    def append_to_model(self, model):
        self.model = model

    def validate(self, val):
        return True

    def standarlize(self, val):
        return val

    def display(self, val):
        if val is None:
            return ''
        else:
            return str(val)

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

class OIDField(TixisField):
    def standarlize(self, val):
        return ObjectId(val)

class TimeField(TixisField):
    def standarlize(self, val):
        if type(val) == str or type(val) == unicode:
            return gen_time(val)
        else:
            return val

class PriceField(TixisField):
    def standarlize(self, val):
        return round(float(val), 3)


def test_model_base():
    class TestModelProgram(TixisModel):
        _collection_name = 'programs'
        _fields = [
            CharField(name="user", default='qianli'),
            CharField(name="name", unique=True),
            CharField(name="desc"),
            EnumField(name="target_type", values=('percent', 'amount')),
            UIntField(name="target_value"),
        ]

    f = TestModelProgram.get_field('user')
    assert f.model == TestModelProgram
    assert f.default == 'qianli'
    ps = TestModelProgram.find({'user':'qianli'})
    print ps[0].user



