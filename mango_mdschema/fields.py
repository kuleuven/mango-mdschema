""""Classes representing the different types of fields in a metadata schema."""
from collections.abc import MutableMapping
import logging
import re
from datetime import datetime, date, time
from copy import copy

import validators

from .constants import NAME_DELIMITER
from .exceptions import ValidationError, ConversionError
from .helpers import bold, is_number

logger = logging.getLogger("mango_mdschema")


class Field:
    """
    Abstract base class representing a field of a metadata schema.

    Attributes:
        name (str): The (full) name of the field, i.e. with namespace prefix.
        type (str): The type of the field, defined within the subclass.
        required (bool): Whether the field is required.
        default (any, optional): The default value for the field, if it is required.
        repeatable (bool): Whether the field is repeatable.
        description (str): Description of the criteria for the field.
    """

    def __init__(self, name: str, **params):
        """Class representing a field of a metadata schema.

        Args:
            name (str): Name of the field (with namespace prefix).
            params (dict, optional): Additional parameters for the field.

        Raises:
            ValueError: When the field type is not provided.
        """
        self._name = name

        if "type" not in params:
            raise ValueError(f"No type defined for field {name}.")
        self.type = params.get("type")
        self.required = params.get("required", False)
        self.default = params.get("default", None)
        self.repeatable = params.get("repeatable", False)

    @property
    def name(self):
        """Get the name of the field."""
        return self._name

    @name.setter
    def name(self, value):
        """Set the name of the field."""
        self._name = value

    @property
    def basename(self):
        """Get the basename of the field name."""
        return self._name.split(NAME_DELIMITER)[-1]

    @basename.setter
    def basename(self, value):
        """Set the basename of the field name."""
        self._name = f"{self.namespace}{NAME_DELIMITER}{value}"

    @property
    def namespace(self):
        """Get the namespace (aka prefix) of the field name."""
        return NAME_DELIMITER.join(self._name.split(NAME_DELIMITER)[:-1])

    @namespace.setter
    def namespace(self, value):
        """Set the namespace (aka prefix) of the field name."""
        self._name = f"{value}{NAME_DELIMITER}{self.basename}"

    @property
    def default(self):
        """Get the default value of the field."""
        return self._default if self._default is not None else None

    @default.setter
    def default(self, value):
        """Set the default value of the field."""
        self._default = value

    @property
    def description(self):
        """Get description property of the field."""
        if not self.required:
            def_message = ""
        elif self.type == "object":  # if it's a composite field
            n_required = len(self.required_fields)  # pylint: disable=no-member
            def_message = (
                f" ({n_required} of its {len(self.fields)} fields "  # pylint: disable=no-member
                f"{'is' if n_required == 1 else 'are'} required.)"
            )
        else:
            def_message = f" {bold('Default')}: {self.default}."
        return "\n".join(
            [
                f"{bold('Type')}: {self.type}.",
                f"{bold('Required')}: {self.required}.{def_message}",
                f"{bold('Repeatable')}: {self.repeatable}.",
            ]
        )

    def validate(self, value, convert: bool = True, set_default: bool = True):
        """Validate the field value.

        Validation is a 3 step process: First the default value is applied
        if the value is empty, then the value is converted to it's
        Python representation (if needed) and finally it is validated.

        The default implementation calls the `apply_default`, `convert` and
        `assert_valid` methods to perform these 3 steps.

        Args:
            value: The field value to validate.
            convert (bool, optional): Whether to convert the value to it's Python
                representation before validating it. Defaults to True.
            set_default (bool, optional): Whether to set the default
                value if the value is empty before validating it. Defaults to True.

        Returns:
            Any: The cleaned value, if valid, or the default value, if empty.

        Raises:
            ValidationError: If the value is invalid.
            ConversionError: If the value cannot be converted.
        """
        if set_default:
            value = self.apply_default(value)
        if convert:
            value = self.convert(value)
        self.assert_valid(value)
        return value

    def assert_valid(self, value):
        """Check if the field value is valid.

        Default implementation throws an error if the value is empty and required.

        Raises:
            ValidationError: If the value is invalid.
        """
        if self.required and self.is_empty(value):
            raise ValidationError(f"Value required for `{self.name}`", self.name)

    def apply_default(self, value):
        """Apply the fields default if needed.

        Args:
            value: The value to check.

        Returns:
            Any: The value with the default applied as needed.
        """
        if self.is_empty(value) and self.default is not None:
            return self.convert(self.default)
        return copy(value)

    def convert(self, value):
        """Convert a value to it's Python representation.

        This method is the first step in every validation. It coerces the
        value to a correct datatype and raises ConversionError if that is
        not possible.

        This method is also used to convert the raw value after unflattening
        the metadata from the iRODS AVU's.

        Raises:
            ConversionError: If the value cannot be converted, or if the value
                is empty and no default is defined.
        """
        return copy(value)

    def is_empty(self, value):
        """Check if a value is empty.

        Args:
        value: The value to check.

        Returns: Whether the value is empty.
        """
        return value is None or value == "" or value == []

    def __str__(self):
        return self.description


