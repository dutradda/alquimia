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
from sqlalchemy.orm import relationship
from alquimia.log import log


class OneToOneManyToManyError(Exception):
    def __init__(self, model_name, rel_name, logger=logging):
        message = '%s.%s is a one-to-one relationship but ' \
                         'was mapped as many-to-many!' % (model_name, rel_name)
        log(logger, 'critical', message)
        Exception.__init__(self, message)


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
