"""Add at least four meaningful engine regression tests for the README contract."""
import unittest
from locale_key_audit.engine import analyze

class AuditTest(unittest.TestCase):
    def test_readme_example(self):
        p = {"reference": {"nav": {"home": "Home", "help": "Help"}}, "locales": {"pt-BR": {"nav": {"home": "X"}}}}
        r = analyze(p)
        self.assertEqual(r, {"valid": False, "reference_keys": 2, "locales": [{"locale": "pt-BR", "missing": ["/nav/help"], "extra": [], "matched": 1}]})

    def test_equal_valid_values_ignored(self):
        p = {"reference": {"a": "x"}, "locales": {"en": {"a": "y"}}}
        r = analyze(p)
        self.assertTrue(r["valid"])
        self.assertEqual(r["reference_keys"], 1)
        self.assertEqual(r["locales"][0]["matched"], 1)
        self.assertEqual(p["reference"], {"a": "x"})

    def test_escape_dot_conflict(self):
        p = {"reference": {"a.b": "x", "a": {"b": "y"}, "q/r": "z", "m~n": "w"}, "locales": {"en": {"a.b": "1", "a": {"b": "2"}, "q/r": "3", "m~n": "4"}}}
        r = analyze(p)
        self.assertTrue(r["valid"])
        self.assertEqual(r["reference_keys"], 4)
        q = {"reference": {"a": {"b": "x"}}, "locales": {"en": {"a": "y"}}}
        r2 = analyze(q)
        self.assertFalse(r2["valid"])
        self.assertEqual(r2["locales"][0]["missing"], ["/a/b"])
        self.assertEqual(r2["locales"][0]["extra"], ["/a"])

    def test_sorted_empty(self):
        p = {"reference": {}, "locales": {"b": {}, "a": {"z": "v"}}}
        r = analyze(p)
        self.assertFalse(r["valid"])
        self.assertEqual([e["locale"] for e in r["locales"]], ["a", "b"])
        self.assertEqual(r["locales"][1]["missing"], [])
        self.assertEqual(analyze({"reference": {}, "locales": {}})["valid"], True)

    def test_invalid_types(self):
        bads = [{"reference": {"a": ["x"]}, "locales": {}}, {"reference": {"a": 1}, "locales": {}}, {"reference": {"a": True}, "locales": {}}, {"reference": {"a": None}, "locales": {}}, {"reference": {}, "locales": {"-bad": {}}}, {"reference": {"a\x01": "x"}, "locales": {}}, {"reference": {"a": "x\x00"}, "locales": {}}, {"reference": {"a": "\ud800"}, "locales": {}}, {"reference": {}, "locales": {}, "extra": 1}, {"reference": {}, "locales": []}]
        for p in bads:
            with self.assertRaises(ValueError) as cm:
                analyze(p)
            self.assertEqual(str(cm.exception), "INPUT_INVALID")

    def test_depth_and_key_limits(self):
        deep = "v"
        for _ in range(13):
            deep = {"k": deep}
        with self.assertRaises(ValueError) as cm:
            analyze({"reference": deep, "locales": {}})
        self.assertEqual(str(cm.exception), "INPUT_INVALID")
        cyc = {}
        cyc["self"] = cyc
        with self.assertRaises(ValueError):
            analyze({"reference": cyc, "locales": {}})
        with self.assertRaises(ValueError):
            analyze({"reference": {"": "x"}, "locales": {}})

if __name__ == "__main__":
    unittest.main()
