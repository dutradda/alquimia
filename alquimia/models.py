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
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, sessionmaker
from sqlalchemy import Column, ForeignKey, MetaData, Table
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.orm import ColumnProperty
from alquimia.model import AlquimiaModel, AlquimiaModelMeta
from alquimia import SCHEMA, DATA_TYPES


class OneToOneManyToManyError(Exception):
    def __init__(self, model_name, rel_name, logger=logging):
        message = '%s.%s is a one-to-one relationship but ' \
                         'was mapped as many-to-many!' % (model_name, rel_name)
        log(logger, 'critical', message)
        Exception.__init__(self, message)


class AmbiguousRelationshipsError(Exception):
    def __init__(self, model_name, rel_name, logger=logging):
        message = "%s.%s and %s.%s relationships is ambiguous!" \
                                 % (model_name, rel_name, rel_name, model_name)
        log(logger, 'critical', message)
        Exception.__init__(self, message)


def log(logger, level, message):
    levels = {
        'info': logger.info,
        'warning': logger.warning,
        'error': logger.error,
        'critical': logger.critical,
        'debug': logger.debug
    }
    levels[level]('Alquimia:%s' % message)


class ModelsAtrrsReflect(dict):
    def __init__(self, metadata, logger=logging, *args):
        self._logger = logger
        self._metadata = metadata
        self._rels = {}
        self._build(*args)

    def _build_rel_instance(self, rel_name, table_name, update_kargs={}):
        kwargs = {'cascade': 'all'}
        kwargs.update(update_kargs)
        self[table_name][rel_name] = relationship(rel_name, **kwargs)

    def _add_rel(self, rel_type, rel_name, table_name, args={}):
        self[table_name][rel_type].append(rel_name)
        self[table_name]['relationships'].append(rel_name)
        self._build_rel_instance(rel_name, table_name, args)

    def _build_many_to_many_rel(self, rel_name, table_name, mtm_table):
        if rel_name == table_name:
            raise OneToOneManyToManyError(table_name, rel_name)
        args = {'secondary': mtm_table}
        self._add_rel('mtm', rel_name, table_name, args)
        self._add_rel('mtm', table_name, rel_name, args)

    def _build_many_to_one_rel(self, rel_name, table_name):
        self._add_rel('mto', rel_name, table_name)
        args = {'cascade': 'all,delete-orphan'}
        self._add_rel('otm', table_name, rel_name, args)
        
    def _build_one_to_one_rel(self, rel_name, table_name, id_column=None):
        args = {'uselist': False, 'single_parent': True,
                'cascade': 'all,delete-orphan'}
        if id_column is not None:
            args['remote_side'] = [id_column]
        self._add_rel('oto', rel_name, table_name, args)
        if not rel_name == table_name:
            self._add_rel('oto', table_name, rel_name, args)

    def _build_relationships(self, table):
        for fk in table.foreign_keys:
            rel_name = fk.column.table.name
            id_column = table.c['id'] if rel_name == table.name else None
            if id_column is not None or fk.parent.unique:
                self._build_one_to_one_rel(rel_name, table.name, id_column)
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
    def __init__(self, dict_, metadata, data_types=DATA_TYPES, logger=logging):
        jsonschema.validate(dict_, SCHEMA)
        self._data_types = data_types
        ModelsAtrrsReflect.__init__(self, metadata, logger, *[dict_])

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
            if isinstance(rels, str):
                rels = [rels]
            for rel in rels:
                self._build_rel_attr_dict(new_rels, rel)
        else:
            for k, v in rels.iteritems():
                self._build_rel_attr_dict(new_rels, {k: v})
        return new_rels

    def _build_relationship_column(self, rel_name, model_name, primary_key, oto):
        foreign_key = {
            'args': [rel_name+'.id'],
            'onupdate': 'CASCADE',
            'ondelete': 'CASCADE'
        }
        rel_col_name = rel_name+'_id'
        column = {'args': [rel_col_name, 'integer', foreign_key],
                  'autoincrement': False}
        if primary_key:
            column['primary_key'] = True
        if oto:
            column['unique'] = True
        self._build_column_instance(column, rel_col_name, model_name)

    def _build_relationships(self, model_name, rels_dict):
        rels = {}
        for rel_name, rel in rels_dict.iteritems():
            if rel.pop('many-to-many', False):
                mtm_table_name = '%s_%s_association' % \
                                                     (model_name, rel_name)
                self._build_many_to_many_table(model_name, rel_name,
                                                            mtm_table_name)
                self._build_many_to_many_rel(rel_name,
                                                model_name, mtm_table_name)
            else:
                is_oto = rel.pop('one-to-one', False) or rel_name == model_name
                self._build_relationship_column(rel_name, model_name,
                                         rel.pop('primary_key', False), is_oto)
                if is_oto:
                    id_column = self[model_name]['id'] \
                                            if rel_name == model_name else None
                    self._build_one_to_one_rel(rel_name, model_name, id_column)
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

    def _check_rels(self, models_rels):
        new_mr = {m: r.copy() for m, r in models_rels.iteritems()}
        for mdl_name, rels in models_rels.iteritems():
            for rel_name, rel in rels.iteritems():
                if mdl_name in new_mr[rel_name] and mdl_name != rel_name:
                    rel2 = models_rels[rel_name][mdl_name]
                    rel_mtm = rel.get('many-to-many', False)
                    rel2_mtm = rel2.get('many-to-many', False)
                    rel_oto = rel.get('one-to-one', False)
                    rel2_oto = rel2.get('one-to-one', False)
                    if (not rel_mtm or not rel2_mtm) and \
                                                (not rel_oto or not rel2_oto):
                        raise AmbiguousRelationshipsError(mdl_name, rel_name)
                    message = 'Removed relationship %s.%s duplicated from '\
                             '%s.%s' % (mdl_name, rel_name, rel_name, mdl_name)
                    log(self._logger, 'warning', message)
                    new_mr[mdl_name].pop(rel_name)
        models_rels.clear()
        models_rels.update(new_mr)

    def _build(self, dict_):
        models_rels = {}
        for model_name, model in dict_.iteritems():
            rels = model.get('relationships', {})
            models_rels[model_name] = self._build_relationships_dict(rels)
            self._init_attrs(model_name)
        self._check_rels(models_rels)

        for model_name, model in dict_.iteritems():
            self._build_columns(model_name, model)
            self._build_relationships(model_name, models_rels[model_name])
            self[model_name]['__tablename__'] = model_name


