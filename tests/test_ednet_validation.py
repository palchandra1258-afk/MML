from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from mcp_ri.ednet_validation import (  # noqa: E402
    derive_correctness,
    inspect_archives,
    is_missing,
    learner_id_from_member,
    parse_timestamp,
    validate_schema,
)
from acquire_ednet import _test_zip  # noqa: E402


class EdNetValidationTests(unittest.TestCase):
    def make_archives(self, base: Path) -> tuple[Path, Path]:
        kt1 = base / "kt1.zip"
        content = base / "content.zip"
        with zipfile.ZipFile(kt1, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "KT1/u123.csv",
                "timestamp,solving_id,question_id,user_answer,elapsed_time\n"
                "1000,1,q1,a,500\n"
                "2000,1,q2,c,\n"
                "1500,2,q1,a,700\n"
                "1500,2,q1,a,700\n",
            )
            archive.writestr(
                "KT1/u456.csv",
                "timestamp,solving_id,question_id,user_answer,elapsed_time\n"
                "3000,1,q3,b,400\n",
            )
        with zipfile.ZipFile(content, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(
                "questions.csv",
                "question_id,bundle_id,explanation_id,correct_answer,part,tags,deployed_at\n"
                "q1,b1,e1,a,1,10;11,900\n"
                "q2,b1,e1,d,1,,900\n",
            )
        return kt1, content

    def test_file_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            kt1, _ = self.make_archives(Path(tmp))
            self.assertIsNone(_test_zip(kt1))
            stored = Path(tmp) / "stored.zip"
            with zipfile.ZipFile(stored, "w", compression=zipfile.ZIP_STORED) as archive:
                archive.writestr("payload.csv", "hello world")
            damaged = bytearray(stored.read_bytes())
            payload_offset = damaged.index(b"hello world")
            damaged[payload_offset] ^= 0x01
            corrupt_member = Path(tmp) / "corrupt_member.zip"
            corrupt_member.write_bytes(damaged)
            self.assertEqual(_test_zip(corrupt_member), "payload.csv")
            corrupt = Path(tmp) / "corrupt.zip"
            corrupt.write_bytes(b"not a zip")
            self.assertFalse(zipfile.is_zipfile(corrupt))

    def test_schema_validation(self):
        expected = {"timestamp", "solving_id", "question_id", "user_answer", "elapsed_time"}
        self.assertEqual(validate_schema(expected), [])
        self.assertEqual(validate_schema(expected - {"timestamp"}), ["timestamp"])

    def test_timestamp_parsing(self):
        self.assertEqual(parse_timestamp("1700000000000"), 1700000000000)
        self.assertIsNone(parse_timestamp(""))
        self.assertIsNone(parse_timestamp("not-a-time"))
        self.assertIsNone(parse_timestamp("0"))

    def test_learner_identification(self):
        self.assertEqual(learner_id_from_member("KT1/u12345.csv"), "u12345")
        self.assertEqual(learner_id_from_member("KT1/12345.csv"), "12345")
        self.assertIsNone(learner_id_from_member("README.md"))
        self.assertIsNone(learner_id_from_member("nested/user.csv"))

    def test_question_and_answer_key_mapping(self):
        self.assertIs(True, derive_correctness("a", "A"))
        self.assertIs(False, derive_correctness("b", "a"))
        self.assertIsNone(derive_correctness("", "a"))
        self.assertIsNone(derive_correctness("x", "a"))

    def test_missing_values_and_sentinels(self):
        self.assertTrue(is_missing(""))
        self.assertTrue(is_missing("  "))
        self.assertFalse(is_missing("-1"))
        self.assertFalse(is_missing("0"))

    def test_duplicate_mapping_and_chronological_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            kt1, content = self.make_archives(Path(tmp))
            report = inspect_archives(kt1, content)
            self.assertEqual(report["learner_files"], 2)
            self.assertEqual(report["interaction_rows"], 5)
            self.assertEqual(report["duplicate_records"], 1)
            self.assertEqual(report["non_monotonic_timestamp_transitions"], 1)
            self.assertEqual(report["duplicate_timestamp_transitions"], 1)
            self.assertEqual(report["invalid_timestamps"], 0)
            self.assertEqual(report["unmatched_question_rows"], 1)
            self.assertEqual(report["answer_key_available_rows"], 4)
            self.assertEqual(report["correctness_derivable_rows"], 4)
            self.assertEqual(report["skill_tag_available_rows"], 3)
            self.assertEqual(report["missing_values_by_column"]["elapsed_time"], 1)
            self.assertTrue(report["prediction_task_supported"])


if __name__ == "__main__":
    unittest.main()
