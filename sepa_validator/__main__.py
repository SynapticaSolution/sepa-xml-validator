"""CLI entry point: python -m sepa_validator <file.xml>"""

import json
import sys
from pathlib import Path

from . import __version__
from .validator import validate_sepa_file


def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(f"SEPA XML Validator v{__version__}")
        print("Usage: python -m sepa_validator <file.xml> [options]")
        print()
        print("Options:")
        print("  --format json    Output as JSON")
        print("  --strict         Warn on missing optional fields")
        print("  --help           Show this help")
        sys.exit(0)

    json_output = "--format" in args and "json" in args
    strict = "--strict" in args

    files = [a for a in args if not a.startswith("-") and a != "json"]

    if not files:
        print("Error: no files specified", file=sys.stderr)
        sys.exit(1)

    # Expand directories
    xml_files = []
    for f in files:
        p = Path(f)
        if p.is_dir():
            xml_files.extend(p.glob("*.xml"))
        elif p.exists():
            xml_files.append(p)
        else:
            print(f"Warning: {f} not found", file=sys.stderr)

    all_valid = True
    results = []

    for xml_file in xml_files:
        result = validate_sepa_file(str(xml_file), strict=strict)

        if json_output:
            results.append(result.to_dict())
        else:
            print(f"\nSEPA XML Validator v{__version__}")
            print(f"File: {xml_file}")
            print(f"Type: {result.message_type} ({result.message_type_description})")
            print()
            print(f"Transactions: {result.transaction_count}")
            print(f"Control Sum: {result.control_sum:,.2f} EUR")
            if result.debtor_name:
                print(f"Debtor: {result.debtor_name} ({result.debtor_iban})")
            print()
            print("Validation Results:")

            if not result.errors and not result.warnings:
                print("  [PASS] All checks passed")
            for err in result.errors:
                print(f"  [FAIL] {err.message}")
            for warn in result.warnings:
                print(f"  [WARN] {warn.message}")

            print()
            status = "VALID" if result.is_valid else "INVALID"
            extras = []
            if result.errors:
                extras.append(f"{len(result.errors)} error(s)")
            if result.warnings:
                extras.append(f"{len(result.warnings)} warning(s)")
            extra_str = f" ({', '.join(extras)})" if extras else ""
            print(f"Result: {status}{extra_str}")

        if not result.is_valid:
            all_valid = False

    if json_output:
        print(json.dumps(results, indent=2, ensure_ascii=False))

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
