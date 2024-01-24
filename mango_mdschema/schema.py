"""Module containing the Schema class."""
from collections.abc import MutableMapping
import json
import logging
import warnings

from irods.data_object import iRODSDataObject
from irods.collection import iRODSCollection
from irods.meta import AVUOperation, iRODSMeta

from .constants import NAME_DELIMITER
from .helpers import bold, flattend_from_avu, flattened_to_avu, flatten, unflatten
from .fields import (
    TextField,
    EmailField,
    UrlField,
    NumericField,
    DateField,
    TimeField,
    DateTimeField,
    BooleanField,
    MultipleField,
    CompositeField,
    RepeatableField,
)

logger = logging.getLogger("mango_mdschema")


class Schema:
    """Class representing a Metadata Schema.

    Attributes:
        name (str): Name of the schema.
        version (str): Version of the schema.
        title (str): Title of the schema, for messages.
            The name if no such title is provided in the JSON (which should not happen).
        root (CompositeField): Root field of the schema.
        fields (dict): Dictionary of fields in the schema (alias for root.fields)
        required_fields (dict): Dictionary of required fields and their default values.
            If a field is required and has no default value, it is not present in the dictionary.
    """

    # Mapping of supported field types to their class
    field_types = {
        "text": TextField,
        "textarea": TextField,
        "email": EmailField,
        "url": UrlField,
        "date": DateField,
        "time": TimeField,
        "datetime-local": DateTimeField,
        "integer": NumericField,
        "float": NumericField,
        "checkbox": BooleanField,
        "select": MultipleField,
        "object": CompositeField,
    }

    def __init__(self, path: str, prefix: str = "mgs"):
        """Init a Schema object from a JSON file.

        Args:
            path (str): Path to the metadata schema.
            prefix (str): Prefix to add to the metadata names. Default is 'mgs' (ManGO schema).

        Raises:
            IOError: When the file cannot be opened.
            KeyError: Some fields are required
                ('schema_name', 'version', 'status', 'properties' and 'title'.)
                If any of them are missing from the schema, this error is raised.
            ValueError: When the schema is not published.
        """
        # TODO allow the path to be a pathlib.Path or io.TextIOWrapper

        with open(path, "r", encoding="utf-8") as f:
            try:
                schema = json.load(f)
            except IOError as err:
                raise IOError(
                    "There was an error opening or loading your schema from the requested path."
                ) from err
            except json.JSONDecodeError as err:
                raise IOError("There was an error decoding the JSON schema.") from err
        # check that all necessary fields are present
        required_fields = ["schema_name", "version", "status", "properties"]
        if sum(x not in schema for x in required_fields) > 0:
            missing = [x for x in required_fields if x not in schema]
            raise KeyError(
                f"The following fields are missing from the schema: {','.join(missing)}"
            )

        # check that the schema is published
        if schema["status"] != "published":
            raise ValueError(
                "The schema is not published: it cannot be used to apply metadata!"
            )

        self.name = schema["schema_name"]
        self.version = schema["version"]
        self.prefix = prefix
        self.title = schema["title"] if schema["title"] else self.name
        self.root = CompositeField(
            self.name,
            fields=[
                self.create_field(name=name, parent=self.name, **params)
                for name, params in schema["properties"].items()
            ],
        )

    @property
    def fields(self):
        """Get the fields of the schema."""
        return self.root.fields

    @property
    def required_fields(self):
        """Get the required fields of the schema."""
        return self.root.required_fields

    @classmethod
    def create_field(cls, name: str, parent: str, **params):
        """Field factory method.

        Args:
            name (str): Name of the field
            parent (str): Name of the parent field (full hierarchical name, including the schema name)
            params (dict): Parameters for the field.

        Raises:
            KeyError: When the field type is not supported.

        Returns:
            Field: The field.
        """
        name = NAME_DELIMITER.join([parent, name])
        if "type" not in params:
            raise KeyError(f"Field {name} should have a type.")
        if params["type"] not in cls.field_types:
            raise KeyError(f"Field type {params['type']} is not supported.")

        field_class = cls.field_types[params["type"]]

        if field_class == CompositeField:
            # Create subfields for composite field
            params["fields"] = [
                cls.create_field(name=subfield_name, parent=name, **subfield_params)
                for subfield_name, subfield_params in params["properties"].items()
            ]

        field = field_class(name, **params)
        # Decorate with RepeatableField if necessary
        return (
            field
            if not params.get("repeatable", False)
            else RepeatableField(field=field)
        )

    def validate(self, metadata: MutableMapping, convert: bool = True) -> bool:
        """Validate a dictionary of metadata against the schema.

        Validation is a 2 step process: First the values in the metadata dictionary
        are converted to it's Python representation (if needed) and then the values are
        validated.

        This method calles the validate method of the schema's root field.

        Args:
            metadata (dict): Dictionary of metadata to validate.
            convert (bool, optional): Whether to convert the values to their Python
                representation before validation. Defaults to True.

        Returns:
            dict: The clean and validated metadata

        Raises:
            ValidationError: If data is invalid.
            ConversionError: If data cannot be converted to the expected type.
        """
        return self.root.validate(metadata, convert)

    def convert(self, metadata: MutableMapping) -> MutableMapping:
        """Convert metadata values to their Python representation after
        unflattenning from AVUs.

        This method calles the convert method of the schema's root field.

        Args:
            metadata (dict): Dictionary of metadata to convert.

        Returns:
            dict: The converted metadata

        Raises:
            ConversionError: If data cannot be converted to the expected type.
        """
        return self.root.convert(metadata)

    def apply(
        self,
        item: iRODSCollection | iRODSDataObject,
        metadata: MutableMapping,
    ):
        """Apply metadata to an iRODS data object or collection.

        Args:
            item (iRODSCollection | iRODSDataObject): iRODS data object or collection
                to apply metadata to.
            metadata (dict): Dictionary of metadata to apply.

        Raises:
            ValidationError: If data is invalid.
            ConversionError: If data cannot be converted to the expected type.
        """
        avu_version_name = NAME_DELIMITER.join([self.prefix, self.name, "__version__"])
        # report if data is annotated with a previous version
        existing_mdschema = avu_version_name in item.metadata
        if existing_mdschema and item.metadata[avu_version_name].value != self.version:
            logger.warning(
                (
                    "Existing metadata found of another version '%s' of the schema `%s` found"
                    " and will be removed."
                ),
                self.version,
                self.name,
            )
        # delete existing AVUs linked to this metadata and warn in that case
        prefix = NAME_DELIMITER.join([self.prefix, self.name])
        existing_avus = [
            avu for avu in item.metadata.items() if avu.name.startswith(prefix)
        ]
        item.metadata.apply_atomic_operations(
            *[AVUOperation(operation="remove", avu=x) for x in existing_avus]
        )
        logger.info(
            "%s existing AVUs linked to the schema '%s' are removed.",
            len(existing_avus),
            self.name,
        )

        avus = list(self.to_avus(metadata, convert=True))
        avus.append(iRODSMeta(avu_version_name, self.version))

        # then apply atomic operations
        item.metadata.apply_atomic_operations(
            *[AVUOperation(operation="add", avu=x) for x in avus]
        )

    def extract(self, item: iRODSCollection | iRODSDataObject) -> MutableMapping:
        """Extract metadata from an iRODS data object or collection.

        Args:
            item (iRODSCollection | iRODSDataObject): iRODS data object or collection
                to extract metadata from.

        Returns:
            dict: Dictionary of metadata extracted from the item.

        Raises:
            ConversionError: If data cannot be converted to the expected type.
        """
        # get all AVUs linked to this metadata schema
        avus = [
            avu
            for avu in item.metadata.items()
            if avu.name.startswith(f"{self.prefix}{self.delimiter}{self.name}")
        ]
        # convert AVUs to a dictionary
        metadata = self.from_avus(avus)
        # convert metadata to their Python representation
        return self.convert(metadata)

    def to_avus(self, metadata: MutableMapping, convert: bool = True):
        """Generate AVUs from a dictionary of metadata.

        Before flattening, the metadata is first converted to the expected Python
        types (optional) and then validated.

        Args:
            metadata (dict): Dictionary of metadata to flatten to AVUs.
            convert (bool, optional): Whether to convert the values to their Python
                representation before validation. Defaults to True.

        Returns:
            list of iRODSMeta: List of AVUs.

        Raises:
            ValidationError: If data is invalid.
            ConversionError: If data cannot be converted to the expected type.
        """
        metadata = self.validate(metadata, convert)
        prefix = f"{self.prefix}{self.delimiter}{self.name}"
        return list(map(lambda x: flattened_to_avu(x, prefix)), flatten(metadata))

    def from_avus(self, avus: list[iRODSMeta]) -> MutableMapping:
        """Generate a dictionary of metadata from a list of AVUs.

        Args:
            avus (list of iRODSMeta): List of AVUs to unflatten.

        Returns:
            dict: Dictionary of metadata.

        Raises:
            ValidationError: If data is invalid.
            ConversionError: If data cannot be converted to the expected type.
        """
        prefix = f"{self.prefix}{self.delimiter}{self.name}"
        unflattened = unflatten(list(map(lambda x: flattend_from_avu(x, prefix), avus)))
        return self.root.convert(unflattened)

    def print_requirements(self, field: str):
        """Print the requirements of a field."""
        print(self.fields[field])

    def check_requirements(self, field):
        """This method is deprecated, use print_requirements instead."""
        warnings.warn(
            "This method is deprecated, use print_requirements instead.",
            DeprecationWarning,
        )
        self.print_requirements(field)

    def __str__(self):
        preamble = [
            bold(self.title),
            (
                f"Metadata annotated with the schema '{self.name}' ({self.version}) "
                f"carry the prefix '{self.prefix}'."
            ),
            f"This schema contains the following {len(self.fields)} fields:",
        ]
        for name, field in self.fields.items():
            preamble.append(
                f"- {bold(name)}, of type '{field.type}'{' (required)' if field.required else ''}."
            )
        return "\n".join(preamble)
