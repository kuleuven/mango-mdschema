import json

from irods.data_object import iRODSDataObject
from irods.collection import iRODSCollection
from irods.meta import AVUOperation

class Schema:
    
    def __init__(self, path: str):
        """Class representing a Metadata Schema to apply.

        Args:
            path (str): Path to the metadata schema.
            
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
        
        # add properties with their particular classes
        
    def apply(item: iRODSCollection | iRODSDataObject, metadata: dict, verbose: bool = False):
        """Apply a metadata schema to an iRODS data object or collection.

        Args:
            item (iRODSCollection | iRODSDataObject): iRODS data object or collection to apply metadata to.
            metadata (dict): Dictionary of metadata to apply.
            verbose (bool, optional): Whether warning should be printed when non-required fields are missing
                and when the default value of a required field is used.
                Defaults to False.
                Warnings will be printed when non-required fields are present but not valid.
        """
        # make sure that the required fields are present
        ## raise error if any required field is not present and there is no default
        ## send warnings (if verbose) for missing non-required fields
        ## send warnings (if verbose) when the default value of a required field is used
        
        # check that all (required) fields are valid AND turn them into AVUs with flattened name
        # if a required field is not valid print an error
        # if a non-required field is not valid print a warning (always)
        
        # create a list with the valid AVUs
        avus = []
        
        # then apply atomic operations
        item.metadata.apply_atomic_operations(*[AVUOperation(operation='add', avu=x) for x in avus])
        