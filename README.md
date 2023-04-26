# Apply metadata schemas in Python

Small application to apply metadata from a metadata schema using iRODS PRC.

## Requirements

- `python-irodsclient`
- `validators`

## Usage

```python
# authentication to iRODS
import os, os.path
from irods.session import iRODSSession
from schema import Schema # THIS MODULE

env_file = os.getenv('IRODS_ENVIRONMENT_FILE', os.path.expanduser('~/.irods/irods_environment.json'))

# load a schema from file
my_schema = Schema('/path/to/schema') # this also validates it as a schema
with iRODSSession(irods_env_file=env_file) as session:
    obj = session.data_objects.get('path/to/my/object')
    my_metadata = {
        'text' : 'Some text',
        'a_date' : '2023-04-26',
        'author' : {
            'name' : 'Mariana',
            'email' : 'mariana.montes@kuleuven.be'
        }
    }
    my_schema.apply(obj, my_metadata)
```

You can check the fields in a schema with:

```python
my_schema.fields
```

The list of required fields and default values is found as the `required_fields` attribute.
You can also check all the characteristics of a specific field such as 'name' with:

```python
my_schema.check_requirements('name') # same as print(my_schema.fields['name'])
```
