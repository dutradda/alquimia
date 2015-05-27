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


import jsonschema
import json
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy.orm.relationships import RelationshipProperty
from alquimia.model import AlquimiaModel, AlquimiaModelMeta
from alquimia import SCHEMA, DATA_TYPES


class ModelsAttributes(dict):
    def __init__(self, dict_, metadata, data_types=DATA_TYPES):
        self._data_types = data_types
        self._metadata = metadata
        self._build(dict_)

    @property
    def metadata(self):
        return self._metadata

    def _build_columns(self, model_name, model):
        model = model.copy()
        model.pop('relationships', None)
        cols = {}
        for col_name, column in model.iteritems():
            if not isinstance(column, dict):
                type_ = column
                column = {'args': [col_name, type_]}
            else:
                type_ = column.pop('type', None)
                if not type_:
                    raise TypeError('Column %s.%s type must be defined!' \
                                                      % (model_name, col_name))
                column['args'] = [col_name, type_]
            cols[col_name] = self._build_column_instance(column)
        id_column = {'args': ['id', 'integer'], 'primary_key': True, 'autoincrement': True}
        cols['id'] = self._build_column_instance(id_column)
        return cols

    def _build_relationships_dict(self, rels):
        new_rels = {}
        if not isinstance(rels, dict):
            for rel in rels:
                if not isinstance(rel, dict):
                    new_rels[rel] = {}
                elif rel.values()[0] == 'many-to-many':
                    new_rels[rel.keys()[0]] = {'many-to-many': True}
                elif rel.values()[0] == 'primary_key':
                    new_rels[rel.keys()[0]] = {'primary_key': True}
                else:
                    new_rels[rel.keys()[0]] = rel.values()[0]
        else:
            new_rels = rels
        return new_rels

    def _raises_one_to_one_error(self, model_name, rel_name):
        raise TypeError('%s.%s is a one-to-one relationship but ' \
                                  'was mapped as many-to-many!' % \
                                            (model_name, rel_name))
    
    def _build_many_to_many(self, model_name, rel_name, rel):
        if rel_name == model_name:
            self._raises_one_to_one_error(model_name, rel_name)        
        rel['secondary'] = '%s_%s_association' % (model_name, rel_name)
        rel['backref'] = {}
        rel['backref']['cascade'] = 'all'

    def _build_many_to_one(self, model_name, rel_name, rel, cols):
        if not model_name == rel_name:
            rel['backref'] = {}
            rel['backref']['cascade'] = 'all,delete-orphan'
        else:
            rel['uselist'] = False
            rel['remote_side'] = [cols['id']]

    def _build_relationship(self, model_name, rel_name, rel):
        rel['args'] = [rel_name]
        rel['cascade'] = 'all'
        if rel.has_key('backref'):
            rel['backref']['args'] = [model_name]

    def _build_relationship_column(self, rel_name, primary_key, many_to_many):
        if not many_to_many:
            foreign_key = {
                'args': [rel_name+'.id'],
                'onupdate': 'CASCADE',
                'ondelete': 'CASCADE'
            }
            column = {'args': [rel_name+'_id', 'integer', foreign_key]}
            if primary_key:
                column['primary_key'] = primary_key
            return self._build_column_instance(column)

    def _build_relationships(self, model_name, rels, cols):
        rels = self._build_relationships_dict(rels)
        for rel_name, rel in rels.iteritems():
            if cols.has_key(rel_name+'_id'):
                raise TypeError(rel+'_id is a alquimia primitive, '\
                                                               "don't use it!")
            if rel.get('many-to-many', False):
                self._build_many_to_many(model_name, rel_name, rel)
            else:
                self._build_many_to_one(model_name, rel_name, rel, cols)
            self._build_relationship(model_name, rel_name, rel)

            primary_key = rel.pop('primary_key', False)
            many_to_many = rel.pop('many-to-many', False)
            cols[rel_name+'_id'] = self._build_relationship_column(rel_name,
                                                     primary_key, many_to_many)
            if many_to_many:
                self._build_many_to_many_table(rel)
            rels[rel_name] = self._build_relationship_instance(rel)
        return rels

    def _build_column_instance(self, column):
        if len(column['args']) == 3:
            fk = column['args'][2]
            column['args'][2] = ForeignKey(*fk.pop('args'), **fk)
        column['args'][1] = self._data_types[column['args'][1]]
        return Column(*column.pop('args'), **column)

    def _build_relationship_instance(self, rel):
        if rel.has_key('backref'):
            br = rel['backref']
            rel['backref'] = backref(*br.pop('args'), **br)
        return relationship(*rel.pop('args'), **rel)

    def _build_many_to_many_table(self, relationship):
        rel1_name = relationship['backref']['args'][0]
        rel2_name = relationship['args'][0]
        table_name = relationship['secondary']
        col1 = Column(rel2_name+'_id', self._data_types['integer'],
           ForeignKey(rel2_name+'.id', onupdate='CASCADE', ondelete='CASCADE'))
        col2 = Column(rel1_name+'_id', self._data_types['integer'],
           ForeignKey(rel1_name+'.id', onupdate='CASCADE', ondelete='CASCADE'))
        Table(table_name, self._metadata, col1, col2)

    def _build(self, dict_):
        new_models = {}
        for model_name, model in dict_.iteritems():
            cols = self._build_columns(model_name, model)
            rels = model.get('relationships', {})
            rels = self._build_relationships(model_name, rels, cols)
            table = Table(model_name, self._metadata, *cols.values())
            new_models[model_name] = {}
            new_models[model_name]['__table__'] = table
            new_models[model_name].update(rels)
        self.update(new_models)


class AlquimiaModels(dict):
    def __init__(self, db_url, dict_, data_types=DATA_TYPES,
                                                    engine=None, create=False):
        if not engine:
            engine = create_engine(db_url)
        sa_base = declarative_base(engine, metaclass=AlquimiaModelMeta,
                                   cls=AlquimiaModel, constructor=AlquimiaModel.__init__)
        self._session = sessionmaker(engine)
        self._metadata = sa_base.metadata
        attrs = ModelsAttributes(dict_, self._metadata, data_types)
        self._build(sa_base, attrs)
        if create:
            self._metadata.create_all()

    @property
    def metadata(self):
        return self._metadata

    @property
    def session(self):
        return self._session
    

    def _build(self, sa_base, models_attrs):
        models = {}
        for model_name, attrs in models_attrs.iteritems():
            attrs.update({'session': self._session})
            model = type(model_name, (sa_base,), attrs)
            models[model_name] = model

        for model in models.values():
            for attr_name, attr in model.iteritems():
                if isinstance(attr.prop, RelationshipProperty):
                    setattr(attr, 'model', models[attr_name])

        self.update(models)