class SimpleField(Field):
    """Base class for single-value fields."""


class TextField(SimpleField):
    """Class representing a text field."""

    def __init__(self, name: str, **params):
        params.setdefault("type", "text")
        super().__init__(name, **params)
        self.max_length = params.get("max_length", None)
        if self.type == "textarea":
            self.pattern = None  # no pattern support for "textarea"
        else:
            self.pattern = params.get("pattern", None)
            if (
                self.pattern is not None
                and not self.pattern.startswith("^")
                and not self.pattern.endswith("$")
            ):
                self.pattern = f"^{self.pattern}$"

    def assert_valid(self, value):
        super().assert_valid(value)
        if not isinstance(value, str) and value is not None:
            raise ValidationError(
                f"Value `{self.name}` must be a string", self.name, value
            )
        if self.max_length is not None and len(value) > int(self.max_length):
            raise ValidationError(
                f"Length of `{self.name}` exceeds max length of {self.max_length}: {value}",
                self.name,
                value,
            )
        if self.pattern is not None and not re.match(self.pattern, value):
            raise ValidationError(
                f"Value of `{self.name}` does not match pattern {self.pattern}: {value}",
                self.name,
                value,
            )

    def convert(self, value):
        return str(value) if value is not None else value

    @property
    def description(self):
        """Modify description property for text fields."""
        extra = ""
        if self.pattern is not None:
            extra = (
                f"fully matching the following regex: \033[91m{self.pattern}\033[0m."
            )
        return "\n".join([super().description, extra]) if extra else super().description


class EmailField(TextField):
    """Class representing an email field."""

    def __init__(self, name: str, **params):
        params.setdefault("type", "email")
        super().__init__(name, **params)

    def assert_valid(self, value):
        super().assert_valid(value)
        if value is not None and validators.email(value) is not True:
            raise ValidationError(
                f"Value `{self.name}` must be a valid email: {value}", self.name, value
            )


class UrlField(TextField):
    """Class representing a URL field."""

    def __init__(self, name: str, **params):
        params.setdefault("type", "url")
        super().__init__(name, **params)

    def assert_valid(self, value):
        super().assert_valid(value)
        if value is not None and validators.url(value) is not True:
            raise ValidationError(
                f"Value `{self.name}` must be a valid URL", self.name, value
            )


class BooleanField(SimpleField):
    """Class representing a boolean field."""

    def __init__(self, name: str, **params):
        params.setdefault("type", "checkbox")
        super().__init__(name, **params)

    def assert_valid(self, value):
        super().assert_valid(value)
        if not isinstance(value, bool) and value is not None:
            raise ValidationError(
                f"Value `{self.name}` must be a boolean", self.name, value
            )

    def convert(self, value):
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, str):
            value = value.lower()
            if value in ["true", "yes", "y", "1"]:
                return True
            if value in ["false", "no", "n", "0"]:
                return False
        raise ConversionError(
            f"Cannot convert {value} to a bool for `{self.name}`", self.name, value
        )


