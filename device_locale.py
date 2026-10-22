"""Resolve the UI locale for BTP helper applications."""

import os
import shelve


SHELF_PATH = "/data/userdata/updater.shelve"

LANGUAGE_LOCALES = {
    "nl": "nl_NL.utf8",
    "es": "es_ES.utf8",
    "en": "en_AU.utf8",
    "au": "en_AU.utf8",
    "nz": "en_NZ.utf8",
}


def normalize_locale(value):
    """Return a gettext-compatible locale, or ``None`` for an empty value."""
    if not value:
        return None
    value = str(value).split(":", 1)[0].split("@", 1)[0].strip()
    if not value:
        return None
    language = value.split(".", 1)[0].replace("-", "_")
    mapped = LANGUAGE_LOCALES.get(language.lower())
    if mapped:
        return mapped
    if "_" not in language:
        return f"{language.lower()}_{language.upper()}.utf8"
    language_code, country_code = language.split("_", 1)
    return f"{language_code.lower()}_{country_code.upper()}.utf8"


def read_device_locale(shelf_path=SHELF_PATH):
    """Read the provisioned language without failing helper startup."""
    try:
        with shelve.open(shelf_path, flag="r", protocol=2) as database:
            return normalize_locale(database.get("nodeinfo", {}).get("language"))
    except Exception:
        return None


def resolve_device_locale(explicit=None, shelf_path=SHELF_PATH, environ=None):
    """Resolve explicit, provisioned, then process locale in priority order."""
    if explicit and explicit != "system":
        return normalize_locale(explicit)
    device_locale = read_device_locale(shelf_path)
    if device_locale:
        return device_locale
    environment = os.environ if environ is None else environ
    return (normalize_locale(environment.get("LANGUAGE"))
            or normalize_locale(environment.get("LANG"))
            or "en_US.utf8")
