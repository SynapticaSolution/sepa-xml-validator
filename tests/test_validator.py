"""Tests for SEPA XML file validator."""

import os
import tempfile
import unittest

from sepa_validator.validator import validate_sepa_file

VALID_PAIN001 = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>MSG001</MsgId>
      <CreDtTm>2026-03-29T10:00:00</CreDtTm>
      <NbOfTxs>2</NbOfTxs>
      <CtrlSum>1500.00</CtrlSum>
      <InitgPty><Nm>Acme SRL</Nm></InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>PMT001</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <ReqdExctnDt>2026-03-30</ReqdExctnDt>
      <Dbtr><Nm>Acme SRL</Nm></Dbtr>
      <DbtrAcct><Id><IBAN>IT68D0300203280000400162854</IBAN></Id></DbtrAcct>
      <DbtrAgt><FinInstnId><BIC>BPPIITRRXXX</BIC></FinInstnId></DbtrAgt>
      <CdtTrfTxInf>
        <PmtId><EndToEndId>E2E001</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="EUR">1000.00</InstdAmt></Amt>
        <Cdtr><Nm>Fornitore Alpha</Nm></Cdtr>
        <CdtrAcct><Id><IBAN>DE89370400440532013000</IBAN></Id></CdtrAcct>
      </CdtTrfTxInf>
      <CdtTrfTxInf>
        <PmtId><EndToEndId>E2E002</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="EUR">500.00</InstdAmt></Amt>
        <Cdtr><Nm>Fornitore Beta</Nm></Cdtr>
        <CdtrAcct><Id><IBAN>FR7630006000011234567890189</IBAN></Id></CdtrAcct>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>"""


class TestSepaValidator(unittest.TestCase):
    """Test SEPA XML file validation."""

    def _write_temp(self, content):
        f = tempfile.NamedTemporaryFile(suffix=".xml", delete=False, mode="w")
        f.write(content)
        f.close()
        return f.name

    def test_valid_pain001(self):
        path = self._write_temp(VALID_PAIN001)
        r = validate_sepa_file(path)
        os.unlink(path)
        self.assertTrue(r.is_valid)
        self.assertEqual(r.message_type, "pain.001.001.03")
        self.assertEqual(r.transaction_count, 2)
        self.assertEqual(r.control_sum, 1500.00)
        self.assertEqual(r.debtor_name, "Acme SRL")

    def test_file_not_found(self):
        r = validate_sepa_file("/nonexistent/file.xml")
        self.assertFalse(r.is_valid)
        self.assertTrue(any("not found" in e.message.lower() for e in r.errors))

    def test_broken_xml(self):
        path = self._write_temp("<root><unclosed>")
        r = validate_sepa_file(path)
        os.unlink(path)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("parse error" in e.message.lower() for e in r.errors))

    def test_non_sepa_xml(self):
        path = self._write_temp("<root><child>text</child></root>")
        r = validate_sepa_file(path)
        os.unlink(path)
        self.assertFalse(r.is_valid)

    def test_control_sum_mismatch(self):
        bad = VALID_PAIN001.replace(
            "<CtrlSum>1500.00</CtrlSum>", "<CtrlSum>9999.99</CtrlSum>"
        )
        path = self._write_temp(bad)
        r = validate_sepa_file(path)
        os.unlink(path)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("mismatch" in e.message.lower() for e in r.errors))

    def test_invalid_creditor_iban(self):
        bad = VALID_PAIN001.replace("DE89370400440532013000", "DE00000000000000000000")
        path = self._write_temp(bad)
        r = validate_sepa_file(path)
        os.unlink(path)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("iban" in e.message.lower() for e in r.errors))

    def test_strict_mode_warnings(self):
        path = self._write_temp(VALID_PAIN001)
        r = validate_sepa_file(path, strict=True)
        os.unlink(path)
        self.assertTrue(r.is_valid)  # warnings don't invalidate
        self.assertGreater(len(r.warnings), 0)

    def test_to_dict(self):
        path = self._write_temp(VALID_PAIN001)
        r = validate_sepa_file(path)
        os.unlink(path)
        d = r.to_dict()
        self.assertTrue(d["is_valid"])
        self.assertEqual(d["transaction_count"], 2)
        self.assertEqual(d["debtor"]["name"], "Acme SRL")


if __name__ == "__main__":
    unittest.main()
