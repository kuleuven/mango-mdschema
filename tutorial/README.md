Metadata schemas in Python
================

This tutorial shows you - The basic workflow with this package - The
contents and possibilities of the `Schema` class - What the dictionary
with metadata should look like - What throws errors or warnings in
validation

# Basic workflow

In the most basic use case of the package, you create a `Schema`
instance with the path to your JSON schema (which should follow a
specific format), you have a dictionary with name-value pairs for
metadata, and you apply them to one or more iRODS objects (data objects
or collections).

In this tutorial we won’t show how to apply them (see the README at the
top of the repository) but how to check that the metadata is compatible
with the schema, what requirements are checked and what the consequences
of mismatches are.

First we import what we need. The `Schema` class is the most important
tool in this package: it reads a schema from file, validates it and lets
you validate and apply metadata. `check_metadata()` is a function called
by the `apply()` method of a `Schema` but you can use it to validate a
dictionary of metadata against a schema.

``` python
from mango_mdschema import Schema, check_metadata
```

Create a schema by providing the path to the file. (In the future,
`pathlib.Path` objects will also be accepted). See below for more
information about this class.

``` python
my_schema = Schema('book-v2.0.0-published.json')
```

Provide the metadata as a dictionary with not-namespaced attribute names
and values (see below for specifications).

``` python
my_metadata = {
    'title' : "A book not written yet",
    'author' : {
        'name' : "Fulano De Tal",
        'email' : "fulano.detal@domain.info"
    },
    'ebook' : 'Available',
    'publishing_date' : '2015-02-01'
}
```

Validate the metadata against the schema with `check_metadata()`. The
`verbose` argument also prints warnings when non required fields or
required fields with default values are not provided. The output of this
function is a list of `irods.meta.iRODSMeta` objects with namespaced
attribute names.

You can now assign them to a data object or collection with atomic
operations, or let this package do it by running
`my_schema.apply(my_object, my_metadata)` instead. This also checks if
there is already metadata linked to the schema and replaces it.

