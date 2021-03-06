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


from sqlalchemy.orm.exc import DetachedInstanceError


class AlquimiaModel(object):
    def __init__(self, **kwargs):
        if 'id' in kwargs:
            raise Exception("Can't add objects with id!")
        for prop_name, prop in kwargs.iteritems():
            if isinstance(prop, dict):
                self[prop_name] = type(self)[prop_name].model(**prop)
            elif isinstance(prop, list):
                self[prop_name] = [type(self)[prop_name].model(**prop_) \
                                   if isinstance(prop_, dict) else prop_ for prop_ in prop]
            else:
                self[prop_name] = prop
        self._session.add(self)
        self._current_pos = 0

    def __setitem__(self, item, value):
        self._check_attr(item)
        setattr(self, item, value)

    def __getitem__(self, item):
        self._check_attr(item)
        try:
            return getattr(self, item)
        except DetachedInstanceError:
            self._session.add(self)
            return getattr(self, item)

    def __repr__(self):
        return repr(self.todict())

    def __iter__(self):
        return self

    def next(self):
        self._current_pos += 1
        if self._current_pos >= len(self.keys()):
            self._current_pos = 0
            raise StopIteration
        else:
            return self.keys()[self._current_pos - 1]

    def _check_attr(self, attr_name):
        if not attr_name in type(self):
            raise TypeError("'%s' is not a valid %s attribute!" %
                                              (attr_name, type(self).__name__))

    def todict(self, rec_stack=None):
        if rec_stack is None:
            rec_stack = []

        if self in rec_stack:
            return None

        dict_ = {}
        rec_stack.append(self)
        for prop_name, prop in self.items():
            if not prop_name.endswith('_id'):
                if isinstance(prop, list):
                    propl = []
                    for each in prop:
                        each = each.todict(rec_stack)
                        if each is not None:
                            propl.append(each)
                    prop = propl if propl else None
                
                elif isinstance(prop, AlquimiaModel):
                    prop = prop.todict(rec_stack)

                if prop is not None:
                    dict_[prop_name] = prop

        return dict_

    def has_key(self, key):
        self._check_attr(key)
        return hasattr(self, key)

    def keys(self):
        return type(self).keys()

    def items(self):
        return [(k, self[k]) for k in self.keys()]

    def remove(self):
        self._session.delete(self)
        self._session.commit()

    def save(self):
        self._session.commit()
