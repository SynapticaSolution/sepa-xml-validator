"""
SEPA XML Validator - Validate SEPA payment files against ISO 20022 standard.

Supports pain.001 (Credit Transfer) and pain.008 (Direct Debit) message types.

Usage:
    from sepa_validator import validate_sepa_file, validate_iban

    result = validate_sepa_file("payments.xml")
    is_valid, error = validate_iban("IT60X0542811101000000123456")

Made by Synaptica Solution - https://synaptica-solution.com
"""

__version__ = "1.0.0"
__author__ = "Synaptica Solution"
__url__ = "https://github.com/SynapticaSolution/sepa-xml-validator"

from .validator import validate_sepa_file, SepaValidationResult
from .iban import validate_iban

__all__ = ["validate_sepa_file", "validate_iban", "SepaValidationResult"]
