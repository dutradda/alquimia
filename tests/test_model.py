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


from tests.models_expected import todict_expected


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
