# Copyright 2015 Diogo Dutra

# This file is part of Alquimia.

# Alquimia is free software: you can redistribute it and/or modify
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
from sqlalchemy.orm.exc import NoResultFound, DetachedInstanceError


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
    def has_key(cls):
        return cls.__attrs__.has_key
    
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

    def _build_query_filter_rec(cls, query_dict, obj, filters):
        for prop_name, prop in query_dict.iteritems():
            if isinstance(prop, dict):
                cls._build_query_filter_rec(prop, obj[prop_name], filters)
            else:
                if hasattr(obj, 'model'):
                    obj = obj.model
                filters.append(obj[prop_name] == prop)
        return filters

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

    def query(cls, query_dict):
        filters = cls._build_query_filter_rec(query_dict, cls, [])
        session = cls._session
        result = session.query(cls).filter(*filters).all()
        return result


class AlquimiaModel(object):
    def __new__(cls, **kwargs):
        inst = object.__new__(cls)
        inst.depth = 0
        return inst

    def __init__(self, **kwargs):
        for prop_name, prop in kwargs.iteritems():
            if isinstance(prop, dict):
                self[prop_name] = type(self)[prop_name].model(**prop)
            else:
                self[prop_name] = prop
        self._session.add(self)
        self._current_pos = 0

    def __setitem__(self, item, value):
        self._check_attr(item)
        setattr(self, item, value)

    def __getitem__(self, item):
        self._check_attr(item)
        try:
            return getattr(self, item)
        except DetachedInstanceError:
            self._session.add(self)
            return getattr(self, item)

    def __repr__(self):
        return repr(self.todict())

    def __iter__(self):
        return self

    def next(self):
        self._current_pos += 1
        if self._current_pos >= len(self.keys()):
            self._current_pos = 0
            raise StopIteration
        else:
            return self.keys()[self._current_pos - 1]

    def _check_attr(self, attr_name):
        if not attr_name in type(self):
            raise TypeError("'%s' is not a valid %s attribute!" %
                                              (attr_name, type(self).__name__))
            
    def _todict_part(self, obj, depth, rec_stack):
        if isinstance(obj, AlquimiaModel):
            if depth != 0:
                depth = depth - 1
                if not obj in rec_stack:
                    obj = self.todict(depth, obj, rec_stack)
                else:
                    obj = '<loaded object at id=%d>' % obj['id']
            else:
                obj = '<1 object>'
        return obj

    def todict(self, depth=0, obj=None, rec_stack=[]):
        obj = self if obj is None else obj
        dict_ = {}
        rec_stack.append(obj)
        for prop_name, prop in obj.items():
            if isinstance(prop, list):
                if depth != 0 and len(prop):
                    propl = []
                    for each in prop:
                        each = self._todict_part(each, depth, rec_stack)
                        propl.append(each)
                    prop = propl
                else:
                    prop = '<%d object(s)>' % len(prop)
            else:
                prop = self._todict_part(prop, depth, rec_stack)
            dict_[prop_name] = prop    
        return dict_

    def has_key(self, key):
        self._check_attr(key)
        return hasattr(self, key)

    def keys(self):
        return type(self).keys()

    def items(self):
        return [(k, self[k]) for k in self.keys()]

    def remove(self):
        self._session.delete(self)
        self._session.commit()

    def save(self):
        self._session.commit()
