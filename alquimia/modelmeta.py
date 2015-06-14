# Copyright 2015 Diogo Dutra

# This file is part of alquimia.

# alquimia is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.exc import NoResultFound
from alquimia import utils


class AlquimiaModelMeta(DeclarativeMeta):
    def __init__(cls, classname, bases, dict_):
        DeclarativeMeta.__init__(cls, classname, bases, dict_)
        attrs = {k:v for k,v in cls.__dict__.items() \
                                       if isinstance(v, InstrumentedAttribute)}
        cls.__attrs__ = cls.__attributes__ = attrs
        cls._current_pos = 0
    
    def __getitem__(cls, attr_name):
        try:
            return cls.__attributes__[attr_name]
        except KeyError, e:
            raise KeyError(e.message)
        
    def __iter__(cls):
        return cls

    def __contains__(cls, item):
        return item in cls.__attrs__

    def next(cls):
        cls._current_pos += 1
        if cls._current_pos >= len(cls.keys()):
            cls._current_pos = 0
            raise StopIteration
        else:
            return cls.keys()[cls._current_pos - 1]

    @property
    def keys(cls):
        return cls.__attrs__.keys
    
    @property
    def values(cls):
        return cls.__attrs__.values

    @property
    def items(cls):
        return cls.__attrs__.items
    
    @property
    def iteritems(cls):
        return cls.__attrs__.iteritems

    def _build_objs(cls, obj):
        if not isinstance(obj, list):
            obj = [obj]
        objs = []
        for each in obj:
            if not isinstance(each, cls):
                each = cls(**each)
            objs.append(each)
        return objs

    def _update_rec(cls, obj_dict, obj):
        for prop_name, prop in obj_dict.iteritems():
            if isinstance(prop, dict):
                cls._update_rec(prop, obj[prop_name])
            else:
                obj[prop_name] = prop

    def insert(cls, objs):
        session = cls._session
        objs_ = cls._build_objs(objs)
        session.commit()
        if not isinstance(objs, list):
            objs_ = objs_[0]
        return objs_

    def update(cls, objs):
        session = cls._session
        if not isinstance(objs, list):
            objs = [objs]
        for obj in objs:
            try:
                id_ = obj.pop('id')
            except KeyError:
                raise KeyError('objects must have an id!')
            try:
                new_obj = session.query(cls).filter(cls.id == id_).one()
            except NoResultFound:
                raise TypeError("invalid id '%s'" % id_)
            cls._update_rec(obj, new_obj)
        session.commit()
        return new_obj

    def delete(cls, ids):
        session = cls._session
        if not isinstance(ids, list):
            ids = [ids]
        for id_ in ids:
            try:
                int(id_)
            except ValueError:
                session.rollback()
                raise TypeError('%s.delete just receive ids (integer)!' \
                                ' No delete operation was done.' % cls)
            session.query(cls).filter(cls.id == id_).delete()
        session.commit()

    def query(cls, filters={}):
        filters = utils.parse_filters(filters, cls, [])
        return cls._session.query(cls).filter(*filters)
