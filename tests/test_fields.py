import unittest
from datetime import datetime, date, time
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
        field = TextField("text_field")
        self.assertEqual(field.type, "text")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)

    def test_email_field(self):
        field = EmailField("email_field")
        self.assertEqual(field.type, "email")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)

    def test_url_field(self):
        field = UrlField("url_field")
        self.assertEqual(field.type, "url")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)

    def test_boolean_field(self):
        field = BooleanField("boolean_field")
        self.assertEqual(field.type, "checkbox")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)

    def test_integer_field(self):
        field = NumericField("integer_field", minimum=0, maximum=10, type="integer")
        self.assertEqual(field.type, "integer")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)
        self.assertEqual(field.minimum, 0)
        self.assertEqual(field.maximum, 10)

    def test_float_field(self):
        field = NumericField("integer_field", minimum=0, maximum=10, type="float")
        self.assertEqual(field.type, "float")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)
        self.assertEqual(field.minimum, 0)
        self.assertEqual(field.maximum, 10)

    def test_datetime_field(self):
        field = DateTimeField("datetime_field")
        self.assertEqual(field.type, "datetime-local")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)

    def test_date_field(self):
        field = DateField("date_field")
        self.assertEqual(field.type, "date")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)

    def test_time_field(self):
        field = TimeField("time_field")
        self.assertEqual(field.type, "time")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)

    def test_composite_field(self):
        subfield1 = TextField("subfield1")
        subfield2 = NumericField("subfield2", type="integer")
        fields = [subfield1, subfield2]
        field = CompositeField("composite", fields=fields)
        self.assertEqual(field.type, "object")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)
        self.assertEqual(list(field.fields.keys()), ["subfield1", "subfield2"])
        self.assertEqual(field.fields["subfield1"].basename, "subfield1")
        self.assertEqual(field.fields["subfield1"], subfield1)
        self.assertEqual(field.fields["subfield2"], subfield2)

    def test_multiple_field(self):
        field = MultipleField(
            "multiple_field", multiple=True, values=["option1", "option2", "option3"]
        )
        self.assertEqual(field.type, "select")
        self.assertFalse(field.required)
        self.assertIsNone(field.default)
        self.assertFalse(field.repeatable)
        self.assertTrue(field.multiple)
        self.assertEqual(field.choices, ["option1", "option2", "option3"])

    def test_repeatable_field(self):
        subfield = TextField("subfield")
        field = RepeatableField(subfield)
        self.assertEqual(field.type, subfield.type)
        self.assertEqual(field.required, subfield.required)
        self.assertEqual(field.default, subfield.default)
        self.assertTrue(field.repeatable)
        self.assertEqual(field.field, subfield)


if __name__ == "__main__":
    unittest.main()
