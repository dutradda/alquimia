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


import os
import sys
from setuptools import setup

if sys.version_info < (2, 7):
    raise Exception("Alquimia requires Python 2.7 or higher.")
elif sys.version_info >= (3, 0):
    raise Exception("Alquimia do not support Python 3")

setup(
    name='alquimia',
    version='0.5.0',
    author='Diogo Dutra',
    author_email='dutradda@gmail.com',
    description='An API to work with JSON schemas in SQLAlchemy',
    license='LGPLv3',
    keywords='json sqlachemy sql orm database',
    url='http://packages.python.org/alquimia',
    packages=['alquimia'],
    package_data={'alquimia': ['schemas/models.json']},
    requires=['sqlalchemy', 'jsonschema'],
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)'
    ]
)