class NumericField(SimpleField):
    """Base class for numeric fields."""

    def __init__(self, name: str, minimum=None, maximum=None, **params):
        super().__init__(name, **params)
        if self.type not in ["integer", "float"]:
            raise NotImplementedError(
                "NumericField only supports integer and float fields"
            )
        self.numeric_type = int if self.type == "integer" else float
        self.minimum = self.numeric_type(minimum) if minimum is not None else None
        self.maximum = self.numeric_type(maximum) if maximum is not None else None

    def assert_valid(self, value):
        super().assert_valid(value)
        if not isinstance(value, self.numeric_type):
            raise ValidationError(
                f"Value `{self.name}` must be {self.type}", self.name, value
            )
        if self.minimum is not None and value < self.minimum:
            raise ValidationError(
                f"Value `{self.name}` must be greater than or equal to {self.minimum}",
                self.name,
                value,
            )
        if self.maximum is not None and value > self.maximum:
            raise ValidationError(
                f"Value `{self.name}` must be less than or equal to {self.maximum}",
                self.name,
                value,
            )

    def convert(self, value):
        try:
            return self.numeric_type(value) if value is not None else value
        except (ValueError, TypeError) as err:
            raise ConversionError(
                f"Cannot convert {value} to {self.type} for `{self.name}`",
                self.name,
                value,
            ) from err

    @property
    def description(self):
        """Modify description property for numeric field."""
        if self.minimum is not None and self.maximum is not None:
            extra = f"{self.type} between {self.minimum} and {self.maximum}."
        elif self.minimum is not None:
            extra = f"{self.type} larger than {self.minimum}."
        elif self.maximum is not None:
            extra = f"{self.type} smaller than {self.maximum}."
        else:
            extra = None
        return "\n".join([super().description, extra]) if extra else super().description


class DateTimeField(SimpleField):
    """Validator for datetime fields."""

    def __init__(self, name: str, **params):
        params.setdefault("type", "datetime-local")
        super().__init__(name, **params)

    def assert_valid(self, value):
        super().assert_valid(value)
        if not isinstance(value, datetime) and value is not None:
            raise ValidationError(
                f"Value `{self.name}` must be a datetime", self.name, value
            )

    def convert(self, value):
        if isinstance(value, datetime) or value is None:
            return value
        if isinstance(value, date):
            return datetime.datetime.combine(value, datetime.time())
        try:
            if is_number(value):
                return datetime.fromtimestamp(float(value))
            return datetime.fromisoformat(str(value))
        except (ValueError, TypeError) as err:
            raise ConversionError(
                f"Cannot convert {value} to a datetime for `{self.name}`",
                self.name,
                value,
            ) from err


class DateField(SimpleField):
    """Validator for date fields."""

    def __init__(self, name: str, **params):
        params.setdefault("type", "date")
        super().__init__(name, **params)

    def assert_valid(self, value):
        super().assert_valid(value)
        if value is not None and (
            not isinstance(value, date) or isinstance(value, datetime)
        ):
            raise ValidationError(
                f"Value `{self.name}` must be a date", self.name, value
            )

    def convert(self, value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date) or value is None:
            return value
        try:
            if is_number(value):
                return date.fromtimestamp(float(value))
            return date.fromisoformat(str(value))
        except (ValueError, TypeError) as err:
            raise ConversionError(
                f"Cannot convert {value} to a date for `{self.name}`",
                self.name,
                value,
            ) from err


class TimeField(SimpleField):
    """Validator for time fields."""

    def __init__(self, name: str, **params):
        params.setdefault("type", "time")
        super().__init__(name, **params)

    def assert_valid(self, value):
        super().assert_valid(value)
        if not isinstance(value, time) and value is not None:
            raise ValidationError(
                f"Value `{self.name}` must be a time", self.name, value
            )

    def convert(self, value):
        if isinstance(value, time) or value is None:
            return value
        if isinstance(value, datetime):
            return value.time()
        if isinstance(value, str):
            try:
                return time.fromisoformat(value)
            except (ValueError, TypeError) as err:
                raise ConversionError(
                    f"Cannot convert {value} to a time for `{self.name}`",
                    self.name,
                    value,
                ) from err
        raise ConversionError(
            f"Cannot convert {value} to a time for `{self.name}`", self.name, value
        )


