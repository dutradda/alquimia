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
import sqlalchemy
from tests.models_expected import models_expected, rels_expected
from alquimia import AlquimiaModels
from alquimia.models_attrs import AmbiguousRelationshipsError
from alquimia.models_attrs_reflect import OneToOneManyToManyError
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

    def _check_column(self, column1, column2, test_fk=True):
        assert column1.name == column2.name
        c1_type = column1.type.python_type
        c2_type = column2.type.python_type
        if not ((c1_type == int and c2_type == bool) or \
                                         (c2_type == int and c1_type == bool)):
            assert column1.type.python_type == column2.type.python_type
        assert column1.primary_key == column2.primary_key
        assert column1.nullable == column2.nullable
        assert bool(column1.autoincrement) == bool(column2.autoincrement)
        if not hasattr(self, 'is_reflect'):
            # sqlalchemy dont reflect unique
            assert column1.unique == column2.unique
            # sqlalchemy dont saves default in db
            if isinstance(column1.default, sqlalchemy.schema.ColumnDefault):
                assert column1.default.arg == column2.default.arg
        if test_fk:
            self._check_foreign_key(column1.foreign_keys, column2.foreign_keys)

    def _check_tables(self, tables, tables_exp):
        for tbl, tbl_exp in zip(tables, tables_exp):
            for col_name, col in tbl.columns.items():
                col_exp = tbl_exp.columns[col_name]
                self._check_column(col, col_exp)

    def _sort_remote_side(self, remote_side):
        drs = {str(col.name): col for col in list(remote_side)}
        skeys = list(drs.keys())
        skeys.sort()
        return [drs[k] for k in skeys]

    def _check_relationship(self, rel1, rel2):
        rel1.table.name == rel2.table.name
        assert rel1.lazy == rel2.lazy
        assert rel1.innerjoin == rel2.innerjoin
        assert rel1.order_by == rel2.order_by
        if not hasattr(self, 'is_reflect'):
            assert len(rel1.remote_side) == len(rel2.remote_side)
            rs1 = self._sort_remote_side(rel1.remote_side)
            rs2 = self._sort_remote_side(rel2.remote_side)
            for c1, c2 in zip(rs1, rs2):
                self._check_column(c1, c2)
            assert rel1.cascade == rel2.cascade
        if rel1.secondary is not None and rel2.secondary is not None:
            self._check_tables([rel1.secondary], [rel2.secondary])

    def _check_models(self, models):
        tables_dict = models.metadata.tables
        tables_exp_dict = models_expected.metadata.tables
        assert len(tables_dict) == len(tables_exp_dict)
        tables = []
        tables_exp = []
        for k in tables_dict.keys():
            tables.append(tables_dict[k])
            tables_exp.append(tables_exp_dict[k])
        self._check_tables(tables, tables_exp)

        for model_name, model in models.iteritems():
            rels = model.__mapper__.relationships
            rels_exp = models_expected[model_name].__mapper__.relationships
            assert len(rels) == len(rels_exp) == len(model.relationships)
            for rel_name in model.relationships:
                rel_exp = getattr(models_expected[model_name], rel_name).prop
                self._check_relationship(model[rel_name].prop, rel_exp)

    def test_create(self, models_create, caplog):
        self._check_models(models_create)
        logs = caplog.records()
        assert len(logs) == 2
        assert logs[0].name == logs[1].name == 'root'
        assert logs[0].levelname == logs[1].levelname == 'WARNING'
        assert logs[0].msg == 'alquimia:Removed relationship t6.t2 duplicated from t2.t6'
        assert logs[1].msg == 'alquimia:Removed relationship t4.t3 duplicated from t3.t4'

    def test_rels_list(self, models_create):
        assert len(models_create) == len(rels_expected)
        for mdl_name, mdl in models_create.items():
            for rel_type, rels in rels_expected[mdl_name].iteritems():
                sr1 = list(getattr(mdl, rel_type))
                sr2 = list(rels)
                sr1.sort()
                sr2.sort()
                assert sr1 == sr2

    def test_models(self, models):
        self._check_models(models)
    
    def test_models_reflect(self, models_reflect):
        self.is_reflect = True
        self._check_models(models_reflect)
        del self.is_reflect

    def test_models_clean(self, models, t1_t2_obj):
        t1 = models['t1'].insert(t1_t2_obj)
        models.clean()
        t1['t2']
        
    def test_models_oto_mtm_error(self, user_models_oto_error, db_uri):
        with pytest.raises(OneToOneManyToManyError):
            AlquimiaModels(db_uri, user_models_oto_error)

    def test_models_amb_rels_error(self, user_models_amb_rels_error, db_uri):
        with pytest.raises(AmbiguousRelationshipsError):
            AlquimiaModels(db_uri, user_models_amb_rels_error)

    def test_models_amb_rels_mto_error(self, user_models_amb_rels_mto_error, db_uri):
        with pytest.raises(AmbiguousRelationshipsError):
            AlquimiaModels(db_uri, user_models_amb_rels_mto_error)

    def test_models_col__id_error(self, user_models_col__id_error, db_uri):
        with pytest.raises(ValidationError):
            AlquimiaModels(db_uri, user_models_col__id_error)

    def test_models_no_type_error(self, user_models_no_type_error, db_uri):
        with pytest.raises(ValidationError):
            AlquimiaModels(db_uri, user_models_no_type_error)

    def test_models_invalid_attribute_error(self, user_models_invalid_attribute_error, db_uri):
        with pytest.raises(ValidationError):
            AlquimiaModels(db_uri, user_models_invalid_attribute_error)
