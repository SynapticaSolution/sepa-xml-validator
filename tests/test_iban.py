"""Tests for IBAN validation."""

import unittest

from sepa_validator.iban import validate_iban, format_iban


class TestIbanValidation(unittest.TestCase):
    """Test IBAN validation against known valid/invalid IBANs."""

    def test_valid_german_iban(self):
        valid, err = validate_iban("DE89370400440532013000")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_valid_uk_iban(self):
        valid, err = validate_iban("GB29NWBK60161331926819")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_valid_french_iban(self):
        valid, err = validate_iban("FR7630006000011234567890189")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_valid_italian_iban(self):
        valid, err = validate_iban("IT68D0300203280000400162854")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_valid_spanish_iban(self):
        valid, err = validate_iban("ES9121000418450200051332")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_valid_iban_with_spaces(self):
        valid, err = validate_iban("DE89 3704 0044 0532 0130 00")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_valid_iban_lowercase(self):
        valid, err = validate_iban("de89370400440532013000")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_invalid_check_digits(self):
        valid, err = validate_iban("IT00X0542811101000000123456")
        self.assertFalse(valid)
        self.assertIn("check digits", err.lower())

    def test_unknown_country(self):
        valid, err = validate_iban("XX89370400440532013000")
        self.assertFalse(valid)
        self.assertIn("Unknown country", err)

    def test_wrong_length(self):
        valid, err = validate_iban("DE8937040044053201300")  # 21 chars, should be 22
        self.assertFalse(valid)
        self.assertIn("Invalid length", err)

    def test_empty_iban(self):
        valid, err = validate_iban("")
        self.assertFalse(valid)

    def test_too_short(self):
        valid, err = validate_iban("DE89")
        self.assertFalse(valid)

    def test_special_characters(self):
        valid, err = validate_iban("DE89-3704-0044-0532-0130-00")
        self.assertTrue(valid)  # dashes are stripped

    def test_format_iban(self):
        result = format_iban("DE89370400440532013000")
        self.assertEqual(result, "DE89 3704 0044 0532 0130 00")


class TestIbanCountries(unittest.TestCase):
    """Test IBAN validation for various European countries."""

    VALID_IBANS = {
        "AT": "AT611904300234573201",
        "BE": "BE68539007547034",
        "CH": "CH9300762011623852957",
        "NL": "NL91ABNA0417164300",
        "PT": "PT50000201231234567890154",
        "SE": "SE4550000000058398257466",
        "NO": "NO9386011117947",
        "DK": "DK5000400440116243",
        "FI": "FI2112345600000785",
        "PL": "PL61109010140000071219812874",
    }

    def test_all_valid_ibans(self):
        for country, iban in self.VALID_IBANS.items():
            with self.subTest(country=country):
                valid, err = validate_iban(iban)
                self.assertTrue(valid, f"{country} IBAN failed: {err}")


if __name__ == "__main__":
    unittest.main()
