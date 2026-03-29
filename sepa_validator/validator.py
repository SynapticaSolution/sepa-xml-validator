"""SEPA XML file validator for ISO 20022 payment messages."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from .iban import validate_iban

# ISO 20022 namespace
NS = {"iso": "urn:iso:std:iso:20022:tech:xsd:"}

# Supported message types
SUPPORTED_TYPES = {
    "pain.001.001.03": "Credit Transfer (SCT)",
    "pain.001.001.09": "Credit Transfer (SCT) v9",
    "pain.008.001.02": "Direct Debit (SDD)",
    "pain.008.001.08": "Direct Debit (SDD) v8",
}


@dataclass
class ValidationError:
    """A single validation error."""

    message: str
    line: int | None = None
    field: str | None = None
    severity: str = "error"  # 'error' or 'warning'


@dataclass
class SepaValidationResult:
    """Result of validating a SEPA XML file."""

    is_valid: bool = True
    message_type: str = ""
    message_type_description: str = ""
    transaction_count: int = 0
    control_sum: float = 0.0
    debtor_name: str = ""
    debtor_iban: str = ""
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    file_path: str = ""

    def to_dict(self) -> dict:
        """Convert result to dictionary (for JSON output)."""
        return {
            "is_valid": self.is_valid,
            "file": self.file_path,
            "message_type": self.message_type,
            "message_type_description": self.message_type_description,
            "transaction_count": self.transaction_count,
            "control_sum": self.control_sum,
            "debtor": {
                "name": self.debtor_name,
                "iban": self.debtor_iban,
            },
            "errors": [{"message": e.message, "field": e.field} for e in self.errors],
            "warnings": [
                {"message": w.message, "field": w.field} for w in self.warnings
            ],
        }


def _detect_message_type(root: ET.Element) -> str | None:
    """Detect the ISO 20022 message type from the root element."""
    tag = root.tag
    # Extract namespace
    if "}" in tag:
        ns = tag.split("}")[0].replace("{", "")
        for msg_type in SUPPORTED_TYPES:
            if msg_type.replace(".", "") in ns.replace(".", ""):
                return msg_type
    # Check child elements
    for child in root:
        child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if child_tag == "CstmrCdtTrfInitn":
            return "pain.001.001.03"
        if child_tag == "CstmrDrctDbtInitn":
            return "pain.008.001.02"
    return None


def _find_with_ns(element: ET.Element, path: str) -> ET.Element | None:
    """Find element ignoring namespace."""
    parts = path.split("/")
    current = element
    for part in parts:
        found = None
        for child in current:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == part:
                found = child
                break
        if found is None:
            return None
        current = found
    return current


def _findall_with_ns(element: ET.Element, tag_name: str) -> list:
    """Find all elements with a given tag name, ignoring namespace."""
    results = []
    for child in element:
        child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if child_tag == tag_name:
            results.append(child)
    return results


def validate_sepa_file(file_path: str, strict: bool = False) -> SepaValidationResult:
    """
    Validate a SEPA XML file against ISO 20022 standard.

    Args:
        file_path: Path to the XML file.
        strict: If True, missing optional fields generate warnings.

    Returns:
        SepaValidationResult with validation details.
    """
    result = SepaValidationResult(file_path=str(file_path))
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        result.is_valid = False
        result.errors.append(ValidationError("File not found", field="file"))
        return result

    if not path.suffix.lower() == ".xml":
        result.warnings.append(
            ValidationError(
                "File does not have .xml extension",
                field="file",
                severity="warning",
            )
        )

    # Parse XML
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        result.is_valid = False
        result.errors.append(ValidationError(f"XML parse error: {e}", field="xml"))
        return result

    # Detect message type
    msg_type = _detect_message_type(root)
    if msg_type is None:
        result.is_valid = False
        result.errors.append(
            ValidationError(
                "Unknown or unsupported SEPA message type",
                field="message_type",
            )
        )
        return result

    result.message_type = msg_type
    result.message_type_description = SUPPORTED_TYPES.get(msg_type, "Unknown")

    # Find main element
    is_credit = msg_type.startswith("pain.001")
    main_tag = "CstmrCdtTrfInitn" if is_credit else "CstmrDrctDbtInitn"
    main_elem = _find_with_ns(root, main_tag)
    if main_elem is None:
        result.is_valid = False
        result.errors.append(
            ValidationError(f"Missing {main_tag} element", field="structure")
        )
        return result

    # Group header
    grp_hdr = _find_with_ns(main_elem, "GrpHdr")
    if grp_hdr is None:
        result.is_valid = False
        result.errors.append(
            ValidationError("Missing GrpHdr element", field="structure")
        )
        return result

    # Number of transactions
    nb_of_txs = _find_with_ns(grp_hdr, "NbOfTxs")
    if nb_of_txs is not None and nb_of_txs.text:
        try:
            result.transaction_count = int(nb_of_txs.text)
        except ValueError:
            result.errors.append(
                ValidationError(f"Invalid NbOfTxs: {nb_of_txs.text}", field="NbOfTxs")
            )
            result.is_valid = False

    # Control sum
    ctrl_sum = _find_with_ns(grp_hdr, "CtrlSum")
    if ctrl_sum is not None and ctrl_sum.text:
        try:
            result.control_sum = float(ctrl_sum.text)
        except ValueError:
            result.errors.append(
                ValidationError(f"Invalid CtrlSum: {ctrl_sum.text}", field="CtrlSum")
            )
            result.is_valid = False

    # Payment info blocks
    pmt_inf_tag = "PmtInf"
    pmt_inf_blocks = _findall_with_ns(main_elem, pmt_inf_tag)

    if not pmt_inf_blocks:
        result.is_valid = False
        result.errors.append(ValidationError("No PmtInf blocks found", field="PmtInf"))
        return result

    # Validate transactions
    actual_tx_count = 0
    actual_sum = 0.0
    seen_transactions = set()

    for pmt_inf in pmt_inf_blocks:
        # Debtor info (credit transfer) or Creditor info (direct debit)
        if is_credit:
            dbtr = _find_with_ns(pmt_inf, "Dbtr")
            dbtr_acct = _find_with_ns(pmt_inf, "DbtrAcct")
            if dbtr is not None:
                nm = _find_with_ns(dbtr, "Nm")
                if nm is not None and nm.text:
                    result.debtor_name = nm.text
            if dbtr_acct is not None:
                iban_elem = _find_with_ns(dbtr_acct, "Id/IBAN")
                if iban_elem is None:
                    id_elem = _find_with_ns(dbtr_acct, "Id")
                    if id_elem is not None:
                        iban_elem = _find_with_ns(id_elem, "IBAN")
                if iban_elem is not None and iban_elem.text:
                    result.debtor_iban = iban_elem.text
                    valid, err = validate_iban(iban_elem.text)
                    if not valid:
                        result.is_valid = False
                        result.errors.append(
                            ValidationError(
                                f"Invalid debtor IBAN: {err}",
                                field="DbtrAcct",
                            )
                        )

        # Individual transactions
        tx_tag = "CdtTrfTxInf" if is_credit else "DrctDbtTxInf"
        transactions = _findall_with_ns(pmt_inf, tx_tag)

        for tx in transactions:
            actual_tx_count += 1

            # Amount
            amt_elem = _find_with_ns(tx, "Amt")
            if amt_elem is not None:
                instd = _find_with_ns(amt_elem, "InstdAmt")
                if instd is not None and instd.text:
                    try:
                        amount = float(instd.text)
                        actual_sum += amount
                    except ValueError:
                        result.is_valid = False
                        result.errors.append(
                            ValidationError(
                                f"Invalid amount: {instd.text}",
                                field="InstdAmt",
                            )
                        )

            # Creditor IBAN (credit transfer)
            if is_credit:
                cdtr_acct = _find_with_ns(tx, "CdtrAcct")
                if cdtr_acct is not None:
                    id_elem = _find_with_ns(cdtr_acct, "Id")
                    if id_elem is not None:
                        iban_elem = _find_with_ns(id_elem, "IBAN")
                        if iban_elem is not None and iban_elem.text:
                            valid, err = validate_iban(iban_elem.text)
                            if not valid:
                                result.is_valid = False
                                result.errors.append(
                                    ValidationError(
                                        f"Invalid creditor IBAN ({iban_elem.text}): {err}",
                                        field="CdtrAcct",
                                    )
                                )

                            # Duplicate check
                            tx_key = (
                                iban_elem.text,
                                instd.text if instd is not None else "",
                            )
                            if tx_key in seen_transactions:
                                result.warnings.append(
                                    ValidationError(
                                        f"Possible duplicate: {iban_elem.text}",
                                        field="duplicate",
                                        severity="warning",
                                    )
                                )
                            seen_transactions.add(tx_key)

            # Remittance info (optional but recommended)
            if strict:
                rmt_inf = _find_with_ns(tx, "RmtInf")
                if rmt_inf is None:
                    result.warnings.append(
                        ValidationError(
                            f"Transaction {actual_tx_count}: no remittance info",
                            field="RmtInf",
                            severity="warning",
                        )
                    )

    # Verify transaction count
    if result.transaction_count > 0 and actual_tx_count != result.transaction_count:
        result.is_valid = False
        result.errors.append(
            ValidationError(
                f"Transaction count mismatch: declared {result.transaction_count}, found {actual_tx_count}",
                field="NbOfTxs",
            )
        )

    # Verify control sum
    if result.control_sum > 0:
        if abs(actual_sum - result.control_sum) > 0.01:
            result.is_valid = False
            result.errors.append(
                ValidationError(
                    f"Control sum mismatch: declared {result.control_sum:.2f}, calculated {actual_sum:.2f}",
                    field="CtrlSum",
                )
            )

    return result
