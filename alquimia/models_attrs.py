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


import jsonschema
import logging
from sqlalchemy.orm import relationship
from sqlalchemy import Column, ForeignKey, Table
from alquimia import SCHEMA, DATA_TYPES
from alquimia.utils import log
from alquimia.models_attrs_reflect import ModelsAtrrsReflect


class AmbiguousRelationshipsError(Exception):
    def __init__(self, model_name, rel_name, logger=logging):
        message = "%s.%s and %s.%s relationships is ambiguous!" \
                                 % (model_name, rel_name, rel_name, model_name)
        log(logger, 'critical', message)
        Exception.__init__(self, message)


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
