# SEPA XML Validator

> Validate SEPA XML payment files against ISO 20022 standard before uploading to your bank.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)

## What It Does

Validates SEPA XML files (credit transfers and direct debits) before you upload them to your bank's portal. Catches errors that would cause rejection:

- **IBAN format validation** (length, country code, check digits)
- **BIC/SWIFT validation**
- **XML structure** against ISO 20022 message types
- **Amount consistency** (sum of individual transactions vs control sum)
- **Duplicate detection** (same IBAN + amount + date)
- **Required fields check** (debtor, creditor, payment info)

## Supported Message Types

| Message | Type | Description |
|---------|------|-------------|
| `pain.001.001.03` | Credit Transfer | SEPA bonifici (SCT) |
| `pain.001.001.09` | Credit Transfer | SEPA bonifici v9 |
| `pain.008.001.02` | Direct Debit | SEPA addebiti diretti (SDD) |
| `pain.008.001.08` | Direct Debit | SEPA addebiti diretti v8 |

## Quick Start

```bash
# Install
pip install sepa-xml-validator

# Or use directly
git clone https://github.com/SynapticaSolution/sepa-xml-validator.git
cd sepa-xml-validator
```

### Command Line

```bash
# Validate a single file
python -m sepa_validator payments.xml

# Validate all XML files in a directory
python -m sepa_validator ./xml-files/

# JSON output (for automation)
python -m sepa_validator payments.xml --format json

# Strict mode (warns on optional missing fields too)
python -m sepa_validator payments.xml --strict
```

### Python API

```python
from sepa_validator import validate_sepa_file, validate_iban

# Validate a SEPA XML file
result = validate_sepa_file("payments.xml")

if result.is_valid:
    print(f"Valid {result.message_type} with {result.transaction_count} transactions")
    print(f"Total amount: {result.control_sum} EUR")
else:
    for error in result.errors:
        print(f"ERROR: {error.message} (line {error.line})")
    for warning in result.warnings:
        print(f"WARNING: {warning.message}")

# Validate a single IBAN
is_valid, error = validate_iban("IT60X0542811101000000123456")
```

### Output Example

```
$ python -m sepa_validator bonifici-marzo.xml

SEPA XML Validator v1.0.0
File: bonifici-marzo.xml
Type: pain.001.001.03 (Credit Transfer)

Transactions: 47
Control Sum: 125,430.50 EUR
Debtor: Acme SRL (IT60X0542811101000000123456)

Validation Results:
  [PASS] XML structure valid
  [PASS] Message type: pain.001.001.03
  [PASS] All 47 IBANs valid
  [PASS] BIC codes valid
  [PASS] Control sum matches (125,430.50 EUR)
  [PASS] No duplicate transactions
  [WARN] 3 transactions without remittance info

Result: VALID (1 warning)
```

## IBAN Validation

The validator checks IBANs against the official SWIFT registry:

- Country code (2 letters)
- Check digits (mod 97 algorithm, ISO 7064)
- BBAN length per country (Italy: 23 chars)
- Character set validation

```python
from sepa_validator import validate_iban

validate_iban("IT60X0542811101000000123456")  # (True, None)
validate_iban("IT00X0542811101000000123456")  # (False, "Invalid check digits")
validate_iban("XX60X0542811101000000123456")  # (False, "Unknown country code")
```

## Integration

### With SEPA Manager

This validator is used internally by [SEPA Manager](https://synaptica-solution.com/sepa-manager/), a payment automation tool that generates SEPA XML files from invoicing software (Fatture in Cloud, etc.). SEPA Manager validates every file before generation, which is why it achieves 0% IBAN errors.

### With CI/CD

```yaml
# GitHub Actions
- name: Validate SEPA files
  run: |
    pip install sepa-xml-validator
    python -m sepa_validator ./output/*.xml --format json > validation.json
```

### With Shell Scripts

```bash
# Validate before uploading to bank
python -m sepa_validator payment.xml && upload_to_bank payment.xml
```

## Common Errors Caught

| Error | Description | Impact |
|-------|-------------|--------|
| Invalid IBAN | Wrong check digits or format | Bank rejects entire file |
| Control sum mismatch | Sum of amounts != declared total | Bank rejects entire file |
| Missing BIC | Required for cross-border payments | Transaction rejected |
| Duplicate payment | Same beneficiary + amount + date | Double payment risk |
| Invalid characters | Special chars in beneficiary name | Bank rejects transaction |
| Future execution date | Date > 30 days in future | Bank may reject |

## Why Validate Before Upload?

Banks reject entire SEPA XML files if even one transaction has an error. A single invalid IBAN means all 50 payments fail. Validating locally first saves time and prevents failed batches.

**Without validation**: upload → rejection → fix → re-upload → re-authorize (30+ minutes)
**With validation**: validate → fix → upload → authorize (5 minutes)

## Related Resources

Maintained by **[Synaptica Solution](https://synaptica-solution.com)**, Italian software studio for SME automation.

| If you need… | See… |
|---|---|
| Automated SEPA file generation from invoices | [SEPA Manager](https://synaptica-solution.com/sepa-manager/) |
| SEPA XML pain.001 guide (Italian banks) | [Come generare XML SEPA CBI](https://synaptica-solution.com/knowledge/come-generare-xml-sepa-cbi/) |
| Upload SEPA file to Italian home banking | [Come importare distinta bonifico](https://synaptica-solution.com/knowledge/come-importare-distinta-bonifico-in-banca/) |
| All open source tools | [Open Source Hub](https://synaptica-solution.com/open-source/) |

## License

MIT - See [LICENSE](LICENSE)

---

Made by [Synaptica Solution](https://synaptica-solution.com) - AI Governance & Process Automation for Italian SMEs