class AlquimiaSession(object):
    def __init__(self, engine):
        self._session_class = sessionmaker(engine)
        self._session = self._session_class()

    def delete(self, *args, **kwargs):
        return self._session.delete(*args, **kwargs)

    def query(self, *args, **kwargs):
        return self._session.query(*args, **kwargs)

    def commit(self, *args, **kwargs):
        return self._session.commit(*args, **kwargs)

    def rollback(self, *args, **kwargs):
        return self._session.rollback(*args, **kwargs)

    def add(self, *args, **kwargs):
        return self._session.add(*args, **kwargs)

    def clean(self):
        self._session.close()
        self._session = self._session_class()


class AlquimiaModels(dict):
    def __init__(self, db_url, dict_=None, data_types=DATA_TYPES,
                                    engine=None, create=False, logger=logging):
        if not engine:
            engine = create_engine(db_url)
        base_model = declarative_base(engine, metaclass=AlquimiaModelMeta,
                         cls=AlquimiaModel, constructor=AlquimiaModel.__init__)
        self._session = AlquimiaSession(engine)
        self.metadata = base_model.metadata
        if dict_ is not None:
            attrs = ModelsAttributes(dict_, self.metadata, data_types, logger)
        else:
            attrs = ModelsAtrrsReflect(self.metadata, logger)
        self._build(base_model, attrs)
        if create:
            self.metadata.create_all()

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
                elif isinstance(attr.prop, ColumnProperty):
                    model.columns.append(attr_name)

        self.update(models)

    def clean(self):
        self._session.clean()
