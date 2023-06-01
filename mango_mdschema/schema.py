import json
import logging

from irods.data_object import iRODSDataObject
from irods.collection import iRODSCollection
from irods.meta import AVUOperation, iRODSMeta

from mango_mdschema.fields import Field
from mango_mdschema.helpers import check_metadata, bold


class Schema:
    def __init__(self, path: str, prefix: str = "mgs"):
        """Class representing a Metadata Schema to apply.

        Args:
            path (str): Path to the metadata schema.
            prefix (str): Prefix to add to the metadata names.
                Default is 'mgs' (ManGO schema).

        Attributes:
            name (str): Name of the schema.
            version (str): Version of the schema.
            title (str): Title of the schema, for messages.
                The name if no such title is provided in the JSON (which should not happen).
            fields (dict of Input): Fields of the schema.


        Raises:
            IOError: When the file cannot be opened.
            KeyError: Some fields are required
                ('schema_name', 'version', 'status', 'properties' and 'title'.)
                If any of them are missing from the schema, this error is raised.
            ValueError: When the schema is not published.
        """
        # TODO allow the path to be a pathlib.Path or io.TextIOWrapper

        with open(path, "r") as f:
            try:
                schema = json.load(f)
            except:
                raise IOError(
                    "There was an error opening or loading your schema from the requested path."
                )
        # check that all necessary fields are present
        required_fields = ["schema_name", "version", "status", "properties"]
        if sum(x not in schema for x in required_fields) > 0:
            missing = [x for x in required_fields if not x in schema]
            raise KeyError(
                f"The following fields are missing from the schema: {','.join(missing)}"
            )

        # check that the schema is published
        if schema["status"] != "published":
            raise ValueError(
                f"The schema is not published: it cannot be used to apply metadata!"
            )

        self.name = schema["schema_name"]
        self.version = schema["version"]
        self.prefix = f"{prefix}.{self.name}"
        self.title = schema["title"] if schema["title"] else self.name
        self.fields = {
            k: Field.choose_class(k, v) for k, v in schema["properties"].items()
        }
        for subfield in self.fields.values():
            subfield.flatten_name(self.prefix)
        self.required_fields = {
            subfield.name: subfield.default
            for subfield in self.fields.values()
            if subfield.required
        }

    def apply(
        self,
        item: iRODSCollection | iRODSDataObject,
        metadata: dict,
        verbose: bool = False,
    ):
        """Apply a metadata schema to an iRODS data object or collection.

        Args:
            item (iRODSCollection | iRODSDataObject): iRODS data object or collection to apply metadata to.
            metadata (dict): Dictionary of metadata to apply.
            verbose (bool, optional): Whether warning should be printed when non-required fields are missing,
                when the default value of a required field is used
                and when fields are provided that do not belong to the schema.
                Defaults to False.
                Warnings will be printed when non-required fields are present but not valid.
        """
        avu_version_name = f"{self.prefix}.__version__"
        # report if data is annotated with a previous version
        existing_mdschema = avu_version_name in item.metadata
        if existing_mdschema and item.metadata[avu_version_name] != self.version:
            logging.warning(
                "There is existing metadata linked to a previous version of this schema. It will be removed."
            )
        # delete existing AVUs linked to this metadata and warn in that case
        existing_avus = [
            x for x in item.metadata.items() if x.name.startswith(self.prefix)
        ]
        item.metadata.apply_atomic_operations(
            *[AVUOperation(operation="remove", avu=x) for x in existing_avus]
        )
        if verbose:
            logging.warning(
                f"All of {len(existing_avus)} existing AVUs linked to the schema were removed."
            )

        # create a list with the valid AVUs
        avus = check_metadata(self, metadata, verbose)
        avus.append(iRODSMeta(avu_version_name, self.version))

        # then apply atomic operations
        item.metadata.apply_atomic_operations(
            *[AVUOperation(operation="add", avu=x) for x in avus]
        )

    def check_requirements(self, field):
        print(self.fields[field])

    def __str__(self):
        preamble = [
            bold(self.title),
            f"Metadata annotated with the schema '{self.name}' ({self.version}) carry the prefix '{self.prefix}'.",
            f"This schema contains the following {len(self.fields)} fields:",
        ]
        for name, field in self.fields.items():
            preamble.append(
                f"- {bold(name)}, of type '{field.type}'{' (required)' if field.required else ''}."
            )
        return "\n".join(preamble)