class CompositeField(Field):
    """Class representing a composite field.

    Attributes:
    fields (dict of Field): Collection of subfields. Keys are the (local) names
        of the subfields, values are the subfields themselves.

    Caveats:
    The current implementation of the ManGO metadata specification uses
    indices for both repeatable and non-repeatable composite fields when
    flattening to AVUs. This means that non-repeatable composite fields
    will be unflattened to a list of length 1, with the dict of subfields
    as its only element.

    To resolve this, the CompositeField will convert the list to a dict
    when the repeatable property is False.

    See also: `helpers.unflattened_to_mango_avus`
    """

    def __init__(self, name: str, fields: list = None, **params):
        """Init a composite field.

        Args:
            name (str): Name of the field.
            fields (list, optional): List of subfields.
            params (dict, optional): Additional parameters for the field.
        Raises:
            ValueError: When no subfields are provided.
        """
        params.setdefault("type", "object")
        self.fields = {}
        super().__init__(name, **params)

        if self.type != "object":
            raise ValueError("The type of the field must be 'object'.")
        self.fields = {field.basename: field for field in fields} if fields else {}
        if self.fields is None or len(self.fields) == 0:
            raise ValueError("A composite field must have at least one subfield.")
        # make sure all subfields have correct name prefix
        for subfield in self.fields.values():
            subfield.namespace = self.name

        # override defaults of subfields if default parameter is provided
        if "default" in params:
            self.default = params.get("default", None)

    @property
    def required(self):
        """Override required property of super to get required from subfields"""
        return any(subfield.required for subfield in self.fields.values())

    @required.setter
    def required(self, value):
        """Set required property recursively on all subfields."""
        if self.fields is None or len(self.fields) == 0:
            return
        logger.warning(
            "Setting required to %s for all subfields of %s!", value, self.name
        )
        for subfield in self.fields.values():
            subfield.required = value

    @property
    def required_fields(self):
        """Get the required fields of the composite field."""
        return {
            subfield_basename: subfield.default
            for subfield_basename, subfield in self.fields.items()
            if subfield.required
        }

    @property
    def default(self):
        """Override default property of super to get defaults from subfields"""
        if self.fields is None or len(self.fields) == 0:
            return None
        defaults = {
            subfield_basename: subfield.default
            for subfield_basename, subfield in self.fields.items()
            if subfield.default is not None
        }
        return defaults if len(defaults) > 0 else None

    @default.setter
    def default(self, value):
        """Set defaults of subfields based on dict. Existing defaults are overwritten,
        new defaults are added, but defaults not in the dict are not removed, unless
        explicitly set to None.
        """
        if self.fields is None or len(self.fields) == 0:
            return
        if value is None:
            # remove all defaults
            for subfield in self.fields.values():
                subfield.default = None
        elif isinstance(value, MutableMapping):
            # (re)set defaults for subfields
            for key, val in value.items():
                if key in self.fields:
                    self.fields[key].default = val
                else:
                    raise ValueError(f"Unknown field {key} in `{self.name}`")
        else:
            raise ValueError(f"Default value for `{self.name}` must be a dict")

    @property
    def description(self):
        """Get description property of the field."""
        return "\n".join(
            [
                super().description,
                "\nComposed of the following fields:",
                "\n\n".join(
                    f"\033[4m{subfield.name}\033[0m\n{subfield.description}"
                    for subfield in self.fields.values()
                ),
            ]
        )

    def apply_default(self, value):
        """Apply default recursively to subfields if needed.

        Args:
            value: The value to check.

        Returns:
            Any: The value with the default applied as needed.
        """
        # if there are no subfields set, return the defaults for all subfields
        if self.is_empty(value) and self.default is not None:
            return self.convert(self.default)
        if self.default is not None:
            fields = copy(value) if value is not None else {}
            # apply default to all known subfields set in the current value
            for key, val in fields.items():
                if key in self.fields:
                    fields[key] = self.fields[key].apply_default(val)
            # Set default on all subfields not set in the current value
            for key, val in self.default.items():
                if key not in fields:
                    fields[key] = self.fields[key].convert(val)
            return fields
        return copy(value)

    def assert_valid(self, value):
        super().assert_valid(value)
        if not isinstance(value, MutableMapping):
            raise ValidationError(
                f"Value `{self.name}` must be a dict", self.name, value
            )
        if logger.isEnabledFor(logging.INFO):
            # check for missing non-required fields
            missing_non_required = [
                key
                for key, subfield in self.fields.items()
                if not subfield.required and key not in value.keys()
            ]
            if len(missing_non_required) > 0:
                logger.info(
                    "Missing non-required fields in %s: %s.",
                    self.name,
                    ", ".join(missing_non_required),
                )
        for key, val in value.items():
            if key not in self.fields:
                raise ValidationError(
                    f"Unknown field {key} in `{self.name}`", self.name
                )
            self.fields[key].assert_valid(val)

    def convert(self, value):
        if self.is_empty(value):
            return {}
        if isinstance(value, list) and not self.repeatable:
            # handle ambiguous unflattening of dicts in current ManGO schema specifiation.
            # See above class docstring for more info.
            return self.convert(value[0])
        if not isinstance(value, MutableMapping) and hasattr(value, "to_dict"):
            value = value.to_dict()
        if isinstance(value, MutableMapping):
            if logger.isEnabledFor(logging.INFO):
                # check for unknown fields
                unknown_fields = [key for key in value.keys() if key not in self.fields]
                if len(unknown_fields) > 0:
                    logger.info(
                        "Following fields in %s are undefined and will be ignored: %s.",
                        self.name,
                        ", ".join(unknown_fields),
                    )
            return {
                key: self.fields[key].convert(val)
                for key, val in value.items()
                if key in self.fields  # remove unknown fields
            }
        raise ConversionError(
            (
                f"Can't convert composite field `{self.name}` to dict. "
                "Value must be a dict or an object with a to_dict() method"
            ),
            self.name,
            value,
        )

    @Field.name.setter
    def name(self, value):
        """Update namespace of subfields when name of composite field is updated."""
        Field.name.fset(self, value)
        for subfield in self.fields.values():
            subfield.namespace = value

    @Field.namespace.setter
    def namespace(self, value):
        """Update namespace of subfields when namespace of composite field is updated."""
        Field.namespace.fset(self, value)
        for subfield in self.fields.values():
            subfield.namespace = self.name

    @Field.basename.setter
    def basename(self, value):
        """Update namespace of subfields when basename of composite field is updated."""
        Field.basename.fset(self, value)
        for subfield in self.fields.values():
            subfield.namespace = self.name


