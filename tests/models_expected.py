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
                sqlalchemy.Column(sqlalchemy.Boolean, name='c1'),
                sqlalchemy.Column(sqlalchemy.Integer, name='c2'),
                sqlalchemy.Column(sqlalchemy.Float, name='c3'),
                sqlalchemy.Column(sqlalchemy.String(255), name='c4'),
                sqlalchemy.Column(sqlalchemy.Text(), name='c5'),
                sqlalchemy.Column(sqlalchemy.Boolean, name='c6', nullable=True),
                sqlalchemy.Column(sqlalchemy.Integer, name='c7', primary_key=False),
                sqlalchemy.Column(sqlalchemy.Float, name='c8', primary_key=False,
                                                                  autoincrement=False),
                sqlalchemy.Column(sqlalchemy.String(255), name='c9', default='test'),
                sqlalchemy.Column(sqlalchemy.Text(), name='c10'),
                sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id',
                                                             onupdate='CASCADE',
                                                             ondelete='CASCADE'),
                                                                         name='t1_id'),
                sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('t2.id',
                                                             onupdate='CASCADE',
                                                             ondelete='CASCADE'),
                                                                         name='t2_id',
                                                                         primary_key=False)),
            't1': sqlalchemy.orm.relationship('t1', cascade='all', remote_side=[t1_id]),
            't2': sqlalchemy.orm.relationship('t2', cascade='all',
                backref=sqlalchemy.orm.backref('t1', cascade='all,delete-orphan')),
            't3': sqlalchemy.orm.relationship('t3', cascade='all',
                backref=sqlalchemy.orm.backref('t1', cascade='all'),
                                                    secondary='t1_t3_association')
        },
        't2': {
            '__table__': sqlalchemy.Table('t2', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id'),
                sqlalchemy.Column(sqlalchemy.String, name='c1'))
        },
        't3': {
            '__table__': sqlalchemy.Table('t3', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id'))
        },
        't4': {
            '__table__': sqlalchemy.Table('t4', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id'),
                sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id',
                                                                 onupdate='CASCADE',
                                                                 ondelete='CASCADE'),
                                                                             name='t1_id')),
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
                                                             backref=sqlalchemy.orm.backref('t6', cascade='all')),
            't2': sqlalchemy.orm.relationship('t2', secondary='t6_t2_association',
                                                             cascade='all',
                                                             backref=sqlalchemy.orm.backref('t6', cascade='all'))
        },
        't7': {
            '__table__': sqlalchemy.Table('t7', metadata,
                sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, name='id'))
        }
    })

    sqlalchemy.Table('t6_t2_association', metadata,
    sqlalchemy.Column('t6_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t6.id', onupdate='CASCADE', ondelete='CASCADE')),
    sqlalchemy.Column('t2_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t2.id', onupdate='CASCADE', ondelete='CASCADE')))

    sqlalchemy.Table('t6_t1_association', metadata,
    sqlalchemy.Column('t6_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t6.id', onupdate='CASCADE', ondelete='CASCADE')),
    sqlalchemy.Column('t1_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id', onupdate='CASCADE', ondelete='CASCADE')))

    sqlalchemy.Table('t5_t1_association', metadata,
    sqlalchemy.Column('t5_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t5.id', onupdate='CASCADE', ondelete='CASCADE')),
    sqlalchemy.Column('t1_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id', onupdate='CASCADE', ondelete='CASCADE')))

    sqlalchemy.Table('t1_t3_association', metadata,
    sqlalchemy.Column('t1_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t1.id', onupdate='CASCADE', ondelete='CASCADE')),
    sqlalchemy.Column('t3_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('t3.id', onupdate='CASCADE', ondelete='CASCADE')))

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

attributes_expected = build_models_attributes()