``` python
check_metadata(my_schema, my_metadata)
```

    [<iRODSMeta None mgs.book.title A book not written yet None>,
     <iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>,
     <iRODSMeta None mgs.book.ebook Available None>,
     <iRODSMeta None mgs.book.publishing_date 2015-02-01 None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

## The `Schema` class

The `Schema` class represents a schema. As such, it has `name` and
`version` attributes, as well as the `prefix` used for all AVU names.
The prefix is the combination of a prefix given in the constructor (by
default ‘mgs’) and the name of the schema. For example, initializing
with `Schema('book-v2.0.0-published.json', 'irods')` would generate the
prefix ‘irods.book’ for all the metadata related to this schema.

``` python
f"Metadata annotated with the schema '{my_schema.name}' (current version: {my_schema.version}) carry the prefix '{my_schema.prefix}'."
```

    "Metadata annotated with the schema 'book' (current version: 2.0.0) carry the prefix 'mgs.book'."

When instantiating a `Schema`, some basic validation is performed. For
example, only ‘published’ schemas are accepted.

``` python
import json
with open('book-v3.0.0-draft.json', 'r') as f:
    draft_schema = json.load(f)
    print(draft_schema['status'])
Schema('book-v3.0.0-draft.json')
```

    draft

    ValueError: The schema is not published: it cannot be used to apply metadata!

The code also checks that the fields make sense and have the necessary
fields in the right format.

``` python
with open('bad-schema.json', 'r') as f:
    bad_schema = json.load(f)
    print(bad_schema['properties'])
Schema('bad-schema.json')
```

    {'title': {'title': 'Book title', 'type': 'title', 'required': True}}

    ValueError: The type of the 'title' field is not valid.

If you are not entirely familiar with your schema, you can check its
contents with the `fields` and `required_fields` attributes. The former
is a dictionary of fields; the latter as well, but only listing the
required fields and providing their default values. This is particularly
important because you will only get errors if a required field *without
default* is not provided or the value provided for it is wrong. For
required fields with defaults and non-required fields, wrong or missing
values will simply be ignored.

``` python
my_schema.fields
```

    {'title': <mango_mdschema.fields.SimpleField at 0x7f1e1de9d0c0>,
     'publishing_date': <mango_mdschema.fields.SimpleField at 0x7f1e1de6ffa0>,
     'cover_colors': <mango_mdschema.fields.MultipleField at 0x7f1e1c64c6d0>,
     'publisher': <mango_mdschema.fields.MultipleField at 0x7f1e1c64c760>,
     'ebook': <mango_mdschema.fields.MultipleField at 0x7f1e1c64c7c0>,
     'author': <mango_mdschema.fields.CompositeField at 0x7f1e1c64c820>}

``` python
my_schema.required_fields # note: 'author' is required because it contains required fields
```

    {'title': None, 'publishing_date': None, 'publisher': 'Tor', 'author': None}

A schema also has a method to check the requirements of a specific
field, namely whether they are required and have a default, whether they
are repeatable, and any other characteristic used in validation.

``` python
my_schema.check_requirements('title')
```

    Type: text.
                    Required: True. Default: None.
                    Repeatable: False.
                    

``` python
my_schema.check_requirements('cover_colors')
```

    Type: select.
                    Required: False.
                    Repeatable: False.
                    
    Choose at least one of the following values:
    - red
    - blue
    - green
    - yellow

When checking the requirements of a composite field, it also lists the
requirements of its subfields.

``` python
my_schema.check_requirements('author')
```

    Type: object.
                    Required: True. Default: None.
                    Repeatable: True.
                    
    Composed of the following fields:
    - Type: text.
                    Required: True. Default: None.
                    Repeatable: False.
                    

    - Type: integer.
                    Required: False.
                    Repeatable: False.
                    
    integer between 12 and 99.
    - Type: email.
                    Required: True. Default: None.
                    Repeatable: True.
                    

Composite fields also have `fields` and `required_fields` attributes.

``` python
my_schema.fields['author'].required_fields
```

    {'name': None, 'email': None}

## Metadata format

The `metadata` argument of `check_metadata()` and `Schema.apply()`
(which calls `check_metadata()`) must be a dictionary in which the keys
represent the names/IDs of the fields *without namespacing* and the
values, the value of the AVU to add.

If the field is a checkbox for which multiple values have been selected
*or* a repeatable field with multiple values, then the value in the
dictionary should be a list of such values. For example, the code below
includes metadata for a checkbox. As you can see, this generates
multiple AVUs with the same name and different values.

``` python
my_metadata.update({'cover_colors' : ['red', 'blue']})
check_metadata(my_schema, my_metadata)
```

    [<iRODSMeta None mgs.book.title A book not written yet None>,
     <iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>,
     <iRODSMeta None mgs.book.ebook Available None>,
     <iRODSMeta None mgs.book.publishing_date 2015-02-01 None>,
     <iRODSMeta None mgs.book.cover_colors red None>,
     <iRODSMeta None mgs.book.cover_colors blue None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

For composite fields, the value should be a dictionary with the same
format: keys are field names without namespacing and values, the right
value. In this case, we are providing the following values for ‘author’,
which is a composite field:

``` python
{ 'name' : 'Fulano De Tal', 'email' : 'fulano.detal@domain.info' }
```

This results in two AVUs with `mgs.book.author.name` and
`mgs.book.author.email` as name, respectively, the corresponding values,
and `0` as unit. The goal of the unit is to keep AVUs within the same
composite field together, particularly when the composite field is
repeatable. For example, we could submit two authors by providing a list
with two dictionaries. As a result, we get two AVUs with
`mgs.book.author.name` and two with `mgs.book.author.email`, and the
unit indicates which email goes with each name.

``` python
my_metadata['author']
```

    {'name': 'Fulano De Tal', 'email': 'fulano.detal@domain.info'}

``` python
my_metadata['author'] = [
    {'name': 'Fulano De Tal', 'email': 'fulano.detal@domain.info'},
    {'name': 'Jane Doe', 'email': 'jane_doe@email.com'}
]
checked_metadata = check_metadata(my_schema, my_metadata)
[x for x in checked_metadata if x.name.startswith('mgs.book.author')]
```

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>,
     <iRODSMeta None mgs.book.author.name Jane Doe 1>,
     <iRODSMeta None mgs.book.author.email jane_doe@email.com 1>]

Actually, the email of the author is also a repeatable field, so we
could get more instances of `mgs.book.author.email`, always with the
unit indicating who it belongs to.

``` python
my_metadata['author'][1]['email'] = ['jane_doe@email.com', 'sweetdoe@bambi.be']
checked_metadata = check_metadata(my_schema, my_metadata)
[x for x in checked_metadata if x.name.startswith('mgs.book.author')]
```

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>,
     <iRODSMeta None mgs.book.author.name Jane Doe 1>,
     <iRODSMeta None mgs.book.author.email jane_doe@email.com 1>,
     <iRODSMeta None mgs.book.author.email sweetdoe@bambi.be 1>]

