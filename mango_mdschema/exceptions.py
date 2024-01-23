"""Exceptions for the mango_mdschema package."""

from copy import deepcopy as copy


class FieldError(Exception):
    """Base exception for field errors.

    Attributes:
        message: The error message.
        key: The flattened key of the value.
    """

    def __init__(self, message, field=None, value=None):
        super().__init__(message)
        self.field = field
        self.value = copy(value)


class ValidationError(FieldError):
    """Exception raised when a value fails validation.

    Attributes:
        message: The error message.
        key: The flattened key of the value.
        value: The value that failed validation.
    """


class ConversionError(FieldError):
    """Exception raised when a value cannot be converted to the expected type.

    Attributes:
        message: The error message.
        key: The flattened key of the value.
        value: The value that failed conversion.
    """
