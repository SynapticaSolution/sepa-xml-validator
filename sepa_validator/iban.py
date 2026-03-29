"""IBAN validation module following ISO 13616 and SWIFT registry."""

# IBAN lengths per country (SWIFT registry)
IBAN_LENGTHS = {
    "AL": 28,
    "AD": 24,
    "AT": 20,
    "AZ": 28,
    "BH": 22,
    "BY": 28,
    "BE": 16,
    "BA": 20,
    "BR": 29,
    "BG": 22,
    "CR": 22,
    "HR": 21,
    "CY": 28,
    "CZ": 24,
    "DK": 18,
    "DO": 28,
    "TL": 23,
    "EE": 20,
    "FO": 18,
    "FI": 18,
    "FR": 27,
    "GE": 22,
    "DE": 22,
    "GI": 23,
    "GR": 27,
    "GL": 18,
    "GT": 28,
    "HU": 28,
    "IS": 26,
    "IQ": 23,
    "IE": 22,
    "IL": 23,
    "IT": 27,
    "JO": 30,
    "KZ": 20,
    "XK": 20,
    "KW": 30,
    "LV": 21,
    "LB": 28,
    "LI": 21,
    "LT": 20,
    "LU": 20,
    "MK": 19,
    "MT": 31,
    "MR": 27,
    "MU": 30,
    "MC": 27,
    "MD": 24,
    "ME": 22,
    "NL": 18,
    "NO": 15,
    "PK": 24,
    "PS": 29,
    "PL": 28,
    "PT": 25,
    "QA": 29,
    "RO": 24,
    "LC": 32,
    "SM": 27,
    "ST": 25,
    "SA": 24,
    "RS": 22,
    "SC": 31,
    "SK": 24,
    "SI": 19,
    "ES": 24,
    "SE": 24,
    "CH": 21,
    "TN": 24,
    "TR": 26,
    "UA": 29,
    "AE": 23,
    "GB": 22,
    "VA": 22,
    "VG": 24,
}


def validate_iban(iban: str) -> tuple:
    """
    Validate an IBAN string.

    Args:
        iban: The IBAN string to validate (spaces are stripped automatically).

    Returns:
        Tuple of (is_valid: bool, error_message: str | None).
        If valid, returns (True, None).
        If invalid, returns (False, "reason").
    """
    # Clean input
    iban = iban.replace(" ", "").replace("-", "").upper().strip()

    if not iban:
        return False, "IBAN is empty"

    if len(iban) < 5:
        return False, "IBAN too short"

    # Check country code
    country = iban[:2]
    if not country.isalpha():
        return False, f"Invalid country code: {country}"

    if country not in IBAN_LENGTHS:
        return False, f"Unknown country code: {country}"

    # Check length
    expected_length = IBAN_LENGTHS[country]
    if len(iban) != expected_length:
        return (
            False,
            f"Invalid length for {country}: expected {expected_length}, got {len(iban)}",
        )

    # Check characters (alphanumeric only)
    if not iban.isalnum():
        return False, "IBAN contains invalid characters"

    # Check digits (positions 3-4 must be numeric)
    if not iban[2:4].isdigit():
        return False, "Check digits must be numeric"

    # MOD 97 validation (ISO 7064)
    rearranged = iban[4:] + iban[:4]
    numeric = ""
    for char in rearranged:
        if char.isdigit():
            numeric += char
        else:
            numeric += str(ord(char) - ord("A") + 10)

    if int(numeric) % 97 != 1:
        return False, "Invalid check digits (MOD 97 failed)"

    return True, None


def format_iban(iban: str) -> str:
    """Format an IBAN with spaces every 4 characters."""
    iban = iban.replace(" ", "").replace("-", "").upper().strip()
    return " ".join(iban[i : i + 4] for i in range(0, len(iban), 4))
