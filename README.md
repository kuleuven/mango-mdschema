# Apply ManGO metadata schemas in Python

Small application to apply metadata from a metadata schema using iRODS PRC.

## Requirements

- `python-irodsclient`
- `validators`

## Installation

You can install the package and it's dependencies with `pip`:

```
pip install "git+https://github.com/kuleuven/mango-mdschema@1.0.0"
```

> The package will be published to [Pypi](https://pypi.org/) in the near future.

## Usage

```python
# authentication to iRODS
import os, os.path
from irods.session import iRODSSession
from mango_mdschema import Schema

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

The `apply` function will first validate the provided metadata dictionary
before applying it on the iRODS object. See the [tutorial](tutorial/) for
more details.

To only validate your metadata, without applying it, you can use the `validate`

function of the schema.

```python
try:
    validated = my_schema.validate(metadata)
except (ConversionError, ValidationError) as err:
    print("Oops my metadata was not valid: {err}")
```

You can check the fields in a schema with:

```python
print(my_schema)
```

The list of required fields and default values is found as the `required_fields` attribute.
You can also check all the characteristics of a specific field such as 'name' with:

```python
my_schema.print_requirements('name') # same as print(my_schema.fields['name'])
```

You can test the list of AVUs that would be sent by providing a given
metadata dictonary like so:

```python
avus = my_schema.to_avus(metadata)
```

The schema class can also read the metadata from ManGO and return it as
nested dictionary with all values converted to their Python representation (
i.e. integer fields result in `int` values, datetime fields in `datetime`
objects, etc.).

```python
with iRODSSession(irods_env_file=env_file) as session:
    obj = session.data_objects.get('path/to/my/object')
    my_metadata = my_schema.extract(obj)
```

Check the [tutorial](tutorial/README.ipynb) notebook for more details.
