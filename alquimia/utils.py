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


def log(logger, level, message):
    levels = {
        'info': logger.info,
        'warning': logger.warning,
        'error': logger.error,
        'critical': logger.critical,
        'debug': logger.debug
    }
    levels[level]('alquimia:%s' % message)


def parse_filters(query_dict, obj, filters):
    for prop_name, prop in query_dict.iteritems():
        if isinstance(prop, dict):
            parse_filters(prop, obj[prop_name], filters)
        else:
            if hasattr(obj, 'model'):
                obj = obj.model
            filters.append(obj[prop_name] == prop)
    return filters
