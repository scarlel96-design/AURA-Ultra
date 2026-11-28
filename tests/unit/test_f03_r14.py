"""Verify fail-closed signature classification."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_signature_review as audit

SIGNER = "A" * 40
PRIMARY = "B" * 40
KEY = SIGNER[-16:]
GOOD = "[GNUPG:] GOODSIG " + KEY + " test\n"
VALID = "[GNUPG:] VALIDSIG " + SIGNER + " 2026-01-01 1767225600 0 4 0 1 8 00 " + PRIMARY + "\n"


class SignatureTests(unittest.TestCase):
    def test_valid_is_cryptographic_only(self):
        self.assertEqual(audit.verdict(0, GOOD + VALID, KEY, SIGNER),
                         {"crypto": "VALID", "signerFingerprint": SIGNER,
                          "primaryFingerprint": PRIMARY, "statusTags": ["GOODSIG", "VALIDSIG"]})

    def test_adverse_and_missing_status(self):
        for tag in audit.BAD:
            with self.subTest(tag=tag):
                self.assertEqual(audit.verdict(0, GOOD + VALID + "[GNUPG:] " + tag + "\n", KEY, SIGNER)["crypto"], "NOT_VALIDATED")
        for ret, text in ((1, GOOD + VALID), (0, GOOD), (0, VALID), (0, GOOD + VALID + VALID)):
            self.assertEqual(audit.verdict(ret, text, KEY, SIGNER)["crypto"], "NOT_VALIDATED")

    def test_weak_hash(self):
        self.assertEqual(audit.verdict(0, GOOD + VALID.replace(" 1 8 00 ", " 1 2 00 "), KEY, SIGNER)["crypto"], "WEAK_OR_UNKNOWN_HASH")

    def test_wrong_fingerprint(self):
        with self.assertRaises(ValueError):
            audit.verdict(0, GOOD + VALID, KEY, PRIMARY)

    def test_packet_issuer(self):
        packet = ":signature packet: algo 1, keyid " + KEY + "\n hashed subpkt 33 (issuer fpr v4 " + SIGNER + ")\n"
        self.assertEqual(audit.issuer(packet), (KEY, SIGNER))
        for text in ("", packet + packet, packet.replace(SIGNER, PRIMARY)):
            with self.assertRaises(ValueError):
                audit.issuer(text)

    def test_discovery_not_official(self):
        self.assertTrue(all(kind == "DISCOVERY_ONLY" for kind, _ in audit.key_sources("io.netty", KEY, SIGNER)))
        self.assertEqual(next(audit.key_sources("org.bouncycastle", KEY, SIGNER))[0], "OFFICIAL_KEY_FILE")


if __name__ == "__main__":
    unittest.main()
