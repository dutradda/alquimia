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


import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

class Dict(dict):
    pass

def build_models_attributes():
    metadata = sqlalchemy.MetaData()
    t1_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id')
    models_attributes = Dict({
        't1': {
            '__table__': sqlalchemy.Table('t1', metadata, t1_id,
                sqlalchemy.Column(sqlalchemy.Boolean, name='c1', autoincrement=False),
                sqlalchemy.Column(sqlalchemy.Integer, name='c2', autoincrement=False),
                sqlalchemy.Column(sqlalchemy.Float, name='c3'),
                sqlalchemy.Column(sqlalchemy.String(255), name='c4'),
                sqlalchemy.Column(sqlalchemy.Text(), name='c5'),
                sqlalchemy.Column(sqlalchemy.Boolean, name='c6', nullable=True, autoincrement=False),
                sqlalchemy.Column(sqlalchemy.Integer, name='c7', primary_key=False, autoincrement=False),
                sqlalchemy.Column(sqlalchemy.Float, name='c8', primary_key=False),
                sqlalchemy.Column(sqlalchemy.String(255), name='c9', default='test'),
                sqlalchemy.Column(sqlalchemy.Text(), name='c10'),
                sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id',
                                                             onupdate='CASCADE',
                                                             ondelete='CASCADE'),
                                                                         name='t1_id', unique=True,
                                                                         autoincrement=False),
                sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('t2.id',
                                                             onupdate='CASCADE',
                                                             ondelete='CASCADE'),
                                                                         name='t2_id',
                                                                         autoincrement=False,
                                                                         primary_key=True)),
            't1': sqlalchemy.orm.relationship('t1', cascade='all,delete-orphan', remote_side=[t1_id], single_parent=True),
            't2': sqlalchemy.orm.relationship('t2', cascade='all',
                backref=sqlalchemy.orm.backref('t1', cascade='all,delete-orphan')),
            't3': sqlalchemy.orm.relationship('t3', cascade='all',
                backref=sqlalchemy.orm.backref('t1', cascade='all'),
                                                    secondary='t1_t3_association')
        },
        't2': {
            '__table__': sqlalchemy.Table('t2', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id'),
                sqlalchemy.Column(sqlalchemy.String, name='c1')),
            't6': sqlalchemy.orm.relationship('t6', secondary='t2_t6_association',
                                                             cascade='all',
                                                             backref=sqlalchemy.orm.backref('t2', cascade='all'))
        },
        't3': {
            '__table__': sqlalchemy.Table('t3', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id'),
                sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('t4.id',
                                                                 onupdate='CASCADE',
                                                                 ondelete='CASCADE'),
                                                                             name='t4_id', unique=True,
                                                                         autoincrement=False)),
            't4': sqlalchemy.orm.relationship('t4', cascade='all,delete-orphan', single_parent=True,
                        backref=sqlalchemy.orm.backref('t3', cascade='all,delete-orphan', single_parent=True))
        },
        't4': {
            '__table__': sqlalchemy.Table('t4', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id'),
                sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id',
                                                                 onupdate='CASCADE',
                                                                 ondelete='CASCADE'),
                                                                             name='t1_id',
                                                                         autoincrement=False)),
            't1': sqlalchemy.orm.relationship('t1', cascade='all',
                        backref=sqlalchemy.orm.backref('t4', cascade='all,delete-orphan'))
        },
        't5': {
            '__table__': sqlalchemy.Table('t5', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id')),
            't1': sqlalchemy.orm.relationship('t1', cascade='all',
                    backref=sqlalchemy.orm.backref('t5', cascade='all'),
                                                         secondary='t5_t1_association')
        },
        't6': {
            '__table__': sqlalchemy.Table('t6', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id')),
            't1': sqlalchemy.orm.relationship('t1', secondary='t6_t1_association',
                                                            cascade='all',
                                                             backref=sqlalchemy.orm.backref('t6', cascade='all'))   
        },
        't7': {
            '__table__': sqlalchemy.Table('t7', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id'),
                sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id',
                                                                 onupdate='CASCADE',
                                                                 ondelete='CASCADE'),
                                                                             name='t1_id', unique=True,
                                                                         autoincrement=False)),
            't1': sqlalchemy.orm.relationship('t1', cascade='all,delete-orphan', single_parent=True,
                        backref=sqlalchemy.orm.backref('t7', cascade='all,delete-orphan', single_parent=True))
        },
        't8': {
            '__table__': sqlalchemy.Table('t8', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id'),
                sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('t7.id',
                                                                 onupdate='CASCADE',
                                                                 ondelete='CASCADE'),
                                                                             name='t7_id',
                                                                         autoincrement=False)),
            't7': sqlalchemy.orm.relationship('t7', cascade='all',
                        backref=sqlalchemy.orm.backref('t8', cascade='all,delete-orphan'))
        }
    })

    sqlalchemy.Table('t2_t6_association', metadata,
    sqlalchemy.Column('t6_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t6.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, autoincrement=False),
    sqlalchemy.Column('t2_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t2.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, autoincrement=False))

    sqlalchemy.Table('t6_t1_association', metadata,
    sqlalchemy.Column('t6_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t6.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, autoincrement=False),
    sqlalchemy.Column('t1_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, autoincrement=False))

    sqlalchemy.Table('t5_t1_association', metadata,
    sqlalchemy.Column('t5_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t5.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, autoincrement=False),
    sqlalchemy.Column('t1_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, autoincrement=False))

    sqlalchemy.Table('t1_t3_association', metadata,
    sqlalchemy.Column('t1_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, autoincrement=False),
    sqlalchemy.Column('t3_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t3.id', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, autoincrement=False))

    models_attributes.metadata = metadata
    return models_attributes

def build_models():
    models_attributes = build_models_attributes()

    metadata = models_attributes.metadata

    base = declarative_base(metadata=metadata)
    
    models = models_attributes.copy()
    for model_name, table in models.iteritems():
        model = type(model_name, (base,), table)
        models[model_name] = model
    
    for model in models.values():
        model.__mapper__.relationships

    models = Dict(models)
    models.metadata = metadata
    return models

models_expected = build_models()

rels_expected = {
    't1': {
        'relationships': ['t1', 't2', 't3', 't4', 't5', 't6', 't7'],
        'oto': ['t1', 't7'],
        'mto': ['t2'],
        'otm': ['t4'],
        'mtm': ['t3', 't5', 't6']
    },
    't2': {
        'relationships': ['t1', 't6'],
        'oto': [],
        'mto': [],
        'otm': ['t1'],
        'mtm': ['t6']
    },
    't3': {
        'relationships': ['t1', 't4'],
        'oto': ['t4'],
        'mto': [],
        'otm': [],
        'mtm': ['t1']
    },
    't4': {
        'relationships': ['t1', 't3'],
        'oto': ['t3'],
        'mto': ['t1'],
        'otm': [],
        'mtm': []
    },
    't5': {
        'relationships': ['t1'],
        'oto': [],
        'mto': [],
        'otm': [],
        'mtm': ['t1']
    },
    't6': {
        'relationships': ['t1', 't2'],
        'oto': [],
        'mto': [],
        'otm': [],
        'mtm': ['t1', 't2']
    },
    't7': {
        'relationships': ['t1', 't8'],
        'oto': ['t1'],
        'mto': [],
        'otm': ['t8'],
        'mtm': []
    },
    't8': {
        'relationships': ['t7'],
        'oto': [],
        'mto': ['t7'],
        'otm': [],
        'mtm': []
    }
}