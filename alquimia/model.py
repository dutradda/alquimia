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
import weakref


class AlquimiaModelMeta(DeclarativeMeta):
    def __init__(cls, classname, bases, dict_):
        DeclarativeMeta.__init__(cls, classname, bases, dict_)
        attrs = {k:v for k,v in cls.__dict__.items() if isinstance(v, InstrumentedAttribute)}
        cls.__attrs__ = cls.__attributes__ = attrs
        cls._current_pos = 0

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
    
    def __getitem__(cls, attr_name):
        try:
            return cls.__attributes__[attr_name]
        except KeyError, e:
            raise KeyError(e.message)
        
    def __iter__(cls):
        return cls

    def next(cls):
        if cls._current_pos > len(cls.__attributes__.keys()):
            cls._current_pos = 0
            raise StopIteration
        else:
            cls._current_pos += 1
            return cls.__attributes__.keys()[cls._current_pos - 1]

    def _build_objs(cls, obj):
        if not isinstance(obj, list):
            obj = [obj]
        objs = []
        for each in obj:
            if not isinstance(each, cls):
                each = cls(**each)
            objs.append(each)
        return objs

    def insert(cls, objs):
        session = cls.session()
        objs = cls._build_objs(objs)
        session.add_all(objs)
        session.commit()
        return objs

    def _update_rec(cls, obj_dict, obj):
        for prop_name, prop in obj_dict.iteritems():
            if isinstance(prop, dict):
                cls._update_rec(prop, obj[prop_name])
            else:
                obj[prop_name] = prop

    def update(cls, objs):
        session = cls.session()
        if not isinstance(objs, list):
            objs = [objs]
        for obj in objs:
            new_obj = session.query(cls).filter(cls.id == obj.pop('id')).one()
            cls._update_rec(obj, new_obj)
        session.commit()
        return new_obj

    def delete(cls, ids):
        session = cls.session()
        if not isinstance(ids, list):
            ids = [ids]
        for id_ in ids:
            session.query(cls).filter(cls.id == id_).delete()
        session.commit()

    def _build_query_filter_rec(cls, query_dict, obj, comp_list=[]):
        for prop_name, prop in query_dict.iteritems():
            if isinstance(prop, dict):
                cls._build_query_filter_rec(prop, obj[prop_name], comp_list)
            else:
                if hasattr(obj, 'model'):
                    obj = obj.model
                comp_list.append(obj[prop_name] == prop)
        return comp_list

    def query(cls, query_dict):
        filters = cls._build_query_filter_rec(query_dict, cls)
        session = cls.session()
        return session.query(cls).filter(*filters).first()



class AlquimiaModel(object):
    def _check_attr(self, attr_name):
        if not type(self).has_key(attr_name):
            raise TypeError("'%s' is not a valid model attribute!" % attr_name)

    def __init__(self, **kwargs):
        for prop_name, prop in kwargs.iteritems():
            if isinstance(prop, dict):
                self[prop_name] = type(self)[prop_name].model(**prop)
            else:
                self[prop_name] = prop
        self._current_pos = 0

    def __setitem__(self, item, value):
        self._check_attr(item)
        setattr(self, item, value)

    def __getitem__(self, item):
        self._check_attr(item)
        return getattr(self, item)

    def __repr__(self):
        return str(dict(self))

    def __iter__(self):
        return self

    def next(self):
        if self._current_pos > len(self.keys()):
            self._current_pos = 0
            raise StopIteration
        else:
            self._current_pos += 1
            return self.keys()[self._current_pos - 1]

    def has_key(self, key):
        awld._check_attr(key)
        return hasattr(self, key)

    def keys(self):
        return type(self).keys()