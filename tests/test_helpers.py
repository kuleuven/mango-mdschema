"""Test helper functions"""

import unittest
from irods.meta import iRODSMeta
from mango_mdschema.helpers import (
    flatten,
    flattened_from_mango_avu,
    flattened_to_mango_avu,
    unflatten,
)


class TestFlattening(unittest.TestCase):
    """Test flattening and unflattening of dictionaries."""

    def test_flatten(self):
        """Test flattening of dictionaries."""

        # Test case 1: Empty dictionary
        self.assertEqual(list(flatten({})), [])

        # Test case 2: Nested dictionary
        input_dict = {"a": {"b": {"c": 1, "d": 2}, "e": 3}, "f": 4, "g": None}
        expected_output = [("a.b.c", 1), ("a.b.d", 2), ("a.e", 3), ("f", 4)]
        self.assertEqual(list(flatten(input_dict)), expected_output)

    def test_unflatten(self):
        """Test unflattening of dictionaries."""

        # Test case 1: Empty dictionary
        self.assertEqual(unflatten([]), {})

        # Test case 2: Flattened dictionary
        input_dict = (("a.b.c", 1), ("a.b.d", 2), ("a.e", 3), ("f", 4))
        expected_output = {"a": {"b": {"c": 1, "d": 2}, "e": 3}, "f": 4}
        self.assertEqual(unflatten(input_dict), expected_output)

    def test_reversibility(self):
        """Test that flatten(unflatten(x)) == x for any dictionary x."""

        # Test case 1: Empty dictionary
        self.assertEqual(unflatten(flatten({})), {})

        # Test case 2: Nested dictionary
        input_dict = {"a": {"b": {"c": 1, "d": 2}, "e": 3}, "f": 4}
        self.assertEqual(unflatten(flatten(input_dict)), input_dict)

        # Test case 3: Nested dictionary with simple list
        input_dict = {"a": {"b": {"c": 1, "d": 2}, "e": 3}, "f": 4, "g": [5, 6, 7]}
        self.assertEqual(unflatten(flatten(input_dict)), input_dict)

        # Test case 4: Nested dictionary with list of dictionaries
        input_dict = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3,
                    "f": 4,
                    "g": 5,
                    "h": 6,
                },
                "i": 7,
            },
            "j": [{"k": 8, "l": 9}, {"m": 10, "n": 11}],
            "o": [12, 13, 14, 15],
            "p": [
                {"q": [{"r": 16}, {"s": 17}], "t": 18},
                {"u": [{"v": 19}, {"w": 20}], "x": 21},
            ],
            "y": {"z": [{"aa": 22}, {"ab": 23}], "ac": 24},
            "ad": None,
        }
        output_dict = unflatten(flatten(input_dict))
        self.assertNotIn("ad", output_dict)  # flatten() does not preserve None values
        del input_dict["ad"]
        self.assertEqual(output_dict, input_dict)


