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
from tests.models_expected import models_expected
from alquimia import AlquimiaModels
from jsonschema import ValidationError

class TestAlquimiaModels(object):
    def _check_foreign_key(self, fk1, fk2):
        assert len(fk1) == len(fk2)
        assert not len(fk1) > 1
        if len(fk1) == 1:
            fk1 = list(fk1)[0]
            fk2 = list(fk2)[0]
            assert fk1.onupdate == fk2.onupdate
            assert fk1.ondelete == fk2.ondelete
            self._check_column(fk1.column, fk2.column, False)
            self._check_column(fk1.parent, fk2.parent, False)

    def _check_column(self, column1, column2, test_fk=True, reflect=False):
        assert column1.name == column2.name
        c1_type = column1.type.python_type
        c2_type = column2.type.python_type
        if not ((c1_type == int and c2_type == bool) or \
                                         (c2_type == int and c1_type == bool)):
            assert column1.type.python_type == column2.type.python_type
        assert column1.primary_key == column2.primary_key
        assert column1.nullable == column2.nullable
        assert bool(column1.autoincrement) == bool(column2.autoincrement)
        assert column1.unique == column2.unique
        if isinstance(column1.default, sqlalchemy.schema.ColumnDefault):
            assert column1.default.arg == column2.default.arg
        elif column1.default is not None:
            assert column1.default == column2.default
        if test_fk:
            self._check_foreign_key(column1.foreign_keys, column2.foreign_keys)

    def _check_tables(self, tables, tables_exp):
        for i in range(len(tables)):
            for col_name, col in tables[i].columns.items():
                col_exp = tables_exp[i].columns[col_name]
                self._check_column(col, col_exp)

    def _check_relationship(self, rel1, rel2):
        rel1.table.name == rel2.table.name
        assert rel1.lazy == rel2.lazy
        assert rel1.innerjoin == rel2.innerjoin
        assert rel1.order_by == rel2.order_by
        rs = (rel1.remote_side and rel2.remote_side)
        assert rs is None or rs
        if rs and len(rel1.remote_side) == len(rel2.remote_side) == 1:
            self._check_column(list(rel1.remote_side)[0], list(rel2.remote_side)[0])
        assert rel1.cascade == rel2.cascade
        if rel1.secondary is not None and rel2.secondary is not None:
            self._check_tables([rel1.secondary], [rel2.secondary])

    def _check_models(self, models):
        tables = models.metadata.sorted_tables
        tables_exp = models_expected.metadata.sorted_tables
        assert len(tables) == len(tables_exp)
        self._check_tables(tables, tables_exp)

        for model_name, model in models.iteritems():
            rels = model.__mapper__.relationships
            rels_exp = models_expected[model_name].__mapper__.relationships
            assert len(rels) == len(rels_exp) == len(model.relationships)
            for rel_name in model.relationships:
                rel_exp = getattr(models_expected[model_name], rel_name).prop
                self._check_relationship(model[rel_name].prop, rel_exp)

    def test_create(self, models_create):
        self._check_models(models_create)

    def test_models(self, models):
        self._check_models(models)
    
    def test_models_reflect(self, models_reflect):
        self._check_models(models_reflect)

    def test_models_oto_error(self, user_models_oto_error, db_uri):
        with pytest.raises(TypeError):
            AlquimiaModels(db_uri, user_models_oto_error)

    def test_models_col__id_error(self, user_models_col__id_error, db_uri):
        with pytest.raises(ValidationError):
            AlquimiaModels(db_uri, user_models_col__id_error)

    def test_models_no_type_error(self, user_models_no_type_error, db_uri):
        with pytest.raises(ValidationError):
            AlquimiaModels(db_uri, user_models_no_type_error)

    def test_models_invalid_attribute_error(self, user_models_invalid_attribute_error, db_uri):
        with pytest.raises(ValidationError):
            AlquimiaModels(db_uri, user_models_invalid_attribute_error)


