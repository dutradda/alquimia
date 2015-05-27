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


import pytest
import sqlalchemy
import json
from alquimia import AlquimiaModels
from alquimia.models import ModelsAttributes
from tests.models_fixtures import (user_models, models_attributes, models,
                                   t1_simple_obj, t1_t2_obj,
                                   t1_t2_update, t1_t2_query)
from tests.models_expected import attributes_expected, models_expected

class TestModelsAttributes(object):
    def _test_foreign_key(self, fk1, fk2):
        assert len(fk1) == len(fk2)
        assert not len(fk1) > 1
        if len(fk1) == 1:
            fk1 = list(fk1)[0]
            fk2 = list(fk2)[0]
            assert fk1.onupdate == fk2.onupdate
            assert fk1.ondelete == fk2.ondelete
            self._test_column(fk1.column, fk2.column, False)
            self._test_column(fk1.parent, fk2.parent, False)

    def _test_column(self, column1, column2, test_fk=True):
        assert column1.name == column2.name
        assert column1.type.python_type == column2.type.python_type
        assert column1.primary_key == column2.primary_key
        assert column1.nullable == column2.nullable
        assert column1.autoincrement == column2.autoincrement
        assert column1.unique == column2.unique
        if isinstance(column1.default, sqlalchemy.schema.ColumnDefault):
            assert column1.default.arg == column2.default.arg
        else:
            assert column1.default == column2.default
        if test_fk:
            self._test_foreign_key(column1.foreign_keys, column2.foreign_keys)

    def _test_relationship(self, rel1, rel2):
        assert rel1.argument == rel2.argument
        assert rel1.lazy == rel2.lazy
        assert rel1.innerjoin == rel2.innerjoin
        assert rel1.order_by == rel2.order_by
        rs = (rel1.remote_side and rel2.remote_side)
        assert rs is None or rs
        if rs:
            assert len(rel1.remote_side) == len(rel2.remote_side) == 1
            self._test_column(rel1.remote_side[0], rel2.remote_side[0])
        assert rel1.cascade == rel2.cascade
        assert rel1.backref == rel2.backref

    def test_models_attributes(self, models_attributes):
        tables = models_attributes.metadata.sorted_tables
        tables_exp = attributes_expected.metadata.sorted_tables
        assert len(tables) == len(tables_exp)
        
        for i in range(len(tables)):
            for col_name, col in tables[i].columns.items():
                col_exp = tables_exp[i].columns[col_name]
                self._test_column(col, col_exp)
                        
        for model_name, model in models_attributes.iteritems():
            attrs_expected = attributes_expected[model_name]
            model.pop('__table__')
            attrs_expected.pop('__table__')
            for rel_name, rel in model.iteritems():
                rel_exp = attrs_expected[rel_name]
                self._test_relationship(rel, rel_exp)


class TestAlquimiaModels(object):
    def test_models(self, models):
        tables = models.metadata.sorted_tables
        tables_exp = models_expected.metadata.sorted_tables
        assert len(tables) == len(tables_exp)

        for model_name, model in models.iteritems():
            rels = model.__mapper__.relationships
            model_expected = models_expected[model_name]
            rels_exp = model_expected.__mapper__.relationships
            assert len(rels) == len(rels_exp)


class TestAlquimiaModel(object):
    def test_init_model(self, models, t1_simple_obj):
        obj = models['t1'](**t1_simple_obj)
        assert obj['c1'] == t1_simple_obj['c1']
        assert obj['c2'] == t1_simple_obj['c2']
        assert obj['c4'] == t1_simple_obj['c4']

    def test_init_rec(self, models, t1_t2_obj):
        obj = models['t1'](**t1_t2_obj)
        assert type(obj['t2']) == models['t2']
        assert obj['t2']['c1'] == t1_t2_obj['t2']['c1']

    def test_model_repr(self, models, t1_t2_obj):
        obj = models['t1'].insert(t1_t2_obj)
        t1 = dict(obj[0])
        t1['t2'] = dict(t1['t2'])
        assert repr(t1) == repr(obj[0])


class TestAlquimiaModelMeta(object):
    def test_modelmeta_insert(self, models, t1_t2_obj):
        model = models['t1']
        model.insert(t1_t2_obj)
        s = model.session()
        nobj = s.query(model).all()[1]
        assert nobj['c1'] == t1_t2_obj['c1']
        assert nobj['c2'] == t1_t2_obj['c2']
        assert nobj['c4'] == t1_t2_obj['c4']
        assert nobj['t2']['c1'] == t1_t2_obj['t2']['c1']
            
    def test_modelmeta_delete(self, models, t1_t2_obj):
        models['t1'].insert(t1_t2_obj)
        model = models['t1']
        s = model.session()
        assert len(s.query(model).all()) == 2
        obj = s.query(model).filter(model.c4 == 'test11').one()
        model.delete(obj.id)
        s.close()
        s = model.session()
        assert len(s.query(model).all()) == 0

    def test_modelmeta_update(self, models, t1_t2_obj, t1_t2_update):
        model = models['t1']
        model.insert(t1_t2_obj)
        s = model.session()
        id_ = s.query(models['t1'].id).filter(models['t1'].c4 == 'test1').one()[0]
        t1_t2_update.update({'id': id_})
        model.update(t1_t2_update)
        s = model.session()
        obj = s.query(model).filter(model.id == id_).one()
        assert obj['c4'] == t1_t2_update['c4']
        assert obj['t2']['c1'] == t1_t2_update['t2']['c1']

    def test_modelmeta_query(self, models, t1_t2_query, t1_t2_obj):
        models['t1'].insert(t1_t2_obj)
        query = models['t1'].query(t1_t2_query)
        assert query['c4'] == t1_t2_query['c4']
        assert query['t2']['c1'] == t1_t2_query['t2']['c1']
