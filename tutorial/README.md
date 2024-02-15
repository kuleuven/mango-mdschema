# Metadata schemas in Python

This tutorial shows you
- The basic workflow with this package
- The contents and possibilities of the `Schema` class
- What the dictionary with metadata should look like
- What throws errors or warnings in validation

## Installation

You can install the package and it's dependencies with `pip`:

```python
pip install "git+https://github.com/kuleuven/mango-mdschema@1.0.1"
```

> The package will be published to [Pypi](https://pypi.org/) in the future.

## Basic workflow

In the most basic use case of the package:

- You create a `Schema` instance with the path to your JSON schema (which should
follow a specific format).
- You have a dictionary with name-value pairs for metadata, and you apply them
to one or more iRODS objects (data objects or collections).
- You have an iRODS object (data object or collection) and you extract the metadata
from it into a dictionary with all values converted into their Python representation.

In this tutorial we won’t show how to apply or extract them (see the README at
the top of the repository) but how to check that the metadata is compliant with
the schema, what requirements are checked and what the consequences of mismatches
are.

First we import what we need. The `Schema` class is the most important tool in
this package: it reads a schema from file, validates it and lets you validate,
apply or read metadata.

When calling the `apply()` method on the `Schema` object, it will call its
`validate()` method to do validation. You can use this method also on its own
to validate your dictionary of metadata against a schema.

```python
from pprint import pprint
from mango_mdschema import Schema, ValidationError, ConversionError
```

Create a schema by providing the path to the file. (In the future, `pathlib.Path`
objects will also be accepted). See below for more information about this class.

```python
my_schema = Schema('book-v2.0.0-published.json')
```

Provide the metadata as a dictionary with not-namespaced attribute names
and values (see below for specifications). If you have multiple values
for the same attribute name (i.e. in a repeatable field or a
multiple-value multiple-choice field), you should provide them as a list.

```python
my_metadata = {
    'title': "A book not written yet",
    'author': {
        'name': "Fulano De Tal",
        'email': "fulano.detal@kuleuven.be"
    },
    'ebook': 'Available',
    'publishing_date': '2015-02-01'
}
```

Validate the metadata against the schema:

```python
try:
    validated = my_schema.validate(my_metadata)
    print("My metadata is valid!")
    pprint(validated)
except (ConversionError, ValidationError) as err:
    print(f"Oops my metadata was not valid: {err}")
```

    My metadata is valid!
    {'author': [{'email': ['fulano.detal@kuleuven.be'], 'name': 'Fulano De Tal'}],
     'ebook': 'Available',
     'publisher': 'Tor',
     'publishing_date': [datetime.date(2015, 2, 1)],
     'title': 'A book not written yet'}

On success, the converted metadata dictionary is returned. On failure, a
`ConversionError` or `ValidationError` exception will be thrown.

You can also call the `to_avus` method on `Schema`, which will first validate
the provided metadata for you by calling `Schema.validate()`, and will then
generate a list of `irods.meta.iRODSMeta` objects with namespaced attribute names.

```python
my_schema.to_avus(my_metadata)
```

    [<iRODSMeta None mgs.book.title A book not written yet None>,
     <iRODSMeta None mgs.book.author.name Fulano De Tal 1>,
     <iRODSMeta None mgs.book.author.email fulano.detal@kuleuven.be 1>,
     <iRODSMeta None mgs.book.ebook Available None>,
     <iRODSMeta None mgs.book.publishing_date 2015-02-01 None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

You can assign these avus to a data object or collection
with atomic operations, but better is to use the `apply()` method
of `Schema`.

The `apply()` method uses `to_avus()` (and `validate()`) under the hood
to do validation and generation of AVUs, but before actually applying the
metadata to the given iRODS collection of data object, it will
check if there is already metadata linked to the schema, replace it and
update the metadata related to the schema version. This way the behavior is
consistent with that of the ManGO portal.

```python
my_schema.apply(my_object, my_metadata)
```

For all three methods (`apply()`, `to_avus()` and `validate()`) you can pass the
parameters `set_defaults=False` and/or `convert=False` to disable the the
first 2 steps of the validation: applying defaults and conversion.

With the method `extract()` you can do the reverse, i.e. read the iRODS AVUs
from a collection or data object, and convert the metadata to a dictionary with
all values converted to their type as defined by the schema fields.

```python
my_metadata = my_schema.extract(my_object)
```

The `extract()` method calls `to_avus()` to unflatten the AVUs to a
dictionary.

As shown below, passing the AVUs generated by `to_avus()` back into
`from_avus()`, will result in a dictionary identical to the one returned
by the `validate()` method.

```python
avus = my_schema.to_avus(my_metadata)
reconstructed = my_schema.from_avus(avus)
print("Validated meta data converted to AVUs:")
pprint(validated)
print("Reconstructed metadata:")
pprint(reconstructed)
```

    Validated meta data converted to AVUs:
    {'author': [{'email': ['fulano.detal@kuleuven.be'], 'name': 'Fulano De Tal'}],
     'ebook': 'Available',
     'publisher': 'Tor',
     'publishing_date': [datetime.date(2015, 2, 1)],
     'title': 'A book not written yet'}
    Reconstructed metadata:
    {'author': [{'email': ['fulano.detal@kuleuven.be'], 'name': 'Fulano De Tal'}],
     'ebook': 'Available',
     'publisher': 'Tor',
     'publishing_date': [datetime.date(2015, 2, 1)],
     'title': 'A book not written yet'}

## The `Schema` class

The `Schema` class represents a schema. As such, it has `name` and `version`
attributes, as well as the `prefix` used for all AVU names. The prefix is provided
in the constructor (by default 'mgs') and is used in the namespacing of all
metadata related to this schema. For example, initializing with
`Schema('book-v2.0.0-published.json', 'irods')` would prefix all metadata
names from this schema with 'irods.book'.

```python
print(f"Metadata annotated with the schema '{my_schema.name}' (current version: {my_schema.version}) carry the prefix '{my_schema.prefix}'.")
```

    Metadata annotated with the schema 'book' (current version: 2.0.0) carry the prefix 'mgs'.

When instantiating a `Schema`, some basic validation is performed. For example, only ‘published’ schemas are accepted.

```python
import json
with open('book-v3.0.0-draft.json', 'r', encoding="utf-8") as f:
    draft_schema = json.load(f)
    print(draft_schema['status'])
Schema('book-v3.0.0-draft.json')
```

    draft

    ValueError: The schema is not published: it cannot be used to apply metadata!

The code also checks that the fields make sense and have the necessary
fields in the right format.

```python
with open('bad-schema.json', 'r', encoding="utf-8") as f:
    bad_schema = json.load(f)
    pprint(bad_schema['properties'])
Schema('bad-schema.json')
```

    {'title': {'required': True, 'title': 'Book title', 'type': 'title'}}

    KeyError: 'Field type title is not supported.'

If you are not entirely familiar with your schema, you can check its
contents by printing it or listing its `required_fields` attribute. This
attribute is a dictionary with the names of the required fields as keys and
their default value, if available, as value. This is particularly
important because you will only get errors if a required field *without
default* is not provided or the value provided for it is wrong.

```python
print(my_schema)
```

    Book schema as an example
    Metadata annotated with the schema 'book' (2.0.0) carry the prefix 'mgs'.
    This schema contains the following 7 fields:
    - title, of type 'text' (required).
    - publishing_date, of type 'date' (required).
    - cover_colors, of type 'select'.
    - publisher, of type 'select' (required).
    - ebook, of type 'select'.
    - author, of type 'object' (required).
    - market_price, of type 'float'.

```python
my_schema.required_fields # note: 'author' is required because it contains required fields
```

    {'title': None, 'publishing_date': None, 'publisher': 'Tor', 'author': None}

A schema also has a method to check the requirements of a specific
field, namely whether they are required and have a default, whether they
are repeatable, and any other characteristic used in validation.

```python
my_schema.print_requirements('title')
```

    Type: text.
    Required: True. Default: None.
    Repeatable: False.

```python
my_schema.print_requirements('cover_colors')
```

    Type: select.
    Required: False.
    Repeatable: False.
    Choose at least one of the following values:
    - red
    - blue
    - green
    - yellow

When checking the requirements of a composite field, it also lists the requirements of its subfields.

```python
my_schema.print_requirements('author')
```

    Type: object.
    Required: True. (2 of its 3 fields are required.)
    Repeatable: True.
    
    Composed of the following fields:
    book.author.name
    Type: text.
    Required: True. Default: None.
    Repeatable: False.
    
    book.author.age
    Type: integer.
    Required: False.
    Repeatable: False.
    integer between 12 and 99.
    
    book.author.email
    Type: email.
    Required: True. Default: None.
    Repeatable: True.
    fully matching the following regex: ^[^@]+@kuleuven.be$.

Composite fields also have `required_fields` attributes and, like schemas, a `fields` attribute listing all the fields.

```python
my_schema.fields['author'].required_fields
```

    {'name': None, 'email': None}

## Metadata format

The `metadata` argument of `Schema.validate()`, `Schema.to_avus()` and `Schema.apply()`
(which calls `Schema.validate()` and `Schema.to_avus()` for you) must be a dictionary
in which the keys represent the names/IDs of the fields *without namespacing* and
the values, the value of the AVU to add.

If the field is a checkbox for which multiple values have been selected _or_ a
repeatable field with multiple values, then the value in the dictionary should be a
list of such values. For example, the code below includes metadata for a checkbox.
As you can see, this generates multiple AVUs with the same name and different values.

```python
my_metadata.update({'cover_colors' : ['red', 'blue']})
my_schema.to_avus(my_metadata)
```

    [<iRODSMeta None mgs.book.title A book not written yet None>,
     <iRODSMeta None mgs.book.author.name Fulano De Tal 1>,
     <iRODSMeta None mgs.book.author.email fulano.detal@kuleuven.be 1>,
     <iRODSMeta None mgs.book.ebook Available None>,
     <iRODSMeta None mgs.book.publishing_date 2015-02-01 None>,
     <iRODSMeta None mgs.book.cover_colors red None>,
     <iRODSMeta None mgs.book.cover_colors blue None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

For composite fields, the value should be a dictionary with the same format: keys are field names without namespacing and values, the right value. In this case, we are providing the following values for 'author', which is a composite field:

```python
{ 'name': 'Fulano De Tal', 'email': 'fulano.detal@kuleuven.be' }
```

This results in two AVUs with `mgs.book.author.name` and `mgs.book.author.email` as name, respectively, the corresponding values, and `1` as unit.
The goal of the unit is to keep AVUs within the same composite field together, particularly when the composite field is repeatable. For example, we could submit two authors by providing a list with two dictionaries.
As a result, we get two AVUs with `mgs.book.author.name` and two with `mgs.book.author.email`, and the unit indicates which email goes with each name.

```python
my_metadata['author']
```

    {'name': 'Fulano De Tal', 'email': 'fulano.detal@kuleuven.be'}

```python
my_metadata['author'] = [
    {'name': 'Fulano De Tal', 'email': 'fulano.detal@kuleuven.be'},
    {'name': 'Jane Doe', 'email': 'jane_doe@kuleuven.be'}
]
avus = my_schema.to_avus(my_metadata)
[x for x in avus if x.name.startswith('mgs.book.author')]
```

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 1>,
     <iRODSMeta None mgs.book.author.email fulano.detal@kuleuven.be 1>,
     <iRODSMeta None mgs.book.author.name Jane Doe 2>,
     <iRODSMeta None mgs.book.author.email jane_doe@kuleuven.be 2>]

Actually, the email of the author is also a repeatable field, so we could get more instances of `mgs.book.author.email`, always with the unit indicating who it belongs to.

```python
my_metadata['author'][1]['email'] = ['jane_doe@kuleuven.be', 'sweetdoe@kuleuven.be']
avus = my_schema.to_avus(my_metadata)
[x for x in avus if x.name.startswith('mgs.book.author')]
```

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 1>,
     <iRODSMeta None mgs.book.author.email fulano.detal@kuleuven.be 1>,
     <iRODSMeta None mgs.book.author.name Jane Doe 2>,
     <iRODSMeta None mgs.book.author.email jane_doe@kuleuven.be 2>,
     <iRODSMeta None mgs.book.author.email sweetdoe@kuleuven.be 2>]

## Verbose logging

To enable verbose logging for the `mango_mdschema` package, you can use the
[`logging`](https://docs.python.org/3/library/logging.html) module to increase
the logging level for the package:

```python
import logging
logger = logging.getLogger("mango_mdschema")
# logger.setLevel(logging.INFO)
```

## Metadata validation

The validation works in 3 steps:

1. Any missing or empty values will be set to their default value if defined
in the schema, for both required and non-required fields.

2. All values in the metadata dictionary (with added defaults) are converted
to their Python representation for validation (e.g. dates in string format are
converted to `datetime.date` objects).

3. The converted metadata (loaded withe defaults) is validated.

> **Warning**: Setting defaults in the ManGO portal works different than this
package. On the portal, a default value is only applied when a field is required.

If a required field is missing, and there is no default value, it will throw an error.

```python
my_schema.validate({'title': 'I only have a title'})
```

    ValidationError: Missing required fields in 'book': ['publishing_date', 'author']

If a required field is missing and there is a default value, you will only get
a warning if the log level is set to `INFO`; the default value is then used.

If a non-required field is missing, you will only get a warning if the log level
is set to `INFO`.

```python
logger.setLevel(logging.INFO)
my_schema.to_avus(my_metadata)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    [<iRODSMeta None mgs.book.title A book not written yet None>,
     <iRODSMeta None mgs.book.author.name Fulano De Tal 1>,
     <iRODSMeta None mgs.book.author.email fulano.detal@kuleuven.be 1>,
     <iRODSMeta None mgs.book.author.name Jane Doe 2>,
     <iRODSMeta None mgs.book.author.email jane_doe@kuleuven.be 2>,
     <iRODSMeta None mgs.book.author.email sweetdoe@kuleuven.be 2>,
     <iRODSMeta None mgs.book.ebook Available None>,
     <iRODSMeta None mgs.book.publishing_date 2015-02-01 None>,
     <iRODSMeta None mgs.book.cover_colors red None>,
     <iRODSMeta None mgs.book.cover_colors blue None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

If a field is provided that is not included in a schema, it will be ignored,
and you will only get warning if the log level is set to `INFO`.

```python
logger.setLevel(logging.INFO)
mini_md = {'title' : 'I only have a title', 'publishing_date' : '2023-04-28',
           'author' : {'name' : 'Name Surname', 'email' : 'rightemail@kuleuven.be'},
           'publishing_house' : 'Oxford'}
my_schema.to_avus(mini_md)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Following unknown fields in 'book' will be ignored: ['publishing_house'].
    INFO:mango_mdschema:Missing non-required fields in 'book': ['cover_colors', 'ebook', 'market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    [<iRODSMeta None mgs.book.title I only have a title None>,
     <iRODSMeta None mgs.book.publishing_date 2023-04-28 None>,
     <iRODSMeta None mgs.book.author.name Name Surname 1>,
     <iRODSMeta None mgs.book.author.email rightemail@kuleuven.be 1>,
     <iRODSMeta None mgs.book.publisher Tor None>]

```python
del mini_md['publishing_house']
```

Once the defaults has been set for fields with empty or missing value, and
the values have been converted to their proper Python representation,
the values are actually validated against the requirements of the fields.

The `validators` package is used to validate the range of numbers as well
as email and urls.

Any invalid data will always result in a `ValidationError` exception
during this validation step.

As mentioned above in section "Basic Workflow", for all three Schema
methods (`apply()`, `to_avus()` and `validate()`) you can use
`set_defaults=False` and/or `convert=False` to disable application of
defaults and/or conversion.

### Numbers

Integer and float simple fields must be of type `int` or `float` respectively, or
something that can be converted to such format.

Numeric fields can have a _minimum_ and _maximum_ property and during validation
it's checked that the number is within the provided range.

```python
my_metadata['author'][0]['age'] = 30
avus = my_schema.to_avus(my_metadata)
[x for x in avus if x.name.startswith('mgs.book.author') and x.units == '1']
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 1>,
     <iRODSMeta None mgs.book.author.email fulano.detal@kuleuven.be 1>,
     <iRODSMeta None mgs.book.author.age 30 1>]

```python
# provided as a string that can be converted with `int()`
my_metadata['author'][0]['age'] = '30'
avus = my_schema.to_avus(my_metadata)
[x for x in avus if x.name.startswith('mgs.book.author') and x.units == '1']
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 1>,
     <iRODSMeta None mgs.book.author.email fulano.detal@kuleuven.be 1>,
     <iRODSMeta None mgs.book.author.age 30 1>]

```python
# provided as a float that can be converted with `int()`
my_metadata['author'][0]['age'] = 30.5
avus = my_schema.to_avus(my_metadata)
[x for x in avus if x.name.startswith('mgs.book.author') and x.units == '1']
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 1>,
     <iRODSMeta None mgs.book.author.email fulano.detal@kuleuven.be 1>,
     <iRODSMeta None mgs.book.author.age 30 1>]

```python
# wrong range: it should be between 12 and 99
my_metadata['author'][0]['age'] = 103
avus = my_schema.to_avus(my_metadata)
[x for x in avus if x.name.startswith('mgs.book.author') and x.units == '1']
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']

    ValidationError: 'book.author.age' must be less than or equal to 99

```python
# wrong format
my_metadata['author'][0]['age'] = 'thirty'
avus = my_schema.to_avus(my_metadata)
[x for x in avus if x.name.startswith('mgs.book.author') and x.units == '1']
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'

    ValueError: invalid literal for int() with base 10: 'thirty'

    
    The above exception was the direct cause of the following exception:

    ConversionError: 'book.author.age' cannot be converted to type integer, got value: 'thirty'

Values are also checked if there are no minimum or maximum specified.

```python
mini_md['market_price'] = 9.99
avus = my_schema.to_avus(mini_md)
[x for x in avus if x.name.endswith('price')]
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['cover_colors', 'ebook']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    [<iRODSMeta None mgs.book.market_price 9.99 None>]

### Dates, times and datetimes
Dates, times and datetimes can be provided as `datetime.date`, `datetime.time` or `datetime.datetime` objects or as strings that can be converted as such via their `fromisoformat()` or `fromtimestamp()` methods. The final value is a string in ISO Format.

```python
from datetime import date
import time
```

```python
mini_md['publishing_date'] = date.today()
my_schema.to_avus(mini_md)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['cover_colors', 'ebook']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    [<iRODSMeta None mgs.book.title I only have a title None>,
     <iRODSMeta None mgs.book.publishing_date 2024-01-27 None>,
     <iRODSMeta None mgs.book.author.name Name Surname 1>,
     <iRODSMeta None mgs.book.author.email rightemail@kuleuven.be 1>,
     <iRODSMeta None mgs.book.market_price 9.99 None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

```python
mini_md['publishing_date'] = date.fromtimestamp(time.time())
my_schema.to_avus(mini_md)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['cover_colors', 'ebook']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    [<iRODSMeta None mgs.book.title I only have a title None>,
     <iRODSMeta None mgs.book.publishing_date 2024-01-27 None>,
     <iRODSMeta None mgs.book.author.name Name Surname 1>,
     <iRODSMeta None mgs.book.author.email rightemail@kuleuven.be 1>,
     <iRODSMeta None mgs.book.market_price 9.99 None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

```python
mini_md['publishing_date'] = '03/11/1990'
my_schema.validate(mini_md)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'

    ValueError: Invalid isoformat string: '03/11/1990'

    
    The above exception was the direct cause of the following exception:

    ConversionError: 'book.publishing_date' cannot be converted to date, got value: '03/11/1990'

### URLs and emails

In the example below, _one_ of the provided emails is wrong, which will throw
an error.

```python
my_metadata['author'][0]['age'] = 30
my_metadata['author'][1]['email'].append('bademail@whatevs')
my_schema.validate(my_metadata)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    ValidationError: 'book.author.email' does not match pattern '^[^@]+@kuleuven.be$', got value: 'bademail@whatevs'

```python
my_metadata['author'][1]['email'].pop()
```

    'bademail@whatevs'

### Regular expressions

URLs, emails and simple text can also have a `pattern` attribute providing a regular expression that checks its appropriateness. In the case of these emails, we have additional validation to make sure that the domain is "kuleuven.be":

```python
my_schema.print_requirements('author')
```

    Type: object.
    Required: True. (2 of its 3 fields are required.)
    Repeatable: True.
    
    Composed of the following fields:
    book.author.name
    Type: text.
    Required: True. Default: None.
    Repeatable: False.
    
    book.author.age
    Type: integer.
    Required: False.
    Repeatable: False.
    integer between 12 and 99.
    
    book.author.email
    Type: email.
    Required: True. Default: None.
    Repeatable: True.
    fully matching the following regex: ^[^@]+@kuleuven.be$.

```python
my_metadata['author'][0]['age'] = 30
my_metadata['author'][1]['email'].append('wrong_domain@gmail.com')
my_schema.to_avus(my_metadata)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    ValidationError: 'book.author.email' does not match pattern '^[^@]+@kuleuven.be$', got value: 'wrong_domain@gmail.com'

```python
my_metadata['author'][1]['email'].pop()
```

    'wrong_domain@gmail.com'

### Composite fields

Within composite fields, the same rules apply as for schemas. First, presence is checked: required
values without default throw an error when they are missing, while other cases of missing
or unknown fields will only write log messages (if log level set to `INFO`).

Moreover, composite fields are never required themselves based on the schema,
but they are required if any of their fields are required.

As shown above, bad values throw warnings in all cases.

```python
my_metadata['author'].append({'name' : 'etal'})
my_schema.validate(my_metadata)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']
    INFO:mango_mdschema:Missing required fields in 'book.author': ['email']

    ValidationError: Missing required fields in 'book.author': ['email']

```python
my_metadata['author'][2]['email'] = 'bademail.com'
my_schema.validate(my_metadata)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    ValidationError: 'book.author.email' does not match pattern '^[^@]+@kuleuven.be$', got value: 'bademail.com'

```python
my_metadata['author'][2]['email'] = 'bademail@kuleuven.be'
my_schema.validate(my_metadata)
```

    INFO:mango_mdschema:Applying default value to required field 'book.publisher': 'Tor'
    INFO:mango_mdschema:Missing non-required fields in 'book': ['market_price']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']
    INFO:mango_mdschema:Missing non-required fields in 'book.author': ['age']

    {'title': 'A book not written yet',
     'author': [{'name': 'Fulano De Tal',
       'email': ['fulano.detal@kuleuven.be'],
       'age': 30},
      {'name': 'Jane Doe',
       'email': ['jane_doe@kuleuven.be', 'sweetdoe@kuleuven.be']},
      {'name': 'etal', 'email': ['bademail@kuleuven.be']}],
     'ebook': 'Available',
     'publishing_date': [datetime.date(2015, 2, 1)],
     'cover_colors': ['red', 'blue'],
     'publisher': 'Tor'}

## Final notes on implementation

The metadata can be applied to an object or collection `item` with
`my_schema.apply(item, my_metadata)`, which basically calls `to_avus()`
on the schema and adds the generated list to `item.metadata.apply_atomic_operations()`,
adding each of the AVUs.

In addition, another AVU is added with name `{prefix}.__version__` (e.g. `mgs.book.__version__`)
indicating the version of the schema used for annotation (in this case, "2.0.0").

However, before actually adding the metadata, `apply()` does two things:

- It checks whether there already is a `{prefix}.__version__` AVU and prints a
warning if it's different from the version of the current schema.
- It removes all existing metadata with the same prefix.

This is the same behavior from the ManGO portal: it replaces all existing
metadata linked to a schema with the metadata provided in this instance.
