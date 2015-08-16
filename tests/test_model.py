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


import copy
import pytest


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
        obj = models['t2'].query({'c1': 'test12'}).one()
        
        t1_t2_obj_cp = copy.deepcopy(t1_t2_obj)
        obj_exp = t1_t2_obj_cp.pop('t2')
        obj_exp['t1'] = [t1_t2_obj_cp]
        obj_exp['id'] = obj['id']
        obj_exp['t1'][0]['id'] = obj['t1'][0]['id']
        obj_exp['t1'][0]['c9'] = obj['t1'][0]['c9']
        obj_exp['t1'][0]['t1']['id'] = obj['t1'][0]['t1']['id']
        obj_exp['t1'][0]['t1']['c9'] = obj['t1'][0]['t1']['c9']
        obj_exp['t1'][0]['t1']['t2']['id'] = obj['t1'][0]['t1']['t2']['id']
        assert obj.todict() == obj_exp

    def test_iterator(self, models, t1_t2_obj):
        obj = models['t1'](**t1_t2_obj)
        obj.save()
        for attr in obj:
            assert obj.has_key(attr)
        obj.remove()

    def test_model_init_id(self, models, t1_simple_obj):
        with pytest.raises(Exception):
            t1_simple_obj['id'] = 1
            models['t1'](**t1_simple_obj)

    def test_model_one_level(self, models, one_level_obj):
        models['t1'].insert(one_level_obj)
        obj = models['t2'].query({'c1': 'test'}).one()

        obj_exp = "{'c1': 'test', 'id': %dL, 't1': " \
            "[{'c2': 1L, 'c9': 'test', 'c4': 'test1', 'c1': True, 'id': %dL}]}" % \
            (obj['id'], obj['t1'][0]['id'])
        assert repr(obj) == obj_exp