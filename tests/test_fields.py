"""Tests for the fields module."""

# pylint: disable=missing-docstring,too-many-public-methods

import unittest
from datetime import datetime, date, time
from mango_mdschema.exceptions import ConversionError, ValidationError
from mango_mdschema.fields import (
    TextField,
    EmailField,
    UrlField,
    BooleanField,
    NumericField,
    DateTimeField,
    DateField,
    TimeField,
    CompositeField,
    MultipleField,
    RepeatableField,
)


class TestFields(unittest.TestCase):
    def test_text_field(self):
        field = TextField("text_field", max_length=15, pattern="^[a-z]+$")
        self.assertEqual(field.type, "text")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertEqual(field.max_length, 15)
        self.assertEqual(field.pattern, "^[a-z]+$")
        self.assertEqual(field.validate("abc"), "abc")
        with self.assertRaises(ValidationError):
            field.validate("123")
        with self.assertRaises(ValidationError):
            field.validate("abcdefghijklmnopqrstuvwxyz")
        with self.assertRaises(ValidationError):
            field.validate({"a": 1, "b": 2}, convert=False)

    def test_email_field(self):
        field = EmailField("email_field")
        self.assertEqual(field.type, "email")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertEqual(field.validate("me@example.org"), "me@example.org")
        with self.assertRaises(ValidationError):
            field.validate("no-valid-email")

    def test_url_field(self):
        field = UrlField("url_field")
        self.assertEqual(field.type, "url")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertEqual(field.validate("https://kuleuven.be"), "https://kuleuven.be")
        with self.assertRaises(ValidationError):
            field.validate("no-valid-url")

    def test_boolean_field(self):
        field = BooleanField("boolean_field")
        self.assertEqual(field.type, "checkbox")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertEqual(field.validate(True), True)
        self.assertEqual(field.validate(False), False)
        self.assertEqual(field.validate("yes"), True)
        self.assertEqual(field.validate("no"), False)
        self.assertEqual(field.validate("false"), False)
        with self.assertRaises(ConversionError):
            field.validate("no-valid-boolean")

    def test_integer_field(self):
        field = NumericField("integer_field", minimum=0, maximum=10, type="integer")
        self.assertEqual(field.type, "integer")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertEqual(field.minimum, 0)
        self.assertEqual(field.maximum, 10)
        self.assertEqual(field.validate(5), 5)
        self.assertEqual(field.validate("5"), 5)
        with self.assertRaises(ValidationError):
            field.validate(11)

    def test_float_field(self):
        field = NumericField(
            "float_field",
            minimum=1.5,
            maximum=10.5,
            type="float",
            default=5.5,
            required=True,
        )
        self.assertEqual(field.type, "float")
        self.assertTrue(field.required)
        self.assertEqual(field.default, 5.5)
        self.assertEqual(field.minimum, 1.5)
        self.assertEqual(field.maximum, 10.5)
        self.assertEqual(field.validate(4.5), 4.5)
        self.assertEqual(field.validate("6.7"), 6.7)
        self.assertEqual(field.validate(None), field.default)
        with self.assertRaises(ValidationError):
            field.validate(11.5)

    def test_datetime_field(self):
        now = datetime.now()
        field = DateTimeField("datetime_field", default=now, required=True)
        self.assertEqual(field.type, "datetime-local")
        self.assertTrue(field.required)
        self.assertEqual(field.default, now)
        self.assertEqual(field.validate(now), now)
        self.assertEqual(field.validate(now.isoformat()), now)
        self.assertEqual(field.validate(None), now)
        self.assertEqual(field.validate(now.timestamp()), now)
        self.assertEqual(field.validate(str(now.timestamp())), now)
        with self.assertRaises(ConversionError):
            field.validate("no-valid-datetime")

    def test_date_field(self):
        field = DateField("date_field")
        self.assertEqual(field.type, "date")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertEqual(field.validate(date.today()), date.today())
        self.assertEqual(field.validate(date.today().isoformat()), date.today())
        self.assertEqual(field.validate(datetime.now()), date.today())
        self.assertEqual(
            field.validate(datetime.now().strftime("%Y-%m-%d")), date.today()
        )
        self.assertEqual(field.validate(datetime.now().timestamp()), date.today())
        self.assertEqual(field.validate(str(datetime.now().timestamp())), date.today())
        self.assertEqual(field.validate(None), None)
        with self.assertRaises(ConversionError):
            field.validate("no-valid-date")

    def test_time_field(self):
        now = datetime.now()
        field = TimeField("time_field", default=time(12, 30))
        self.assertEqual(field.type, "time")
        self.assertFalse(field.required)
        self.assertEqual(field.default, time(12, 30))
        self.assertEqual(field.validate(time(12, 30)), time(12, 30))
        self.assertEqual(field.validate(time(12, 30).isoformat()), time(12, 30))
        self.assertEqual(field.validate(now), now.time())
        self.assertEqual(field.validate("12:30"), time(12, 30))

    def test_composite_field(self):
        subfield1 = TextField("subfield1")
        subfield2 = NumericField("subfield2", type="integer")
        fields = [subfield1, subfield2]
        field = CompositeField("composite1", fields=fields)
        self.assertEqual(field.type, "object")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertEqual(list(field.fields.keys()), ["subfield1", "subfield2"])
        self.assertEqual(field.fields["subfield1"].basename, "subfield1")
        self.assertEqual(field.fields["subfield1"], subfield1)
        self.assertEqual(field.fields["subfield2"], subfield2)
        self.assertEqual(subfield1.namespace, "composite1")
        self.assertEqual(subfield1.name, "composite1.subfield1")
        self.assertEqual(
            field.validate({"subfield1": "abc", "subfield2": 123}),
            {"subfield1": "abc", "subfield2": 123},
        )
        field.namespace = "parent"
        self.assertEqual(field.namespace, "parent")
        self.assertEqual(subfield1.namespace, "parent.composite1")
        self.assertEqual(subfield1.basename, "subfield1")
        self.assertEqual(subfield1.name, "parent.composite1.subfield1")
        self.assertEqual(
            field.validate({"subfield1": "abc", "subfield2": 123}),
            {"subfield1": "abc", "subfield2": 123},
        )

        now = datetime.now()
        subfield3 = TextField("subfield3", default="xyz")
        subfield4 = DateTimeField("subfield4", required=True)
        fields = [subfield3, subfield4]
        field = CompositeField("composite2", fields=fields, default={"subfield4": now})
        self.assertTrue(field.required)
        self.assertEqual(field.default, {"subfield3": "xyz", "subfield4": now})
        self.assertEqual(subfield4.default, now)
        field.default = None
        self.assertIsNone(field.default)
        self.assertIsNone(subfield4.default)
        field.default = {"subfield3": "abc", "subfield4": None}
        self.assertEqual(field.default, {"subfield3": "abc"})
        self.assertEqual(subfield3.default, "abc")

    def test_multiple_field(self):
        field = MultipleField(
            "multiple_field", multiple=True, values=["option1", "option2", "option3"]
        )
        self.assertEqual(field.type, "select")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertTrue(field.multiple)
        self.assertEqual(field.choices, ["option1", "option2", "option3"])
        self.assertEqual(field.validate(["option1", "option2"]), ["option1", "option2"])
        self.assertEqual(field.validate(["option3"]), ["option3"])
        self.assertEqual(field.validate([]), [])
        self.assertEqual(field.validate(None), None)
        self.assertEqual(field.validate(["option3", "option4"]), ["option3"])
        self.assertEqual(field.validate(["option5"]), [])
        field.required = True
        self.assertEqual(field.validate(["option3", "option4"]), ["option3"])
        with self.assertRaises(ValidationError):
            field.validate(["option5"])
        field.multiple = False
        field.required = False
        self.assertEqual(field.validate("option3"), "option3")
        self.assertEqual(field.validate("option5"), None)
        self.assertEqual(field.validate(None), None)
        with self.assertRaises(ValidationError):
            field.validate(["option1", "option4"])
        with self.assertRaises(ValidationError):
            field.validate(["option2"])

    def test_repeatable_field(self):
        subfield = TextField("subfield")
        field = RepeatableField(subfield)
        self.assertEqual(field.type, subfield.type)
        self.assertEqual(field.required, subfield.required)
        self.assertEqual(field.default, subfield.default)
        self.assertTrue(field.repeatable)
        self.assertEqual(field.field, subfield)
        self.assertEqual(field.validate(["abc", "def"]), ["abc", "def"])
        self.assertEqual(field.validate(["abc", "def", "ghi"]), ["abc", "def", "ghi"])
        self.assertEqual(field.validate(["abc"]), ["abc"])
        self.assertEqual(field.validate([]), [])
        self.assertEqual(field.validate(None), None)


if __name__ == "__main__":
    unittest.main()
