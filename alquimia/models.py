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
from abc import ABCMeta
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.orm import ColumnProperty
from alquimia.model import AlquimiaModel, AlquimiaModelMeta
from alquimia import SCHEMA, DATA_TYPES


class ModelsAtrrsReflect(dict):
    __metaclass__ = ABCMeta

    def __init__(self, metadata, *args):
        self._metadata = metadata
        self._rels = {}
        self._build(*args)

    @property
    def metadata(self):
        return self._metadata

    def _build_rel_args(self, rel_name, cascade='all'):
        args = {}
        args['args'] = [rel_name]
        args['cascade'] = cascade
        return args

    def _build_rel_instance(self, args, rel_name, table_name):
        self[table_name][rel_name] = relationship(*args.pop('args'), **args)

    def _raises_one_to_one_error(self, model_name, rel_name):
        raise TypeError('%s.%s is a one-to-one relationship but ' \
                                  'was mapped as many-to-many!' % \
                                            (model_name, rel_name))

    def _build_many_to_many_rel(self, rel_name, table_name, mtm_table):
        if rel_name == table_name:
            self._raises_one_to_one_error(table_name, rel_name)
        self[table_name]['mtm'].append(rel_name)
        self[rel_name]['mtm'].append(table_name)
        self[table_name]['relationships'].append(rel_name)
        self[rel_name]['relationships'].append(table_name)
        args = self._build_rel_args(rel_name)
        args['secondary'] = mtm_table
        args_br = self._build_rel_args(table_name)
        args_br['secondary'] = mtm_table
        self._build_rel_instance(args, rel_name, table_name)
        self._build_rel_instance(args_br, table_name, rel_name) # backref

    def _build_many_to_one_rel(self, rel_name, table_name):
        self[table_name]['mto'].append(rel_name)
        self[rel_name]['otm'].append(table_name)
        self[table_name]['relationships'].append(rel_name)
        self[rel_name]['relationships'].append(table_name)
        args = self._build_rel_args(rel_name)
        args_br = self._build_rel_args(table_name, 'all,delete-orphan')
        self._build_rel_instance(args, rel_name, table_name)
        self._build_rel_instance(args_br, table_name, rel_name)
    
    def _build_one_to_one_rel(self, rel_name, table_name, id_column):
        self[table_name]['oto'].append(rel_name)
        self[table_name]['relationships'].append(rel_name)
        args = self._build_rel_args(rel_name)
        args['uselist'] = False
        args['remote_side'] = [id_column]
        self._build_rel_instance(args, rel_name, table_name)

    def _build_relationships(self, table):
        for fk in table.foreign_keys:
            rel_name = fk.column.table.name
            if rel_name == table.name:
                self._build_one_to_one_rel(rel_name, table.name,
                                                                 table.c['id'])
            else:
                self._build_many_to_one_rel(rel_name, table.name)
        mtm_tables = list(self._mtm_tables.values())
        for mtm_table in mtm_tables:
            mtm_rels = list(mtm_table.columns.keys())
            table_rel = table.name+'_id'
            if table_rel in mtm_rels:
                mtm_rels.remove(table_rel)
                rel_name = mtm_rels[0][:-3]
                self._build_many_to_many_rel(rel_name, table.name,
                                                                mtm_table.name)
                self._mtm_tables.pop(mtm_table.name)

    def _keep_mtm_tables(self):
        self._mtm_tables = {}
        for table in self._metadata.tables.values():
            fks = table.foreign_keys
            if len(fks) == len(table.c) == 2:
                is_pks = True
                for fk in fks:
                    if not fk.column.primary_key:
                        is_pks = False
                        break
                if not is_pks:
                    continue
                self._mtm_tables[table.name] = table

    def _init_attrs(self, table_name):
        self[table_name] = {
            'mtm': [],
            'mto': [],
            'oto': [],
            'otm': [],
            'relationships': [],
            'columns': [],
            'session': None
        }

    def _build(self, *args):
        self._metadata.reflect()
        self._keep_mtm_tables()
        attrs = {}
        tables = [table for table in self._metadata.tables.values() \
                                         if table.name not in self._mtm_tables]
        for table in tables:
            self._init_attrs(str(table.name))

        for table in tables:
            if table.name not in self._mtm_tables:
                self._build_relationships(table)
                self[table.name]['__table__'] = table