class MultipleField(Field):
    """Class representing a multiple-choice field."""

    def __init__(self, name: str, multiple: bool = False, choices=None, **params):
        """Init a multiple-choice field.

        Args:
            name (str): Name of the field.
            multiple (bool, optional): Whether more than one value can be given.
            choices (list, optional): The possible values (alias for `values`).
            params (dict, optional): Additional parameters for the field.

        Raises:
            ValueError: When no values are provided.
        """
        params.setdefault("type", "select")
        super().__init__(name, **params)
        if params.get("values") is not None and choices is None:
            choices = params.get("values")
        elif choices is None:
            raise ValueError(
                f"No 'values' or 'choices' provided for select field {name}."
            )
        if not isinstance(choices, list) or len(choices) == 0:
            raise ValueError(
                f"Invalid 'choices' for select field {name}, must be a non-empty list."
            )
        self.multiple = multiple
        self.choices = [str(v) for v in choices]

    @property
    def default(self):
        """Override default property of super to convert default to list if multiple."""
        if self._default is None:
            return None
        return [self._default] if self.multiple else self._default

    @default.setter  # we need to redefine the setter because we have a custom getter
    def default(self, value):
        """Set default property."""
        self._default = value

    @property
    def description(self):
        """Get description property of the field."""
        return "\n".join(
            [
                super().description,
                f'Choose {"at least" if self.multiple else "only"} one of the following values:',
                "- " + "\n- ".join(self.choices),
            ]
        )

    def assert_valid(self, value):
        super().assert_valid(value)
        if self.is_empty(value):
            return
        if self.multiple and not isinstance(value, list):
            raise ValidationError(
                f"Value `{self.name}` must be a list", self.name, value
            )
        if self.multiple:
            if not all(x in self.choices for x in value):
                raise ValidationError(
                    f"Value `{self.name}` must be a list of values in {self.choices}",
                    self.name,
                    value,
                )
        else:
            if value not in self.choices:
                raise ValidationError(
                    f"Value `{self.name}` must be one of {self.choices}",
                    self.name,
                    value,
                )

    def convert(self, value):
        if isinstance(value, list):  # if we have multiple values
            if not self.multiple:
                raise ValidationError(
                    f"Single value expected for `{self.name}` must be a single value, not a list",
                    self.name,
                    value,
                )
            if len(value) == 0:
                return []
            values = [str(v) for v in value]
            if all(v not in self.choices for v in values):
                if self.required:
                    raise ValidationError(
                        f"No valid values in `{self.name}`. Allowed options are {self.choices}",
                        self.name,
                        value,
                    )
                return []
            return [v for v in values if v in self.choices]
        # if we have only one value
        value = str(value) if value is not None else None
        return value if value in self.choices else None


