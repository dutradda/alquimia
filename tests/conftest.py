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


import os
import pytest
import copy
from alquimia.models import AlquimiaModels
from sqlalchemy import MetaData


@pytest.fixture(scope='class')
def user_models():
    return {
        't1': {
            'c1': {'type': 'boolean', 'autoincrement': False},
            'c2': {'type': 'integer', 'autoincrement': False},
            'c3': 'float',
            'c4': 'string',
            'c5': 'text',
            'c6': {'type': 'boolean', 'nullable': True, 'autoincrement': False},
            'c7': {'type': 'integer', 'primary_key': False, 'autoincrement': False},
            'c8': 'float',
            'c9': {'type': 'string', 'default': 'test'},
            'c10': {'type': 'text'},
            'relationships': ['t1', {'t2': {'primary_key': True}}, {'t3': 'many-to-many'}]
        },
        't2': {
            'c1': 'string',
            'relationships': {'t6': 'many-to-many'}
        },
        't3': {'c1': {'type': 'string'}, 'relationships': {'t4': 'one-to-one'}},
        't4': {'relationships': ['t1', {'t3': 'one-to-one'}]},
        't5': {'relationships': {'t1': {'many-to-many': True}}},
        't6': {'relationships': [{'t1': 'many-to-many'}, {'t2': 'many-to-many'}]},
        't7': {
            'c7': 'string',
            'relationships': {'t1': 'one-to-one'}
        },
        't8': {
            'c8': 'string',
            'relationships': 't7'
        }
    }

@pytest.fixture
def user_models_oto_error():
    return {'t': {'relationships': {'t': 'many-to-many'}}}

@pytest.fixture
def user_models_amb_rels_error():
    return {'t': {'relationships': {'t2': 'many-to-many'}},
            't2': {'relationships':{'t': 'one-to-one'}}}

@pytest.fixture
def user_models_amb_rels_mto_error():
    return {'t': {'relationships': ['t2']},
            't2': {'relationships': ['t']}}

@pytest.fixture
def user_models_no_type_error():
    return {'t': {'c': {'primary_key': True}}}

@pytest.fixture
def user_models_col__id_error():
    return {'t': {'c_id': 'integer'}}

@pytest.fixture
def user_models_invalid_attribute_error():
    return {'t': {'c': 'test'}}

@pytest.fixture(scope='class')
def db_uri():
    return os.environ.get('ALQUIMIA_TEST_DB') or 'mysql://root:root@localhost:3600/alquimia_test'

def models_finalizer(models_):
    s = models_._session
    for model in models_.values():
        s.query(model).delete()
        s.commit()

@pytest.fixture(scope='class')
def models_create(request, user_models, db_uri):
    metadata = MetaData(db_uri)
    metadata.reflect()
    metadata.drop_all()
    models_ = AlquimiaModels(db_uri, user_models, create=True)
    request.addfinalizer(metadata.drop_all)
    return models_

@pytest.fixture
def models(request, user_models, models_create, db_uri):
    models_ = AlquimiaModels(db_uri, user_models)
    def fin():
        models_finalizer(models_)
    request.addfinalizer(fin)
    return models_

@pytest.fixture
def models_reflect(request, models_create, db_uri):
    models_ = AlquimiaModels(db_uri)
    def fin():
        models_finalizer(models_)
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
def t1_t2_query_like():
    return {
        'c4': 'testa%',
        't2': {
            'c1': 'test%'
        }
    }

@pytest.fixture
def t1_t2_query_or():
    return {
        '_or': [
            {
                'c4': 'test1',
                't2': {
                    'c1': 'test12'
                }
            },{
                'c4': 'test11'
            }
        ]
    }

@pytest.fixture
def t1_simple_obj():
    return {'c1': True, 'c2': 1L, 'c4': 'test1'}

@pytest.fixture
def t1_t3_obj(t1_simple_obj):
    obj = t1_simple_obj.copy()
    obj.update({'t2': {'c1': 'test12'}, 't3': [{'c1': 'test13'}]})
    return obj

@pytest.fixture
def t1_t2_obj(t1_simple_obj):
    obj = t1_simple_obj.copy()
    obj.update({'t2': {'c1': 'test12'}, 't1': {'c4': 'test11', 't2': {'c1': 'test123'}}})
    return obj

@pytest.fixture
def t7_obj():
    return {
        'c7': 'test17',
        't1_id': None
    }

@pytest.fixture
def t8_t7_t1_t2_obj(t1_simple_obj):
    t1 = t1_simple_obj.copy()
    t1['t2'] = {'c1': 'test12'}
    return {
        'c8': 'test18',
        't7': {
            'c7': 'test17',
            't1': t1
        }
    }

@pytest.fixture
def one_level_obj(t1_simple_obj):
    obj = t1_simple_obj.copy()
    obj['t2'] = {'c1': 'test'}
    return obj

@pytest.fixture
def t2_t1_t7_t8_query():
    return {
            't1': {
                't7': {
                   't8': {
                        'c8': 'test18'
                   }    
                }
            }
        }

@pytest.fixture
def t8_t7_t1_t2_query():
    return {
            't7': {
                't1': {
                    't2': {
                        'c1': 'test12'
                    }
                }
            }
        }

@pytest.fixture
def t1_t2_update():
    return {'c4': 'test_updated', 't2': {'c1': 'test_updated'}}

@pytest.fixture
def invalid_obj():
    return {'test': 'test', 'test2': {'test': 'test'}}