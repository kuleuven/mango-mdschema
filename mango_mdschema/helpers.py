import logging

from irods.meta import iRODSMeta


def check_metadata(
    schema, metadata: dict, verbose: bool = False, index: str = None
) -> list:
    """Check that the metadata for a schema or composite field is valid and generate the AVUs.

    Args:
        schema (schema.Schema | fields.CompositeField): A schema or composite field.
        metadata (dict): Dictionary with metadata to apply.
        verbose (bool, optional): Whether warnings should be logged when non required
            fields are missing or defaults are used.. Defaults to False.
        index (str, optional): Index of the composite field, for the units of its
            subfields. Defaults to None.

    Raises:
        KeyError: When a required field is missing and there is no default.

    Returns:
        list of iRODSMeta: Processed AVUs.
    """
    # make sure that the required fields are present
    missing_required = [
        schema.fields[field_name].avu_name
        for field_name, default in schema.required_fields.items()
        if field_name not in metadata.keys() and default is None
    ]
    # raise error if any required field is not present and there is no default
    if len(missing_required) > 0:
        raise KeyError(
            (
                "The following required fields are missing and there is no default: "
                f"{', '.join(missing_required)}."
            )
        )

    go_to_default = [
        field_name
        for field_name, default in schema.required_fields.items()
        if field_name not in metadata and default is not None
    ]
    to_use = {k: v for k, v in metadata.items() if k in schema.fields}

    if verbose:
        # send warning when the default value of a required field is used
        if len(go_to_default) > 0:
            default_pairs = ", ".join(
                f"{schema.fields[field_name].avu_name} ({schema.required_fields[field_name]})"
                for field_name in go_to_default
            )
            logging.warning(
                "The following required fields are missing and the default value will be used: %s",
                default_pairs,
            )

        # send warning for missing non-required fields
        missing_non_required = [
            field.avu_name
            for field_name, field in schema.fields.items()
            if not field.required and field_name not in metadata
        ]
        if len(missing_non_required) > 0:
            logging.warning(
                "The following non required fields are missing: %s.",
                ", ".join(missing_non_required),
            )

        # send warnings for irrelevant metadata fields
        if len(to_use) < len(metadata):
            logging.warning(
                "The following fields do not belong to the schema and will be ignored: %s.",
                ", ".join(x for x in metadata.keys() if x not in schema.fields),
            )

    for k, v in to_use.items():
        to_use[k] = schema.fields[k].create_avu(v, index, verbose)
    for k in go_to_default:
        to_use[k] = [
            iRODSMeta(schema.fields[k].avu_name, schema.fields[k].default, index)
        ]

    return [
        meta for meta_list in to_use.values() for meta in meta_list if meta is not None
    ]


def bold(string: str) -> str:
    """Return the string in bold. Useful for printing."""
    return f"\033[1m{string}\033[0m"