class TestAlquimiaModel(object):
    def test_init_model(self, models, t1_t2_obj):
        obj = models['t1'](**t1_t2_obj)
        obj.save()
        assert obj['c1'] == t1_t2_obj['c1']
        assert obj['c2'] == t1_t2_obj['c2']
        assert obj['c4'] == t1_t2_obj['c4']
        obj.delete_()

    def test_init_rec(self, models, t1_t2_obj):
        obj = models['t1'](**t1_t2_obj)
        assert type(obj['t2']) == models['t2']
        assert obj['t2']['c1'] == t1_t2_obj['t2']['c1']

    def test_model_repr(self, models, t1_t2_obj):
        obj = models['t1'].insert(t1_t2_obj)
        t1 = dict(obj[0])
        t1['t2'] = dict(t1['t2'])
        assert repr(t1) == repr(obj[0])

    def test_iterator(self, models, t1_t2_obj):
        obj = models['t1'](**t1_t2_obj)
        obj.save()
        for attr in obj:
            assert obj.has_key(attr)
        obj.delete_()


class TestAlquimiaModelMeta(object):
    def test_modelmeta_insert(self, models, t1_t2_obj):
        model = models['t1']
        model.insert(t1_t2_obj)
        s = model.session
        nobj = s.query(model).all()[1]
        assert nobj['c1'] == t1_t2_obj['c1']
        assert nobj['c2'] == t1_t2_obj['c2']
        assert nobj['c4'] == t1_t2_obj['c4']
        assert nobj['t2']['c1'] == t1_t2_obj['t2']['c1']

    def test_modelmeta_insert_invalid(self, models, invalid_obj):
        with pytest.raises(TypeError):
            models['t1'].insert(invalid_obj)
            
    def test_modelmeta_delete(self, models, t1_t2_obj):
        models['t1'].insert(t1_t2_obj)
        model = models['t1']
        s = model.session
        assert len(s.query(model).all()) == 2
        obj = s.query(model).filter(model.c4 == 'test11').one()
        model.delete(obj.id)
        s.close()
        s = model.session
        assert len(s.query(model).all()) == 0

    def test_modelmeta_delete_invalid(self, models, invalid_obj):
        with pytest.raises(TypeError):
            models['t1'].delete(invalid_obj)

    def test_modelmeta_delete_invalid_id(self, models):
        with pytest.raises(TypeError):
            models['t1'].delete('test')

    def test_modelmeta_update(self, models, t1_t2_obj, t1_t2_update):
        model = models['t1']
        model.insert(t1_t2_obj)
        s = model.session
        id_ = s.query(models['t1'].id).filter(models['t1'].c4 == 'test1').one()[0]
        t1_t2_update.update({'id': id_})
        model.update(t1_t2_update)
        s = model.session
        obj = s.query(model).filter(model.id == id_).one()
        assert obj['c4'] == t1_t2_update['c4']
        assert obj['t2']['c1'] == t1_t2_update['t2']['c1']

    def test_modelmeta_update_no_id(self, models, invalid_obj):
        model = models['t1']
        with pytest.raises(KeyError):
            model.update(invalid_obj)

    def test_modelmeta_update_invalid_id(self, models, invalid_obj):
        invalid_obj['id'] = 1
        model = models['t1']
        with pytest.raises(TypeError) as e:
            model.update(invalid_obj)

    def test_modelmeta_update_invalid_obj(self, models, t1_t2_obj):
        model = models['t1']
        obj = dict(model.insert(t1_t2_obj)[0]['t1'])
        obj['test'] = 'test'
        print obj
        with pytest.raises(TypeError) as e:
            model.update(obj)
    
    def test_modelmeta_query(self, models, t1_t2_query, t1_t2_obj):
        models['t1'].insert(t1_t2_obj)
        query = models['t1'].query(t1_t2_query)
        assert len(query) == 1
        query = query[0]
        assert query['c4'] == t1_t2_query['c4']
        assert query['t2']['c1'] == t1_t2_query['t2']['c1']

    def test_modelmeta_query_invalid_obj(self, models, invalid_obj):
        with pytest.raises(KeyError):
            models['t1'].query(invalid_obj)

    def test_modelmeta_query_4(self, models, t1_t2_query, t1_t2_obj):
        models['t1'].insert(t1_t2_obj)
        models['t1'].insert(t1_t2_obj)
        models['t1'].insert([t1_t2_obj, t1_t2_obj])
        query = models['t1'].query(t1_t2_query)
        assert len(query) == 4
        query = query[0]
        assert query['c4'] == t1_t2_query['c4']
        assert query['t2']['c1'] == t1_t2_query['t2']['c1']

    def test_iterator(self, models, t1_t2_obj):
        for attr in models['t1']:
            assert attr
        for k, v in models['t1'].items():
            assert models['t1'][k]
        models['t1'].values()