# Alquimia
An API to work with JSON schemas in SQLAlchemy

## Instalation
```
$ pip install alquimia 
```

## Usage example
```python
from alquimia import AlquimiaModels

models_dict = {
    'person': {
        'name': 'string',
        'age': 'integer',
        'relationships': ['address']
    },
    'address': {
        'street': 'string'
    }
}
models = AlquimiaModels('sqlite://', models_dict, create=True)

person = {
    'name': 'John',
    'age': 78,
    'address': {
        'street': "john's street"
    }
}
models['person'].insert(person)

qr =  models['address'].query({'street': "john's street"})
print qr
```
Output:
```
[{'street': u"john's street", 'id': 1}]
```

Detailed usage and documantion is in working process.