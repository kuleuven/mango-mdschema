""""Unit tests for the Schema class"""

from datetime import date
import unittest
import os
import logging
from unittest.mock import MagicMock, call

from irods.meta import iRODSMeta, AVUOperation

from mango_mdschema.schema import Schema
from mango_mdschema.exceptions import ConversionError, ValidationError
from mango_mdschema.fields import (
    TextField,
    EmailField,
    NumericField,
    DateField,
    MultipleField,
    CompositeField,
    RepeatableField,
)

# Set up logging
logger = logging.getLogger("mango_mdschema")
logger.setLevel(logging.DEBUG)


class TestLoadSchema(unittest.TestCase):
    """Unit tests for Schema loading from json files"""

    # pylint: disable=missing-docstring

    def test_load_schema_from_file(self):
        """Test loading a schema from a schema file"""

        # Construct the schema file path
        schema_file = os.path.join(
            os.path.dirname(__file__), "resources", "book-2.0.0-published.json"
        )

        # Load the schema
        schema = Schema(schema_file)

        # Perform assertions on the loaded schema
        self.assertEqual(schema.name, "book")
        self.assertEqual(schema.version, "2.0.0")
        self.assertEqual(schema.title, "Published Book")
        self.assertEqual(len(schema.fields), 8)
        self.assertIsInstance(schema.fields["title"], TextField)
        self.assertEqual(schema.fields["title"].name, "book.title")
        self.assertIsInstance(schema.fields["author"], RepeatableField)
        self.assertEqual(schema.fields["author"].name, "book.author")
        author_field = schema.fields["author"].field
        self.assertIsInstance(author_field, CompositeField)
        self.assertEqual(author_field.name, "book.author")
        self.assertIsInstance(author_field.fields["name"], TextField)
        self.assertEqual(author_field.fields["name"].name, "book.author.name")
        self.assertIsInstance(author_field.fields["email"], RepeatableField)
        self.assertIsInstance(author_field.fields["email"].field, EmailField)
        self.assertEqual(author_field.fields["email"].type, "email")
        self.assertTrue(author_field.fields["email"].required)
        self.assertIsInstance(author_field.fields["age"], NumericField)
        self.assertEqual(author_field.fields["age"].type, "integer")
        self.assertEqual(author_field.fields["age"].minimum, 12)
        self.assertEqual(author_field.fields["age"].maximum, 99)
        self.assertIsInstance(schema.fields["publishing_date"], DateField)
        self.assertIsInstance(schema.fields["cover"], CompositeField)
        cover_field = schema.fields["cover"]
        self.assertEqual(cover_field.name, "book.cover")
        self.assertIsInstance(cover_field.fields["colors"], MultipleField)
        self.assertEqual(len(cover_field.fields["colors"].choices), 4)
        self.assertEqual(cover_field.fields["colors"].choices[0], "red")
        self.assertTrue(cover_field.fields["colors"].multiple)
        self.assertIsInstance(cover_field.fields["type"], MultipleField)
        self.assertEqual(len(cover_field.fields["type"].choices), 2)
        self.assertIsInstance(schema.fields["publisher"], MultipleField)
        self.assertIsInstance(schema.fields["market_price"], NumericField)
        self.assertEqual(schema.fields["market_price"].type, "float")


