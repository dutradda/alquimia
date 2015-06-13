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
from tests.models_expected import models_expected, rels_expected, todict_expected
from alquimia import AlquimiaModels
from alquimia.models import OneToOneManyToManyError, AmbiguousRelationshipsError
from jsonschema import ValidationError


class TestAlquimiaModel(object):
    def test_init_model(self, models, t1_t2_obj):
        obj = models['t1'](**t1_t2_obj)
        obj.save()
        assert obj['c1'] == t1_t2_obj['c1']
        assert obj['c2'] == t1_t2_obj['c2']
        assert obj['c4'] == t1_t2_obj['c4']
        obj.remove()

    def test_init_rec(self, models, t1_t2_obj):
        obj = models['t1'](**t1_t2_obj)
        assert type(obj['t2']) == models['t2']
        assert obj['t2']['c1'] == t1_t2_obj['t2']['c1']

    def test_model_todict(self, models, t1_t2_obj):
        models['t1'].insert(t1_t2_obj)
        obj = models['t2'].query({'c1': 'test12'})[0]
        todict_expected['id'] = obj['id']
        todict_expected['t1'][0]['id'] = obj['t1'][0]['id']
        todict_expected['t1'][0]['t2'] = todict_expected['t1'][0]['t2'] % obj['id']
        todict_expected['t1'][0]['t1_id'] = obj['t1'][0]['t1_id']
        todict_expected['t1'][0]['t2_id'] = obj['t1'][0]['t2_id']
        todict_expected['t1'][0]['t1']['id'] = obj['t1'][0]['t1']['id']
        todict_expected['t1'][0]['t1']['t2_id'] = obj['t1'][0]['t1']['t2_id']
        todict_expected['t1'][0]['t1']['t2']['id'] = obj['t1'][0]['t1']['t2']['id']
        todict_expected['t1'][0]['t1']['t2']['t1'][0] = todict_expected['t1'][0]['t1']['t2']['t1'][0] % obj['t1'][0]['t1']['id']
        assert obj.todict(-1) == todict_expected

    def test_model_repr(self, models, t1_t2_obj):
        models['t1'].insert(t1_t2_obj)
        obj = models['t2'].query({'c1': 'test12'})[0]
        exp = "{'t6': '<0 object(s)>', 'c1': 'test12', " \
              "'id': %dL, 't1': '<1 object(s)>'}" % obj['id']
        assert repr(obj) == exp

    def test_iterator(self, models, t1_t2_obj):
        obj = models['t1'](**t1_t2_obj)
        obj.save()
        for attr in obj:
            assert obj.has_key(attr)
        obj.remove()


class TestAlquimiaModelMeta(object):
    def test_modelmeta_insert(self, models, t1_t2_obj):
        model = models['t1']
        model.insert(t1_t2_obj)
        s = model._session
        nobj = s.query(model).all()[1]
        assert nobj['c1'] == t1_t2_obj['c1']
        assert nobj['c2'] == t1_t2_obj['c2']
        assert nobj['c4'] == t1_t2_obj['c4']
        assert nobj['t2']['c1'] == t1_t2_obj['t2']['c1']

    def test_modelmeta_insert_invalid(self, models, invalid_obj):
        with pytest.raises(TypeError):
            models['t1'].insert(invalid_obj)

    def test_modelmeta_insert_list(self, models, t1_t2_obj):
        ins = models['t1'].insert([t1_t2_obj])
        assert isinstance(ins, list) and len(ins) == 1

    def test_modelmeta_delete(self, models, t1_t2_obj):
        models['t1'].insert(t1_t2_obj)
        model = models['t1']
        s = model._session
        assert len(s.query(model).all()) == 2
        obj = s.query(model).filter(model.c4 == 'test11').one()
        model.delete(obj.id)
        s = model._session
        assert len(s.query(model).all()) == 0

    def test_modelmeta_delete_list(self, models, t1_t2_obj):
        models['t1'].insert(t1_t2_obj)
        model = models['t1']
        s = model._session
        assert len(s.query(model).all()) == 2
        obj = s.query(model).filter(model.c4 == 'test11').one()
        model.delete([obj.id])
        s = model._session
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
        s = model._session
        id_ = s.query(models['t1'].id).filter(models['t1'].c4 == 'test1').one()[0]
        t1_t2_update.update({'id': id_})
        model.update(t1_t2_update)
        s = model._session
        obj = s.query(model).filter(model.id == id_).one()
        assert obj['c4'] == t1_t2_update['c4']
        assert obj['t2']['c1'] == t1_t2_update['t2']['c1']

    def test_modelmeta_update_list(self, models, t1_t2_obj, t1_t2_update):
        model = models['t1']
        model.insert(t1_t2_obj)
        s = model._session
        id_ = s.query(models['t1'].id).filter(models['t1'].c4 == 'test1').one()[0]
        t1_t2_update.update({'id': id_})
        model.update([t1_t2_update])
        s = model._session
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
        obj = dict(model.insert(t1_t2_obj)['t1'])
        obj['test'] = 'test'
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