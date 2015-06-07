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