## Metadata validation

There are two levels of validation for metadata: presence and
appropriateness. They are applied both at the level of the schema and on
each composite field.

- If a required field is missing, and there is no default value, it will
  throw an error.

``` python
check_metadata(my_schema, {'title' : 'I only have a title'})
```

    KeyError: 'The following required fields are missing and there is no default: mgs.book.publishing_date, mgs.book.author.'

- If a required field is missing and there is a default value, you will
  only get a warning if `verbose` is `True`; the default value is then
  used.
- If a non-required field is missing, you will only get a warning if
  `verbose` is `True`.

``` python
check_metadata(my_schema, my_metadata, verbose = True)
```

    WARNING:root:The following required fields are missing and the default value will be used: mgs.book.publisher (Tor)
    WARNING:root:The following non required fields are missing: mgs.book.author.age.
    WARNING:root:The following non required fields are missing: mgs.book.author.age.

    [<iRODSMeta None mgs.book.title A book not written yet None>,
     <iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>,
     <iRODSMeta None mgs.book.author.name Jane Doe 1>,
     <iRODSMeta None mgs.book.author.email jane_doe@email.com 1>,
     <iRODSMeta None mgs.book.author.email sweetdoe@bambi.be 1>,
     <iRODSMeta None mgs.book.ebook Available None>,
     <iRODSMeta None mgs.book.publishing_date 2015-02-01 None>,
     <iRODSMeta None mgs.book.cover_colors red None>,
     <iRODSMeta None mgs.book.cover_colors blue None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

- If a field is provided that is not included in a schema, it will be
  ignored, and you will only get a warning if `verbose` is `True`.

``` python
mini_md = {'title' : 'I only have a title', 'publishing_date' : '2023-04-28',
           'author' : {'name' : 'Name Surname', 'email' : 'rightemail@domain.info'},
           'publishing_house' : 'Oxford'}
check_metadata(my_schema, mini_md, verbose = True)
```

    WARNING:root:The following required fields are missing and the default value will be used: mgs.book.publisher (Tor)
    WARNING:root:The following non required fields are missing: mgs.book.cover_colors, mgs.book.ebook.
    WARNING:root:The following fields do not belong to the schema and will be ignored: publishing_house.
    WARNING:root:The following non required fields are missing: mgs.book.author.age.

    [<iRODSMeta None mgs.book.title I only have a title None>,
     <iRODSMeta None mgs.book.publishing_date 2023-04-28 None>,
     <iRODSMeta None mgs.book.author.name Name Surname 0>,
     <iRODSMeta None mgs.book.author.email rightemail@domain.info 0>,
     <iRODSMeta None mgs.book.publisher Tor None>]

``` python
del mini_md['publishing_house']
```

Once the presence of fields has been checked, we move on to
appropriateness: are the values ok based on the requirements of the
different fields? The `validators` package is used to validate the range
of numbers as well as email and urls.

On this level, there is no effect of `verbose`, because if you are
providing a value you will most certainly want to know that it has
failed:

- when required fields *with no default value* are wrong an error is
  thrown.
- when required fields with default values are wrong, the default is
  used and a warning is printed.
- when non required fields are wrong, they are ignored and a warning is
  printed.

### Numbers

Integer and float simple fields must be of type `int` or `float`
respectively or something that can be converted to such format.
`validators.between()` is used to make sure that the number is within
the provided range.

``` python
my_metadata['author'][0]['age'] = 30
checked_metadata = check_metadata(my_schema, my_metadata)
[x for x in checked_metadata if x.name.startswith('mgs.book.author') and x.units == '0']
```

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>,
     <iRODSMeta None mgs.book.author.age 30 0>]

