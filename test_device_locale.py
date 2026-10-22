import os
import shelve
import tempfile
import unittest

from device_locale import normalize_locale, resolve_device_locale


class DeviceLocaleTests(unittest.TestCase):
    def test_normalizes_provisioner_language_codes(self):
        self.assertEqual(normalize_locale("es"), "es_ES.utf8")
        self.assertEqual(normalize_locale("nl"), "nl_NL.utf8")
        self.assertEqual(normalize_locale("en-AU.UTF-8"), "en_AU.utf8")

    def test_explicit_locale_wins(self):
        self.assertEqual(
            resolve_device_locale("es", shelf_path="/missing", environ={"LANG": "nl_NL.UTF-8"}),
            "es_ES.utf8",
        )

    def test_provisioned_language_wins_over_process_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            shelf_path = os.path.join(directory, "updater.shelve")
            with shelve.open(shelf_path, protocol=2) as database:
                database["nodeinfo"] = {"language": "es"}
            self.assertEqual(
                resolve_device_locale(shelf_path=shelf_path, environ={"LANG": "nl_NL.UTF-8"}),
                "es_ES.utf8",
            )

    def test_environment_is_used_when_device_data_is_unavailable(self):
        self.assertEqual(
            resolve_device_locale(shelf_path="/missing", environ={"LANGUAGE": "nl"}),
            "nl_NL.utf8",
        )

    def test_locale_category_overrides_are_honored(self):
        self.assertEqual(
            resolve_device_locale(
                shelf_path="/missing",
                environ={"LC_ALL": "es_ES.UTF-8", "LANG": "nl_NL.UTF-8"},
            ),
            "es_ES.utf8",
        )
        self.assertEqual(
            resolve_device_locale(shelf_path="/missing", environ={"LC_MESSAGES": "nl"}),
            "nl_NL.utf8",
        )


if __name__ == "__main__":
    unittest.main()
