import json
import logging

from irods.data_object import iRODSDataObject
from irods.collection import iRODSCollection
from irods.meta import AVUOperation

import fields

class Schema:
    
    def __init__(self, path: str, prefix: str = 'mgs'):
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
        
        with open(path, 'r') as f:
            try:
                schema = json.load(f)
            except:
                raise IOError("There was an error opening or loading your schema from the requested path.")
        # check that all necessary fields are present
        required_fields = ['schema_name', 'version', 'status', 'properties']
        if sum(x not in schema for x in required_fields) > 0:
            missing = [x for x in required_fields if not x in schema]
            raise KeyError(f"The following fields are missing from the schema: {','.join(missing)}")
        
        # check that the schema is published
        if schema['version'] != 'published':
            raise ValueError(f"The schema is not published: it cannot be used to apply metadata!")
        
        self.name = schema['schema_name']
        self.version = schema['version']
        self.title = schema['title'] if schema['title'] else self.name
        self.fields = { k : fields.Field.choose_class(k, v) for k, v in schema['properties'].items()}
        for subfield in self.fields.values():
            subfield.flatten_name(f"{prefix}.{self.name}")
        self.required_fields = {subfield.name : subfield.default for subfield in self.fields.values() if subfield.required}
        
    def apply(self, item: iRODSCollection | iRODSDataObject, metadata: dict, verbose: bool = False):
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
        # make sure that the required fields are present
        missing_required = [field_name for field_name, default in self.required_fields.items()
                            if not field_name in metadata and default is None]
        ## raise error if any required field is not present and there is no default
        if len(missing_required) > 1:
            raise KeyError(f"The following required fields are missing and there is no default: {', '.join(missing_required)}.")
        
        go_to_default = [field_name for field_name, default in self.required_fields.items()
                         if not field_name in metadata and default is not None]
        to_use = {k : v for k, v in metadata if k in self.fields}
        
        if verbose:
            ## send warning when the default value of a required field is used
            if len(go_to_default) > 1:
                default_pairs = ', '.join(f"{field_name} ({self.required_fields[field_name]})" for field_name in go_to_default)
                logging.warning(f"The following required fields are missing and the default value will be used: {default_pairs}")
            
            ## send warning for missing non-required fields
            missing_non_required = [field_name for field_name, field in self.fields.items()
                                    if not field.required and not field_name in metadata]
            if len(missing_non_required) > 1:
                logging.warning(f"The following non required fields are missing: {', '.join(missing_non_required)}.")
            
            ## send warnings for irrelevant metadata fields
            if len(to_use) < len(metadata):
                extras = ', '.join(x for x in metadata.keys() if not x in self.fields)
                logging.warning(f"The following fields do not belong to the schema and will be ignored: {extras}.")
            
        
        # NOTE: use to_use, not metadata!
        # check that all (required) fields are valid AND turn them into AVUs with flattened name
        # do this with the field object itself :)
        # if a required field is not valid print an error
        # if a non-required field is not valid print a warning (always)
        
        # create a list with the valid AVUs
        avus = []
        
        # then apply atomic operations
        item.metadata.apply_atomic_operations(*[AVUOperation(operation='add', avu=x) for x in avus])
        