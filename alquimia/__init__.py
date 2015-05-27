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


import os.path
import sqlalchemy
import json

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

SCHEMAS_DIR = os.path.join(ROOT_DIR, 'schemas')

MODELS_SCHEMA_FILE = os.path.join(SCHEMAS_DIR, 'models.json')

SCHEMA = json.loads(open(MODELS_SCHEMA_FILE).read())

DATA_TYPES = {
    'integer': sqlalchemy.Integer,
    'string': sqlalchemy.String(255),
    'float': sqlalchemy.Float,
    'text': sqlalchemy.Text(),
    'boolean': sqlalchemy.Boolean
}

from alquimia.models import AlquimiaModels
