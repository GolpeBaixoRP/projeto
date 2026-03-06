import unittest

from config.error_codes import ERROR_TABLE


class ErrorCatalogTests(unittest.TestCase):
    def test_all_codes_start_with_ms_prefix(self):
        for code in ERROR_TABLE.keys():
            self.assertTrue(code.startswith("MS-"), msg=code)

    def test_codes_are_unique_and_match_entry_code(self):
        self.assertEqual(len(ERROR_TABLE), len(set(ERROR_TABLE.keys())))
        for key, spec in ERROR_TABLE.items():
            self.assertEqual(key, spec.code)

    def test_error_spec_has_essential_attributes(self):
        spec = next(iter(ERROR_TABLE.values()))
        for attr in (
            "code",
            "domain",
            "name",
            "severity",
            "recoverable",
            "description",
            "probable_cause",
            "recommended_action",
        ):
            self.assertTrue(hasattr(spec, attr), msg=attr)

    def test_list_fields_are_lists(self):
        for spec in ERROR_TABLE.values():
            self.assertIsInstance(spec.probable_causes_pt, list)
            self.assertIsInstance(spec.recommended_actions_pt, list)


if __name__ == "__main__":
    unittest.main()
