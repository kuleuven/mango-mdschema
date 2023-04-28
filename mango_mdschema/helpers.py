import logging

from irods.meta import iRODSMeta

def check_metadata(schema, metadata: dict, verbose: bool = False, index: int = None) -> list:
    """Check that the metadata provided for a schema or composite field is valid and generate the AVUs.

    Args:
        schema (schema.Schema | fields.CompositeField): A schema or composite field.
        metadata (dict): Dictionary with metadata to apply.
        verbose (bool, optional): Whether warnings should be logged when non required fields are missing
          or defaults are used.. Defaults to False.
        index (int, optional): Index of the composite field, for the units of its subfields.. Defaults to None.

    Raises:
        KeyError: When a required field is missing and there is no default.

    Returns:
        list of iRODSMeta: Processed AVUs.
    """
    # make sure that the required fields are present
    missing_required = [schema.fields[field_name].flattened_name
                        for field_name, default in schema.required_fields.items()
                        if not field_name in metadata and default is None]
    ## raise error if any required field is not present and there is no default
    if len(missing_required) > 0:
        raise KeyError(f"The following required fields are missing and there is no default: {', '.join(missing_required)}.")
    
    go_to_default = [field_name for field_name, default in schema.required_fields.items()
                     if not field_name in metadata and default is not None]
    to_use = {k : v for k, v in metadata.items() if k in schema.fields}
    
    if verbose:
        ## send warning when the default value of a required field is used
        if len(go_to_default) > 0:
            default_pairs = ', '.join(f"{schema.fields[field_name].flattened_name} ({schema.required_fields[field_name]})"
                                      for field_name in go_to_default)
            logging.warning(f"The following required fields are missing and the default value will be used: {default_pairs}")
        
        ## send warning for missing non-required fields
        missing_non_required = [field.flattened_name for field_name, field in schema.fields.items()
                                if not field.required and not field_name in metadata]
        if len(missing_non_required) > 0:
            logging.warning(f"The following non required fields are missing: {', '.join(missing_non_required)}.")
        
        ## send warnings for irrelevant metadata fields
        if len(to_use) < len(metadata):
            extras = ', '.join(x for x in metadata.keys() if not x in schema.fields)
            logging.warning(f"The following fields do not belong to the schema and will be ignored: {extras}.")
    
    for k, v in to_use.items():
        to_use[k] = schema.fields[k].create_avu(v, index, verbose)
    for k in go_to_default:
        to_use[k] = [iRODSMeta(schema.fields[k].flattened_name, schema.fields[k].default, index)]
    
    return [meta for meta_list in to_use.values() for meta in meta_list if meta is not None]