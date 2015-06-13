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


import pytest


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

    def test_modelmeta_iterator(self, models, t1_t2_obj):
        for attr in models['t1']:
            assert attr
        for k, v in models['t1'].items():
            assert models['t1'][k]
        models['t1'].values()

    def test_modelmeta_all(self, models, t1_t2_obj):
        o1 = models['t1'].insert(t1_t2_obj)
        o2 = models['t1'].insert(t1_t2_obj)
        o3 = models['t1'].insert(t1_t2_obj)
        all_ = models['t1'].all()
        assert len(all_) == 6
        all_exp = [o1, o2, o3, o1['t1'], o2['t1'], o3['t1']]
        all_.sort()
        all_exp.sort()
        assert all_ == all_exp