class TestApplyAndExtractSchema(unittest.TestCase):
    """Unit tests for the Schema.apply() and Schema.to_avus() methods"""

    # pylint: disable=missing-docstring

    def setUp(self):
        # Create mock iRODSCollection and iRODSDataObject objects
        self.collection = MagicMock()
        self.data_object = MagicMock()

        # Construct the schema file path
        schema_file = os.path.join(
            os.path.dirname(__file__), "resources", "book-2.0.0-published.json"
        )

        # Create a sample schema
        self.schema = Schema(schema_file)

        # Create a sample metadata dictionary
        self.metadata = [
            {
                "title": "Valid Book 1",
                "author": [
                    {
                        "name": "John Doe",
                        "email": ["john.doe@kuleuven.be"],
                        "age": 42,
                    }
                ],
                "publishing_date": "2024-01-25",
                "cover": {"colors": ["red", "blue"], "type": "hard"},
                "publisher": "Corgi",
            },
            {
                "title": "Valid Book 2",
                "author": [
                    {
                        "name": "Jane Doe",
                        "email": ["jane.doe@kuleuven.be"],
                        "age": 30,
                    },
                    {
                        "name": "John Doe",
                        "email": ["john.doe@kuleuven.be"],
                        "age": 42,
                    },
                ],
                "publishing_date": "2024-01-01",
                "cover": {"type": "soft"},
                "ebook": "Available",
                "summary": None,
            },
        ]

        # Create list of expected iRODSMeta objects for the above sample metadata
        self.avus = [
            [
                iRODSMeta(
                    name="mgs.book.title", value=self.metadata[0]["title"], units=None
                ),
                iRODSMeta(
                    name="mgs.book.author.name",
                    value=self.metadata[0]["author"][0]["name"],
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.author.email",
                    value=self.metadata[0]["author"][0]["email"][0],
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.author.age",
                    value=str(self.metadata[0]["author"][0]["age"]),
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.publishing_date",
                    value=self.metadata[0]["publishing_date"],
                    units=None,
                ),
                iRODSMeta(
                    name="mgs.book.cover.colors",
                    value=self.metadata[0]["cover"]["colors"][0],
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.cover.colors",
                    value=self.metadata[0]["cover"]["colors"][1],
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.cover.type",
                    value=self.metadata[0]["cover"]["type"],
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.publisher",
                    value=self.metadata[0]["publisher"],
                    units=None,
                ),
            ],
            [
                iRODSMeta(
                    name="mgs.book.title", value=self.metadata[1]["title"], units=None
                ),
                iRODSMeta(
                    name="mgs.book.author.name",
                    value=self.metadata[1]["author"][0]["name"],
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.author.email",
                    value=self.metadata[1]["author"][0]["email"][0],
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.author.age",
                    value=str(self.metadata[1]["author"][0]["age"]),
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.author.name",
                    value=self.metadata[1]["author"][1]["name"],
                    units="2",
                ),
                iRODSMeta(
                    name="mgs.book.author.email",
                    value=self.metadata[1]["author"][1]["email"][0],
                    units="2",
                ),
                iRODSMeta(
                    name="mgs.book.author.age",
                    value=str(self.metadata[1]["author"][1]["age"]),
                    units="2",
                ),
                iRODSMeta(
                    name="mgs.book.publishing_date",
                    value=self.metadata[1]["publishing_date"],
                    units=None,
                ),
                iRODSMeta(
                    name="mgs.book.cover.type",
                    value=self.metadata[1]["cover"]["type"],
                    units="1",
                ),
                iRODSMeta(
                    name="mgs.book.ebook", value=self.metadata[1]["ebook"], units=None
                ),
                iRODSMeta(
                    name="mgs.book.publisher",
                    value=self.schema.fields["publisher"].default,
                    units=None,
                ),
            ],
        ]

    def test_validate_valid_metadata(self):
        # Validate the sample metadata against the schema
        for i, metadata in enumerate(self.metadata):
            result = self.schema.validate(metadata)

            self.assertIsInstance(result, dict, msg=f"Sample {i}")
            self.assertEqual(result["title"], metadata["title"], msg=f"Sample {i}")
            self.assertEqual(result["author"], metadata["author"], msg=f"Sample {i}")
            self.assertEqual(
                result["publishing_date"],
                date.fromisoformat(metadata["publishing_date"]),
                msg=f"Sample {i}",
            )
            self.assertEqual(
                result["publisher"],
                (
                    metadata["publisher"]
                    if "publisher" in metadata
                    else self.schema.fields["publisher"].default
                ),
                msg=f"Sample {i}",
            )

    def test_validate_invalid_metadata(self):
        # Modify the metadata to make it invalid
        invalid_metadata = self.metadata.copy()

        invalid_metadata[0]["publishing_date"] = "invalid-date"
        with self.assertRaises(ConversionError, msg="Invalid date") as context:
            self.schema.validate(invalid_metadata[0])
        self.assertEqual(context.exception.field, "book.publishing_date")
        self.assertEqual(context.exception.value, "invalid-date")

        invalid_metadata[1]["author"][0]["email"] = "invalid-email"
        with self.assertRaises(ValidationError, msg="Invalid email") as context:
            self.schema.validate(invalid_metadata[1])
        self.assertEqual(context.exception.field, "book.author.email")
        self.assertEqual(context.exception.value, "invalid-email")

    def test_convert_metadata(self):
        for i, metadata in enumerate(self.metadata):
            # Convert the sample metadata to the iRODS AVU format
            avus = self.schema.to_avus(metadata)

            # Perform assertions on the converted AVUs
            self.assertEqual(len(avus), len(self.avus[i]), msg=f"Sample {i}")
            for j, avu in enumerate(avus):
                self.assertEqual(avu.name, self.avus[i][j].name, msg=f"Sample {i}")
                self.assertEqual(avu.value, self.avus[i][j].value, msg=f"Sample {i}")
                self.assertEqual(avu.units, self.avus[i][j].units, msg=f"Sample {i}")

    def test_apply_metadata_to_collection(self):
        # Apply the sample metadata to the mock iRODSCollection object
        self.schema.apply(self.collection, self.metadata[0])
        assert all(isinstance(x.value, str) for x in self.avus[0])

        # Perform assertions on AVU operations
        added = [AVUOperation(operation="add", avu=x) for x in self.avus[0]] + [
            AVUOperation(
                operation="add",
                avu=iRODSMeta("mgs.book.__version__", self.schema.version),
            )
        ]
        deleted = []
        assert self.collection.metadata.apply_atomic_operations.call_args_list == [
            call(*deleted),
            call(*added),
        ], "Add metadata to collection with no previous metadata"

        self.collection.reset_mock()

        # Apply the sample metadata to the mock iRODSCollection object
        # with already existing metadata (to test the update operation)
        self.collection.metadata.items.return_value = self.avus[0] + [
            iRODSMeta("mgs.book.__version__", "1.0.0")
        ]
        self.schema.apply(self.collection, self.metadata[1])
        assert all(isinstance(x.value, str) for x in self.avus[0])

        # Perform assertions on AVU operations
        added = [AVUOperation(operation="add", avu=x) for x in self.avus[1]] + [
            AVUOperation(
                operation="add",
                avu=iRODSMeta("mgs.book.__version__", self.schema.version),
            )
        ]
        deleted = [AVUOperation(operation="remove", avu=x) for x in self.avus[0]] + [
            AVUOperation(
                operation="remove",
                avu=iRODSMeta("mgs.book.__version__", "1.0.0"),
            )
        ]
        assert self.collection.metadata.apply_atomic_operations.call_args_list == [
            call(*deleted),
            call(*added),
        ], "Apply metadata with existing metadata of previous version"

    def test_extract_metadata_from_data_object(self):
        # Set up the mock iRODSDataObject to return the sample metadata
        self.data_object.metadata.items.return_value = self.avus[0]

        # Extract the metadata from the mock iRODSDataObject
        extracted_metadata = self.schema.extract(self.data_object)

        # Perform assertions on the extracted metadata
        self.assertIsInstance(extracted_metadata, dict)
        self.assertEqual(extracted_metadata["title"], self.metadata[0]["title"])
        self.assertEqual(extracted_metadata, self.schema.validate(self.metadata[0]))

    def test_empty_metadata(self):
        # Set up the mock iRODSDataObject to return empty metadata
        self.data_object.reset_mock()
        self.data_object.metadata.items.return_value = []

        # Extract the metadata from the mock iRODSDataObject
        extracted_metadata = self.schema.extract(self.data_object)

        # Perform assertions on the extracted metadata
        self.assertIsInstance(extracted_metadata, dict)
        self.assertEqual(extracted_metadata, {})

        # Set up the mock iRODSDataObject to return non-relevant metadata
        self.data_object.reset_mock()
        self.data_object.metadata.items.return_value = [
            iRODSMeta(
                name="mgs.other_schema.title",
                value="Title for other schema",
                units=None,
            ),
            iRODSMeta(
                name="subject.length",
                value="11",
                units="cm",
            ),
        ]

        # Extract the metadata from the mock iRODSDataObject
        extracted_metadata = self.schema.extract(self.data_object)

        # Perform assertions on the extracted metadata
        self.assertIsInstance(extracted_metadata, dict)
        self.assertEqual(extracted_metadata, {})

    def test_reversibility(self):
        for i, metadata in enumerate(self.metadata):
            # Convert the sample metadata to the iRODS AVU format
            avus = self.schema.to_avus(metadata)
            validated = self.schema.validate(metadata)

            # Convert the AVUs back to metadata
            reconstructed = self.schema.from_avus(avus)

            if "summary" in validated and validated["summary"] is None:
                # If the summary field is present in the validated metadata but is None,
                # it will not be present in the reconstructed metadata because
                # the None values are not stored in the AVUs
                self.assertNotIn("summary", reconstructed, msg=f"Sample {i}")
                reconstructed["summary"] = None

            # Perform assertions on the converted metadata
            self.assertEqual(validated, reconstructed, msg=f"Sample {i}")


if __name__ == "__main__":
    unittest.main()
