Metadata schemas in Python
================

# Basic workflow

In the most basic use of the package, you create a `Schema` instance
with the path to your JSON schema (which should follow a specific
format), you have a dictionary with name-value pairs for metadata, and
you apply them to one or more iRODS objects (data objects or
collections).

In this tutorial we won’t show how to apply them (see README) but how to
check that the metadata is compatible with the schema, what requirements
are checked and what the consequences of mismatches are.

First we import what we need. The `Schema` class is the most important
tool in this package: it reads a schema from file, validates it and lets
you validate and apply metadata. `check_metadata()` is a function called
by the `apply()` method of a `Schema` but you can use it to validate a
dictionary of metadata against a schema.

``` python
from mango_mdschema import Schema, check_metadata
```

Create a schema by providing the path to the file. (In the future,
`pathlib.Path` objects will also be accepted).

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

Validate the metadata agains the schema with `check_metadata()`. The
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

## Metadata format

The `metadata` argument of `check_metadata()` and `Schema.apply()`
(which calls `check_metadata()`) must be a dictionary in which the keys
represent the names/IDs of the fields *without namespacing* and the
values, the value of the AVU to add.

If the field is a checkbox for which multiple values have been selected
*or* a repeatable field with multiple values, then the value in the
dictionary should be a list of such values.

For composite fields, the value should be a dictionary with the same
format: keys are field names without namespacing and values, the right
value.

## Metadata validation

The `validators` package is used to validate some formats; others are
custom. Naturally, multiple-choice values are contrasted against the
possible values.

### Numbers

Integer and float simple fields must be of type `int` or `float`
respectively or something that can be converted to such format.
`validators.between()` is used to make sure that the number is within
the provided range.

### Dates, times and datetimes

Dates, times and datetimes can be provided as `datetime.date`,
`datetime.time` or `datetime.datetime` objects or as strings that can be
converted as such via their `fromisoformat()` or `fromtimestamp()`
methods. The final value is a string in ISO Format.

### URLs and emails

URLs and emails are validated with the `validators` package.

# Other things to document

- With the `apply()` method, existing metadata related to the schema
  will be removed, and if the version if different it will be recorded
  in a warning (if `verbose`).
- The version number of the schema will be added as
  `{prefix}.{schema_name}.__version__`.
- Attributes of the `Schema` class, e.g. `name`, `fields`,
  `required_fields`, `version`.
- Checking the requirements of a field.

``` python
my_schema.name
```

    'book'

``` python
my_schema.prefix
```

    'mgs.book'

``` python
my_schema.version
```

    '2.0.0'

``` python
my_schema.required_fields
```

    {'title': None, 'publishing_date': None, 'publisher': 'Tor'}

``` python
my_schema.fields['author'].required_fields
```

    {'name': None, 'email': None}

``` python
my_schema.check_requirements('title')
```

    Type: text.
                    Required: True. Default: None.
                    Repeatable: False.
                    

``` python
my_schema.check_requirements('author')
```

    Type: object.
                    Required: False.
                    Repeatable: False.
                    
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
                    
