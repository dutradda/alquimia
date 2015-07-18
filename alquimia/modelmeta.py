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
from sqlalchemy import or_
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

    def _update_rec(cls, new_values, obj):
        for prop_name, new_value in new_values.iteritems():
            if isinstance(new_value, dict):
                cls._update_rec(new_value, obj[prop_name])
            elif isinstance(new_value, list):
                new_list = []
                model = type(obj)[prop_name].model
                for each_value in new_value:
                    if 'id' in each_value:
                        each_obj = cls._get_obj_by_id(model, each_value['id'])
                        cls._update_rec(each_value, each_obj)
                    else:
                        each_obj = model(**each_value)
                    new_list.append(each_obj)
                obj[prop_name] = new_list
            else:
                obj[prop_name] = new_value

    def _get_obj_by_id(cls, model, id_):
        try:
            return cls._session.query(model).filter(model.id == id_).one()
        except NoResultFound:
            raise TypeError("invalid id '%s'" % id_)

    def insert(cls, objs):
        objs_ = cls._build_objs(objs)
        cls._session.commit()
        if not isinstance(objs, list):
            objs_ = objs_[0]
        return objs_

    def update(cls, new_values):
        objs = []
        if not isinstance(new_values, list):
            new_values = [new_values]
        for new_value in new_values:
            try:
                id_ = new_value.pop('id')
            except KeyError:
                raise KeyError('values must have id property!')
            obj = cls._get_obj_by_id(cls, id_)
            cls._update_rec(new_value, obj)
            objs.append(obj)
        cls._session.commit()
        objs = objs[0] if len(objs) == 1 else objs
        return objs

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

    def _parse_filters(cls, query_dict, obj, filters):
        for prop_name, prop in query_dict.iteritems():
            if prop_name == '_or':
                filters_ = []
                [cls._parse_filters(subfilter, obj, filters_) for subfilter in prop]
                filters.append(or_(*filters_))
            else:
                if hasattr(obj, 'model'):
                    obj = obj.model
                if isinstance(prop, dict):
                    cls._parse_filters(prop, obj[prop_name], filters)
                elif isinstance(prop, list):
                    cls._parse_filters({'_or': prop}, obj[prop_name], filters)
                else:
                    filter_ = (obj[prop_name] == prop) if not isinstance(prop, str) \
                        else obj[prop_name].like(prop)
                    filters.append(filter_)
        return filters

    def query(cls, filters={}):
        filters = cls._parse_filters(filters, cls, [])
        return cls._session.query(cls).filter(*filters)