``` python
# provided as a string that can be converted with `int()`
my_metadata['author'][0]['age'] = '30'
checked_metadata = check_metadata(my_schema, my_metadata)
[x for x in checked_metadata if x.name.startswith('mgs.book.author') and x.units == '0']
```

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>,
     <iRODSMeta None mgs.book.author.age 30 0>]

``` python
# wrong range: it should be between 12 and 99
my_metadata['author'][0]['age'] = 103
checked_metadata = check_metadata(my_schema, my_metadata)
[x for x in checked_metadata if x.name.startswith('mgs.book.author') and x.units == '0']
```

    WARNING:root:The values provided for `mgs.book.author.age` are not valid and will be ignored.

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>]

``` python
# wrong format
my_metadata['author'][0]['age'] = 'thirty'
checked_metadata = check_metadata(my_schema, my_metadata)
[x for x in checked_metadata if x.name.startswith('mgs.book.author') and x.units == '0']
```

    WARNING:root:The values provided for `mgs.book.author.age` are not valid and will be ignored.

    [<iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>]

### Dates, times and datetimes

Dates, times and datetimes can be provided as `datetime.date`,
`datetime.time` or `datetime.datetime` objects or as strings that can be
converted as such via their `fromisoformat()` or `fromtimestamp()`
methods. The final value is a string in ISO Format.

``` python
from datetime import date
import time
```

``` python
mini_md['publishing_date'] = date.today()
check_metadata(my_schema, mini_md)
```

    [<iRODSMeta None mgs.book.title I only have a title None>,
     <iRODSMeta None mgs.book.publishing_date 2023-04-28 None>,
     <iRODSMeta None mgs.book.author.name Name Surname 0>,
     <iRODSMeta None mgs.book.author.email rightemail@domain.info 0>,
     <iRODSMeta None mgs.book.publisher Tor None>]

``` python
mini_md['publishing_date'] = date.fromtimestamp(time.time())
check_metadata(my_schema, mini_md)
```

    [<iRODSMeta None mgs.book.title I only have a title None>,
     <iRODSMeta None mgs.book.publishing_date 2023-04-28 None>,
     <iRODSMeta None mgs.book.author.name Name Surname 0>,
     <iRODSMeta None mgs.book.author.email rightemail@domain.info 0>,
     <iRODSMeta None mgs.book.publisher Tor None>]

``` python
mini_md['publishing_date'] = '03/11/1990'
check_metadata(my_schema, mini_md)
```

    ValueError: None of the values provided for `mgs.book.publishing_date` are valid.

### URLs and emails