class ModelsAttributes(ModelsAtrrsReflect):
    def __init__(self, dict_, metadata, data_types=DATA_TYPES):
        jsonschema.validate(dict_, SCHEMA)
        self._data_types = data_types
        ModelsAtrrsReflect.__init__(self, metadata, *[dict_])

    def _build_columns(self, model_name, model):
        new_model = {}
        for k, v in model.iteritems():
            new_model[k] = type(v)(v)
        model = new_model
        model.pop('relationships', None)
        model['id'] = {'type': 'integer', 'primary_key': True}
        for col_name, column in model.iteritems():
            if not isinstance(column, dict):
                type_ = column
                column = {'args': [col_name, type_]}
            else:
                column['args'] = [col_name, column.pop('type')]
            self._build_column_instance(column, col_name, model_name)

    def _build_rel_attr_dict(self, new_rels, rel):
        if not isinstance(rel, dict):
            new_rels[rel] = {}
        elif not isinstance(rel.values()[0], dict):
            new_rels[rel.keys()[0]] = {rel.values()[0]: True}
        else:
            new_rels[rel.keys()[0]] = rel.values()[0].copy()

    def _build_relationships_dict(self, rels):
        new_rels = {}
        if not isinstance(rels, dict):
            for rel in rels:
                self._build_rel_attr_dict(new_rels, rel)
        else:
            for k, v in rels.iteritems():
                self._build_rel_attr_dict(new_rels, {k: v})
        return new_rels

    def _build_relationship_column(self, rel_name, model_name, primary_key):
        foreign_key = {
            'args': [rel_name+'.id'],
            'onupdate': 'CASCADE',
            'ondelete': 'CASCADE'
        }
        rel_col_name = rel_name+'_id'
        column = {'args': [rel_col_name, 'integer', foreign_key],
                  'autoincrement': False}
        if primary_key:
            column['primary_key'] = primary_key
        self._build_column_instance(column, rel_col_name, model_name)

    def _build_relationships(self, model_name, rels_model):
        rels_dict = self._build_relationships_dict(rels_model)
        rels = {}
        for rel_name, rel in rels_dict.iteritems():
            mtm_table_name = rel.pop('many-to-many', None)
            if mtm_table_name is not None:
                if not self[model_name].has_key(rel_name):
                    mtm_table_name = '%s_%s_association' % \
                                                         (model_name, rel_name)
                    self._build_many_to_many_table(model_name, rel_name,
                                                                mtm_table_name)
                    self._build_many_to_many_rel(rel_name,
                                                    model_name, mtm_table_name)
            else:
                primary_key = rel.pop('primary_key', False)
                self._build_relationship_column(rel_name, model_name,
                                                                   primary_key)
                if rel_name == model_name:
                    self._build_one_to_one_rel(rel_name, model_name,
                                                        self[model_name]['id'])
                else:
                    self._build_many_to_one_rel(rel_name, model_name)
        return rels

    def _build_column_instance(self, column, col_name, model_name):
        if len(column['args']) == 3:
            fk = column['args'][2]
            column['args'][2] = ForeignKey(*fk.pop('args'), **fk)
        column['args'][1] = self._data_types[column['args'][1]]
        self[model_name][col_name] = Column(*column.pop('args'), **column)

    def _build_many_to_many_table(self, rel1_name, rel2_name, table_name):
        col1 = Column(rel2_name+'_id', self._data_types['integer'],
           ForeignKey(rel2_name+'.id', onupdate='CASCADE', ondelete='CASCADE'),
           primary_key=True, autoincrement=False)
        col2 = Column(rel1_name+'_id', self._data_types['integer'],
           ForeignKey(rel1_name+'.id', onupdate='CASCADE', ondelete='CASCADE'),
           primary_key=True, autoincrement=False)
        Table(table_name, self._metadata, col1, col2)

    def _build(self, dict_):
        for model_name in dict_.keys():
            self._init_attrs(model_name)

        for model_name, model in dict_.iteritems():
            self._build_columns(model_name, model)
            rels = model.get('relationships', {})
            self._build_relationships(model_name, rels)
            self[model_name]['__tablename__'] = model_name


class AlquimiaModels(dict):
    def __init__(self, db_url, dict_=None, data_types=DATA_TYPES,
                                                    engine=None, create=False):
        if not engine:
            engine = create_engine(db_url)
        base_model = declarative_base(engine, metaclass=AlquimiaModelMeta,
                         cls=AlquimiaModel, constructor=AlquimiaModel.__init__)
        self._session_class = sessionmaker(engine)
        self._session = self._session_class()
        self._metadata = base_model.metadata
        if dict_ is not None:
            attrs = ModelsAttributes(dict_, self._metadata, data_types)
        else:
            attrs = ModelsAtrrsReflect(self._metadata)
        self._build(base_model, attrs)
        if create:
            self._metadata.create_all()

    @property
    def metadata(self):
        return self._metadata

    @property
    def session(self):
        return self._session

    def _build(self, base_model, models_attrs):
        models = {}
        for model_name, attrs in models_attrs.iteritems():
            attrs.update({'session': self.session})
            model = type(model_name, (base_model,), attrs)
            models[model_name] = model

        for model in models.values():
            model.__mapper__.relationships
            for attr_name, attr in model.iteritems():
                if isinstance(attr.prop, RelationshipProperty):
                    setattr(attr, 'model', models[attr_name])
                elif isinstance(attr.prop, ColumnProperty):
                    model.columns.append(attr_name)

        self.update(models)
