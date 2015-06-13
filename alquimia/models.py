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


import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.orm import ColumnProperty
from alquimia.model import AlquimiaModel
from alquimia.modelmeta import AlquimiaModelMeta
from alquimia.models_attrs import ModelsAttributes
from alquimia.models_attrs_reflect import ModelsAtrrsReflect
from alquimia import DATA_TYPES


class AlquimiaSession(object):
    def __init__(self, engine):
        self._session_class = sessionmaker(engine)
        self._session = self._session_class()

    def delete(self, *args, **kwargs):
        return self._session.delete(*args, **kwargs)

    def query(self, *args, **kwargs):
        return self._session.query(*args, **kwargs)

    def commit(self, *args, **kwargs):
        return self._session.commit(*args, **kwargs)

    def rollback(self, *args, **kwargs):
        return self._session.rollback(*args, **kwargs)

    def add(self, *args, **kwargs):
        return self._session.add(*args, **kwargs)

    def clean(self):
        self._session.close()
        self._session = self._session_class()


class AlquimiaModels(dict):
    def __init__(self, db_url, dict_=None, data_types=DATA_TYPES,
                                    engine=None, create=False, logger=logging):
        if not engine:
            engine = create_engine(db_url)
        base_model = declarative_base(engine, metaclass=AlquimiaModelMeta,
                         cls=AlquimiaModel, constructor=AlquimiaModel.__init__)
        self._session = AlquimiaSession(engine)
        self.metadata = base_model.metadata
        if dict_ is not None:
            attrs = ModelsAttributes(dict_, self.metadata, data_types, logger)
        else:
            attrs = ModelsAtrrsReflect(self.metadata, logger)
        self._build(base_model, attrs)
        if create:
            self.metadata.create_all()

    def _build(self, base_model, models_attrs):
        models = {}
        for model_name, attrs in models_attrs.iteritems():
            attrs.update({'_session': self._session})
            model = type(model_name, (base_model,), attrs)
            models[model_name] = model

        for model in models.values():
            model.__mapper__.relationships
            for attr_name, attr in model.iteritems():
                if isinstance(attr.prop, RelationshipProperty):
                    setattr(attr, 'model', models[attr_name])
                elif isinstance(attr.prop, ColumnProperty):
                    model.columns.append(attr_name)

        self.update(models)

    def clean(self):
        self._session.clean()