``` python
my_metadata['author'][0]['age'] = 30
my_metadata['author'][1]['email'].append('bademail@whatevs')
check_metadata(my_schema, my_metadata)
```

    WARNING:root:The following values provided for `mgs.book.author.email` are not valid and will be ignored: bademail@whatevs.

    [<iRODSMeta None mgs.book.title A book not written yet None>,
     <iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>,
     <iRODSMeta None mgs.book.author.age 30 0>,
     <iRODSMeta None mgs.book.author.name Jane Doe 1>,
     <iRODSMeta None mgs.book.author.email jane_doe@email.com 1>,
     <iRODSMeta None mgs.book.author.email sweetdoe@bambi.be 1>,
     <iRODSMeta None mgs.book.ebook Available None>,
     <iRODSMeta None mgs.book.publishing_date 2015-02-01 None>,
     <iRODSMeta None mgs.book.cover_colors red None>,
     <iRODSMeta None mgs.book.cover_colors blue None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

In the example above, *one* of the provided emails is wrong, and
therefore it is just ignored. In the next section we see that if the
value is missing or the only provided value is wrong, an error is
thrown, because the field is required.

### Composite fields

Within composite fields, the same rules apply as for schemas. First,
presence is checked: required values without default throw an error when
they are missing, while other cases of missing or extra fields throw
warnings only when `verbose` is `True`.

Moreover, composite fields are never required themselves based on the
schema, but they are required if any of their fields are required.

As shown above, bad values throw warnings in all cases.

``` python
my_metadata['author'].append({'name' : 'etal'})
check_metadata(my_schema, my_metadata)
```

    WARNING:root:The following values provided for `mgs.book.author.email` are not valid and will be ignored: bademail@whatevs.

    KeyError: 'The following required fields are missing and there is no default: mgs.book.author.email.'

``` python
#error: true
my_metadata['author'][2]['email'] = 'bademail.com'
check_metadata(my_schema, my_metadata)
```

    WARNING:root:The following values provided for `mgs.book.author.email` are not valid and will be ignored: bademail@whatevs.

    ValueError: None of the values provided for `mgs.book.author.email` are valid.

``` python
my_metadata['author'][2]['email'] = 'bademail@domain.com'
check_metadata(my_schema, my_metadata)
```

    WARNING:root:The following values provided for `mgs.book.author.email` are not valid and will be ignored: bademail@whatevs.

    [<iRODSMeta None mgs.book.title A book not written yet None>,
     <iRODSMeta None mgs.book.author.name Fulano De Tal 0>,
     <iRODSMeta None mgs.book.author.email fulano.detal@domain.info 0>,
     <iRODSMeta None mgs.book.author.age 30 0>,
     <iRODSMeta None mgs.book.author.name Jane Doe 1>,
     <iRODSMeta None mgs.book.author.email jane_doe@email.com 1>,
     <iRODSMeta None mgs.book.author.email sweetdoe@bambi.be 1>,
     <iRODSMeta None mgs.book.author.name etal 2>,
     <iRODSMeta None mgs.book.author.email bademail@domain.com 2>,
     <iRODSMeta None mgs.book.ebook Available None>,
     <iRODSMeta None mgs.book.publishing_date 2015-02-01 None>,
     <iRODSMeta None mgs.book.cover_colors red None>,
     <iRODSMeta None mgs.book.cover_colors blue None>,
     <iRODSMeta None mgs.book.publisher Tor None>]

# Final notes on implementation

The metadata can be applied to an object or collection `item` with
`my_schema.apply(item, my_metadata)`, which basically calls
`check_metadata()` and then provides the list to
`item.metadata.apply_atomic_operations()`, adding each of the AVUs. In
addition, another AVU is added with name `{prefix}.__version__`
(e.g. `mgs.book.__version__`) indicating the version of the schema used
for annotation (in this case, “2.0.0”).

However, before actually adding the metadata, `apply()` does two things:

- It checks whether there already is a `{prefix}.__version__` AVU and
  prints a warning if it’s different from the version of the current
  schema.
- It removes all existing metadata with the same prefix.

This is the same behavior from the ManGO portal: it replaces all
existing metadata linked to a schema with the metadata provided in this
instance.
