import os
import pathlib
import pytest

from irods.session import iRODSSession
from mango_mdschema.schema import Schema, get_mango_schema
from mango_mdschema.fields import (
    TextField,
    EmailField,
    NumericField,
    DateField,
    MultipleField,
    CompositeField,
    RepeatableField,
)

ZONE = "gbiomed"
TEST_PROJECT = "datateam_gbiomed"
TEST_SCHEMA = "schematest"
ENV_FILE = os.path.expanduser("~/.irods/irods_environment.json")


@pytest.fixture
def irods_session():
    session = iRODSSession(irods_env_file=ENV_FILE)
    assert session.zone == ZONE
    yield session
    session.cleanup()


@pytest.mark.skipif(not os.path.exists(ENV_FILE), reason="No iRODS to test this")
def test_loading_schema_from_irods(irods_session):

    # Load the schema
    irods_schema = get_mango_schema(
        irods_session, realm=TEST_PROJECT, schema_name=TEST_SCHEMA
    )
    schema = Schema(irods_schema)
    assert isinstance(schema, Schema)
    assert schema.name == TEST_SCHEMA


def test_loading_schema_pathlib():
    """Test loading a schema from a schema file"""

    # Construct the schema file path
    schema_file = pathlib.Path(
        os.path.dirname(__file__), "resources", "book-2.0.0-published.json"
    )

    # Load the schema
    schema = Schema(schema_file)

    # Perform assertions on the loaded schema
    assert schema.name == "book"
    assert schema.version == "2.0.0"
    assert schema.title == "Published Book"
    assert len(schema.fields) == 8
    assert isinstance(schema.fields["title"], TextField)
    assert schema.fields["title"].name == "book.title"
    assert isinstance(schema.fields["author"], RepeatableField)
    assert schema.fields["author"].name == "book.author"
    author_field = schema.fields["author"].field
    assert isinstance(author_field, CompositeField)
    assert author_field.name == "book.author"
    assert isinstance(author_field.fields["name"], TextField)
    assert author_field.fields["name"].name == "book.author.name"
    assert isinstance(author_field.fields["email"], RepeatableField)
    assert isinstance(author_field.fields["email"].field, EmailField)
    assert author_field.fields["email"].type == "email"
    assert author_field.fields["email"].required
    assert isinstance(author_field.fields["age"], NumericField)
    assert author_field.fields["age"].type == "integer"
    assert author_field.fields["age"].minimum == 12
    assert author_field.fields["age"].maximum == 99
    assert isinstance(schema.fields["publishing_date"], DateField)
    assert isinstance(schema.fields["cover"], CompositeField)
    cover_field = schema.fields["cover"]
    assert cover_field.name == "book.cover"
    assert isinstance(cover_field.fields["colors"], MultipleField)
    assert len(cover_field.fields["colors"].choices) == 4
    assert cover_field.fields["colors"].choices[0] == "red"
    assert cover_field.fields["colors"].multiple
    assert isinstance(cover_field.fields["type"], MultipleField)
    assert len(cover_field.fields["type"].choices) == 2
    assert isinstance(schema.fields["publisher"], MultipleField)
    assert isinstance(schema.fields["market_price"], NumericField)
    assert schema.fields["market_price"].type == "float"
