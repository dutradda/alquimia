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
from alquimia.models import ModelsAttributes, AlquimiaModels
from sqlalchemy.testing.engines import mock_engine
from sqlalchemy import MetaData, create_engine

@pytest.fixture()
def user_models():
    return {
    't1': {
        'c1': 'boolean',
        'c2': 'integer',
        'c3': 'float',
        'c4': 'string',
        'c5': 'text',
        'c6': {'type': 'boolean', 'nullable': True},
        'c7': {'type': 'integer', 'primary_key': False},
        'c8': {'type': 'float', 'primary_key': False, 'autoincrement': False},
        'c9': {'type': 'string', 'default': 'test'},
        'c10': {'type': 'text'},
        'relationships': ['t1', {'t2': {'primary_key': False}}, {'t3': 'many-to-many'}]
    },
    't2': {'c1': 'string'},
    't3': {},
    't4': {'relationships': ['t1']},
    't5': {'relationships': {'t1': {'many-to-many': True}}},
    't6': {'relationships': [{'t1': 'many-to-many'}, {'t2': 'many-to-many'}]},
    't7': {}
    }

@pytest.fixture
def models_attributes(user_models):
    return ModelsAttributes(user_models, MetaData())

@pytest.fixture
def models(request, user_models):
    models_ = AlquimiaModels('mysql://root:root@localhost:3600/alquimia_test', user_models, create=True)
    def fin():
        for model in models_.values():
            s = model.session()
            s.query(model).delete()
            s.commit()
            s.close()
    request.addfinalizer(fin)
    return models_

@pytest.fixture
def t1_t2_query():
    return {
        'c4': 'test1',
        't2': {
            'c1': 'test12'
        }
    }

@pytest.fixture
def t1_simple_obj():
    return {'c1': True, 'c2': 1, 'c4': 'test1'}

@pytest.fixture
def t1_t2_obj(t1_simple_obj):
    obj = t1_simple_obj.copy()
    obj.update({'t2': {'c1': 'test12'}, 't1': {'c4': 'test11'}})
    return obj

@pytest.fixture
def t1_t2_update():
    return {'c4': 'test_updated', 't2': {'c1': 'test_updated'}}