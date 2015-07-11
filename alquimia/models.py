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


import logging
import copy
from sqlalchemy import create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.orm.query import Query
from sqlalchemy.orm import ColumnProperty
from alquimia.model import AlquimiaModel
from alquimia.modelmeta import AlquimiaModelMeta
from alquimia.models_attrs import ModelsAttributes
from alquimia.models_attrs_reflect import ModelsAtrrsReflect
from alquimia import DATA_TYPES


class JoinNotFoundError(Exception):
    def __init__(self, join_name, field):
        message = 'Join %s not found in gived joins for field %s.%s' % \
                                                  (join_name, join_name, field)
        Exception.__init__(self, message)


class AlquimiaQuery(Query):
    pass


class QueryBuilderMeta(type):
    def _build_subquery_join(cls, f_name, fields):
        fields_copy = list(fields)
        join = None
        for field in fields_copy:
            if isinstance(field, dict):
                if 'id' in field:
                    model = field['id'].keys()[0]
                    attr = field['id'].values()[0]
                    join = ('%s_id' % f_name, cls._models[model][attr])
                    field.pop('id')
                    if not len(field):
                        fields.remove(field)
                    fields.append(new_field, 'id')
                    break
        return join

    def _build_subqueries_joins(cls, subqueries):
        joins = {}
        for sub_name, sub in subqueries.iteritems():
            join = None
            for f_name, field in sub.iteritems():
                if f_name in cls._models and isinstance(field, list):
                    join = cls._build_subquery_join(f_name, field)
                    if join:
                        break
            sub = QueryBuilder(sub, cls._models).subquery(sub_name)
            joins[sub_name] = [sub, sub.c[join[0]] == join[1]]
        return joins

    def _build_filter_rec(cls, query_dict, obj, filters):
        for prop_name, prop in query_dict.iteritems():
            if isinstance(prop, dict):
                cls._build_filter_rec(prop, obj[prop_name], filters)
            else:
                if hasattr(obj, 'model'):
                    obj = obj.model
                filters.append(obj[prop_name] == prop)
        return filters

    def _build_filter(cls, filter_):
        for model in filter_:
            pass

    def _build_func(cls, f_name, field):
        if isinstance(field, dict):
            field = cls._models[field.keys()[0]][field.values()[0]]
        cls._fields_map[f_name] = cls._map_counter
        cls._map_counter += 1
        return getattr(func, f_name).label(f_name)

    def _build_fields_rec(cls, f_name, model, fields=[],
                                                     out_name=None, sub=None):
        if not isinstance(model, list):
            model = [model]
        for field in model:
            if isinstance(field, dict):
                for in_model_name, in_model in field.iteritems():
                    if out_name:
                        new_out_name = '%s_%s' % (out_name, f_name)
                    else:
                        new_out_name = f_name
                    cls._build_fields_rec(in_model_name, in_model,
                                                     fields, new_out_name, sub)
            else:
                if out_name:
                    field_name = '%s_%s_%s' % (out_name, f_name, field)
                else:
                    field_name = '%s_%s' % (f_name, field)
                if sub:
                    sub_field_name = field_name
                    if out_name:
                        sub_field_name = '_'.join(field_name.split('_')[1:])
                    new_field = sub.c[sub_field_name].label(field_name)
                else:
                    new_field = cls._models[f_name][field].label(field_name)
                fields.append(new_field)
                if not f_name in cls._fields_map:
                    cls._fields_map[f_name] = {}
                cls._fields_map[f_name][field] = cls._map_counter
                cls._map_counter += 1
        return fields

    def _build_fields(cls, fields, subqueries):
        new_fields = []
        cls._fields_map = {}
        cls._map_counter = 0
        for f_name, field in fields.iteritems():
            if f_name in cls._models:
                model_fields = cls._build_fields_rec(f_name, field)
                new_fields += model_fields
            elif f_name in subqueries:
                sub_fields = cls._build_fields_rec(f_name, field,
                                                     sub=subqueries[f_name][0])
                new_fields += sub_fields
            else:
                func = cls._build_func(f_name, field)
                new_fields.append(func)

    def _build(cls, query):
        query = copy.deepcopy(query)
        subs_joins = cls._build_subqueries_joins(query.pop('subqueries', {}))
        filter_ = cls._build_filter(query.pop('filter', {}))
        group = cls._build_group(query.pop('group', []))
        order = cls._build_order(query.pop('order', {}))
        distinct = query.pop('distinct', False)
        fields = cls._build_fields(query, subs_joins)
        query = AlquimiaQuery(*fields, session=cls._models.session)
        for join in subs_joins.values():
            query = query.join(*join)
        query = query.filter(*filter_).group_by(*group).order_by(order)
        if distinct:
            query = query.distinct()
        return query


class QueryBuilder(object):
    __metaclass__ = QueryBuilderMeta

    def __new__(cls, query, models):
        cls._models = models
        return cls._build(query)

    
class AlquimiaModels(dict):
    def __init__(self, db_url, dict_=None, data_types=DATA_TYPES,
                                                 create=False, logger=logging):
        engine = create_engine(db_url)
        base_model = declarative_base(engine, metaclass=AlquimiaModelMeta,
                         cls=AlquimiaModel, constructor=AlquimiaModel.__init__)
        self._session_class = sessionmaker(engine)
        self._session = self._session_class()
        self.metadata = base_model.metadata
        if dict_ is not None:
            attrs = ModelsAttributes(dict_, self.metadata, data_types, logger)
        else:
            attrs = ModelsAtrrsReflect(self.metadata, logger)
        self._build(base_model, attrs)
        if create:
            self.metadata.create_all()

    @property
    def session(self):
        return self._session

    def _build(self, base_model, models_attrs):
        models = {}
        for model_name, attrs in models_attrs.iteritems():
            attrs.update({'_session': self._session})
            model = type(model_name, (base_model,), attrs)
            models[model_name] = model

        for model in models.values():
            model.__mapper__.relationships
            for attr_name, attr in model.iteritems():
                if isinstance(attr.prop, RelationshipProperty):
                    setattr(attr, 'model', models[attr_name])
                else:
                    model.columns.append(attr_name)

        self.update(models)

    def clean(self):
        self._session.expunge_all()

    def query(self, dict_):
        return QueryBuilder(dict_, self)