class RepeatableField(Field):
    """Class decorating a field to make it repeatable."""

    def __init__(self, field: Field, **params):
        """Init a repeatable field.

        Args:
            field (Field): The field to repeat.
            params (dict, optional): Additional parameters for the field.
        """
        self.field = field
        super().__init__(
            field.name,
            type=field.type,
            default=field.default,
            required=field.required,
            repeatable=True,
            **params,
        )

    @property
    def required(self):
        """Override required property of super to get required from wrapped field"""
        return self.field.required

    @required.setter
    def required(self, value):
        """Set required property recursively on wrapped field."""
        if self.field.required != value:
            self.field.required = value

    @property
    def default(self):
        """Override default property of super to get defaults from wrapped field"""
        return self.field.default

    @default.setter
    def default(self, value):
        """Set defaults of wrapped field based on dict. Existing defaults are overwritten,
        new defaults are added, but defaults not in the dict are not removed, unless
        explicitly set to None.
        """
        self.field.default = value

    @property
    def repeatable(self):
        """Override repeatable property of super to get repeatable from wrapped field"""
        return True

    @repeatable.setter
    def repeatable(self, value):
        """Set repeatable property recursively on wrapped field."""
        if not value:
            raise ValueError("Repeatable field must be repeatable")

    @property
    def description(self):
        """Get description property of the wrapped field."""
        return self.field.description

    def assert_valid(self, value):
        super().assert_valid(value)
        if not isinstance(value, list) and value is not None:
            raise ValidationError(
                f"Value `{self.name}` must be a list", self.name, value
            )
        for val in value if value is not None else []:
            self.field.assert_valid(val)

    def convert(self, value):
        if isinstance(value, list):
            return [self.field.convert(val) for val in value]
        return [self.field.convert(value)] if value is not None else None

    @Field.name.setter
    def name(self, value):
        """Update namespace of subfields when name of composite field is updated."""
        Field.name.fset(self, value)
        self.field.name = value

    @Field.namespace.setter
    def namespace(self, value):
        """Update namespace of subfields when namespace of composite field is updated."""
        Field.namespace.fset(self, value)
        self.field.namespace = value

    @Field.basename.setter
    def basename(self, value):
        """Update namespace of subfields when basename of composite field is updated."""
        Field.basename.fset(self, value)
        self.field.basename = value