class TestAVUFlattening(unittest.TestCase):
    """Test flattening/unflattening to/from AVUs."""

    schema_prefix = "mgs.test"

    def test_flattened_to_mango_avus(self):
        """Test conversion of flattened key/value pairs to AVUs."""

        prefix = self.schema_prefix

        # Test case 1: Empty list
        self.assertEqual(list(map(lambda x: flattened_to_mango_avu(x, prefix), [])), [])

        # Test case 2: List of tuples with simple fields
        input_list = [("a", 1), ("b", 2), ("c", 3), ("d", 4)]
        expected_output = [
            iRODSMeta(f"{prefix}.a", "1", None),
            iRODSMeta(f"{prefix}.b", "2", None),
            iRODSMeta(f"{prefix}.c", "3", None),
            iRODSMeta(f"{prefix}.d", "4", None),
        ]
        self.assertEqual(
            list(map(lambda x: flattened_to_mango_avu(x, prefix), input_list)),
            expected_output,
            msg="Simple fields",
        )

        # Test case 3: List of tuples with nested fields
        input_list = [("a.b.c", 1), ("a.b.d", 2), ("a.e", 3), ("f", 4)]
        expected_output = [
            iRODSMeta(f"{prefix}.a.b.c", "1", "1.1"),
            iRODSMeta(f"{prefix}.a.b.d", "2", "1.1"),
            iRODSMeta(f"{prefix}.a.e", "3", "1"),
            iRODSMeta(f"{prefix}.f", "4", None),
        ]
        self.assertEqual(
            list(map(lambda x: flattened_to_mango_avu(x, prefix), input_list)),
            expected_output,
            msg="Nested fields",
        )

        # Test case 4: List of tuples with nested fields and list indices
        input_list = [
            ("a[0].b.c", 1),
            ("a[1].b.c", 2),
            ("e.f[0]", 3),
            ("e.f[1]", 4),
            ("g.h[0].i", 5),
            ("g.h[1].j", 6),
        ]
        expected_output = [
            iRODSMeta(f"{prefix}.a.b.c", "1", "1.1"),
            iRODSMeta(f"{prefix}.a.b.c", "2", "2.1"),
            iRODSMeta(f"{prefix}.e.f", "3", "1"),
            iRODSMeta(f"{prefix}.e.f", "4", "1"),
            iRODSMeta(f"{prefix}.g.h.i", "5", "1.1"),
            iRODSMeta(f"{prefix}.g.h.j", "6", "1.2"),
        ]
        self.assertEqual(
            list(map(lambda x: flattened_to_mango_avu(x, prefix), input_list)),
            expected_output,
            msg="Nested fields and list indices",
        )

    def test_dict_to_mango_avus(self):
        """Test conversion of nested dictionaries to AVUs."""

        prefix = self.schema_prefix

        input_dict = {
            "a": 1,
            "b": {
                "c": 2,
                "d": {
                    "e": 3,
                    "f": 4,
                },
                "i": 7,
            },
            "j": [{"k": 8, "l": 9}, {"m": 10, "n": 11}],
            "o": [12, 13],
            "p": [
                {"q": [{"r": 14}, {"r": 15}], "s": 16},
                {"t": [{"u": 17}, {"u": 18}], "v": 19},
            ],
            "w": {"x": [{"y": 20}, {"y": 21}], "z": 22},
        }
        expected_output = [
            iRODSMeta(f"{prefix}.a", "1", None),
            iRODSMeta(f"{prefix}.b.c", "2", "1"),
            iRODSMeta(f"{prefix}.b.d.e", "3", "1.1"),
            iRODSMeta(f"{prefix}.b.d.f", "4", "1.1"),
            iRODSMeta(f"{prefix}.b.i", "7", "1"),
            iRODSMeta(f"{prefix}.j.k", "8", "1"),
            iRODSMeta(f"{prefix}.j.l", "9", "1"),
            iRODSMeta(f"{prefix}.j.m", "10", "2"),
            iRODSMeta(f"{prefix}.j.n", "11", "2"),
            iRODSMeta(f"{prefix}.o", "12", None),
            iRODSMeta(f"{prefix}.o", "13", None),
            iRODSMeta(f"{prefix}.p.q.r", "14", "1.1"),
            iRODSMeta(f"{prefix}.p.q.r", "15", "1.2"),
            iRODSMeta(f"{prefix}.p.s", "16", "1"),
            iRODSMeta(f"{prefix}.p.t.u", "17", "2.1"),
            iRODSMeta(f"{prefix}.p.t.u", "18", "2.2"),
            iRODSMeta(f"{prefix}.p.v", "19", "2"),
            iRODSMeta(f"{prefix}.w.x.y", "20", "1.1"),
            iRODSMeta(f"{prefix}.w.x.y", "21", "1.2"),
            iRODSMeta(f"{prefix}.w.z", "22", "1"),
        ]
        self.assertEqual(
            list(map(lambda x: flattened_to_mango_avu(x, prefix), flatten(input_dict))),
            expected_output,
        )

    def test_reversibility(self):
        """Test conversion of nested dictionaries to AVUs and back.

        Caveat:
        The current implementation of the ManGO metadata specification uses
        indices for both repeatable and non-repeatable composite fields. This means
        that the indices of non-repeatable composite fields are always 1. Because of
        this, the conversion of nested dictionaries to AVUs is not reversible for
        non-repeatable composite fields. For example, the following input dictionary:
        {
            "a": 1,
            "b": {"c": 2, "d": {"e": 3, "f": 4}, "i": 7},
        }

        is converted to the following list of AVUs:

        [
            iRODSMeta("mgs.test.a", 1, None),
            iRODSMeta("mgs.test.b.c", 2, "1"),
            iRODSMeta("mgs.test.b.d.e", 3, "1.1"),
            iRODSMeta("mgs.test.b.d.f", 4, "1.1"),
            iRODSMeta("mgs.test.b.i", 7, "1"),
        ]

        When this list of AVUs is converted back to a nested dictionary, the
        non-repeatable composite fields are converted to repeatable composite fields
        with indices 1. This means that the following dictionary is returned instead:

        {
            "a": 1,
            "b": [{"c": 2, "d": [{"e": 3, "f": 4}], "i": 7}],
        }

        This is not the same as the original input dictionary, but when the
        the unflattened dictionary is flattened again, this will result in same
        list of AVUs though.

        To handle this ambiguity, the `CompositeField` class will convert the
        list of dictionaries back to a single dictionary with the first element
        of the list when the CompositeField is not repeatable.
        """

        prefix = self.schema_prefix

        input_dict = {
            "a": "1",
            "b": {"c": "2", "d": {"e": "3", "f": "4", "g": "5", "h": "6"}, "i": "7"},
            "j": [{"k": "8", "l": "9"}, {"m": "10", "n": "11"}],
            "o": ["12", "13"],
            "p": [
                {"q": [{"r": "14"}, {"r": "15"}], "s": "16"},
                {"t": [{"u": "17"}, {"u": "18"}], "v": "19"},
            ],
            "w": {"x": [{"y": "20"}, {"y": "21"}], "z": "22"},
        }

        # The following function will convert non-repeatable composite fields to
        # repeatable composite fields with one element, so that the conversion to AVUs
        # can be reversed. See the caveat above for more information.
        def handle_non_repeatable_composite_fields(d):
            if not isinstance(d, dict):
                return d
            for key, value in d.items():
                if isinstance(value, dict):
                    # convert non-repeatable composite fields to repeatable composite fields
                    d[key] = [handle_non_repeatable_composite_fields(value)]
                elif isinstance(value, list):
                    d[key] = [
                        handle_non_repeatable_composite_fields(item) for item in value
                    ]
            return d

        expected_dict = handle_non_repeatable_composite_fields(input_dict)

        avus = list(
            map(lambda x: flattened_to_mango_avu(x, prefix), flatten(input_dict))
        )
        self.assertEqual(
            unflatten(list(map(lambda x: flattened_from_mango_avu(x, prefix), avus))),
            expected_dict,
        )


if __name__ == "__main__":
    unittest.main()
